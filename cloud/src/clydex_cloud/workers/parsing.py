"""Fixed parser child, bounded JSON pipe, timeout and Linux resource limits."""
import json
import logging
import multiprocessing
import os
import time

from clydex_cloud.core.errors import CloudError


def _child(name, content, pipe):
    logging.disable(logging.CRITICAL)
    try:
        if os.name != 'nt':
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
            resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
            resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        from clydex.knowledge.ingestion import extract, ExtractionError
        try:
            response = {'ok': True, 'data': extract(name, content).public()}
        except ExtractionError as exc:
            response = {'ok': False, 'error': exc.code}
        except Exception:
            response = {'ok': False, 'error': 'parser_rejected'}
        encoded = json.dumps(response, ensure_ascii=False, allow_nan=False).encode()
        if len(encoded) > 4 * 1024**2:
            encoded = b'{"ok":false,"error":"extracted_content_limit"}'
        pipe.send_bytes(encoded)
    finally:
        pipe.close()


def parse_owned(name: str, content: bytes, stopped, timeout=20) -> dict:
    context = multiprocessing.get_context('spawn')
    receive, send = context.Pipe(duplex=False)
    process = context.Process(target=_child, args=(name, content, send), daemon=False)
    process.start()
    send.close()
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline and not stopped.is_set():
            if receive.poll(.05):
                result = json.loads(receive.recv_bytes(4 * 1024**2))
                if not result.get('ok'):
                    raise CloudError('document_' + result.get('error', 'parser_rejected'), 422)
                return result['data']
            if not process.is_alive():
                raise CloudError('parser_resource_or_process_failure', 422)
        raise CloudError('processing_interrupted' if stopped.is_set() else 'parser_timeout', 422)
    except (EOFError, OSError, ValueError):
        raise CloudError('parser_protocol_failure', 422) from None
    finally:
        receive.close()
        if process.is_alive():
            process.terminate()
        process.join(3)
        if process.is_alive():
            process.kill()
            process.join()
