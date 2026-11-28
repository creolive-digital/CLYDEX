"""Fixed native helper inventory. No arbitrary module/script dispatch.

Started only by the owned process runner, never a public listener. The fixed
private launcher mode also supports a windowed frozen executable without
starting another Core, queue or microphone. Optional native libraries stay gated.
"""
import base64
import io
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys


def _odbc(value):
    return '{' + str(value).replace('}', '}}') + '}'


def sql(data):
    import pyodbc
    p = data['profile']
    connection = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=' + _odbc(p['server']) +
        ';DATABASE=' + _odbc(p['database']) + ';UID=' + _odbc(p['user']) + ';PWD=' + _odbc(data['secret']) +
        ';Encrypt=yes;TrustServerCertificate=no;Application Name=CLYDEX;', timeout=8, autocommit=False)
    try:
        connection.timeout = 20
        cursor = connection.cursor()
        cursor.execute('SET LOCK_TIMEOUT 5000; SET TEXTSIZE 65536')
        cursor.execute(data['query'])
        rows, columns = [], []
        if cursor.description:
            columns = [c[0] for c in cursor.description][:64]
            for row in cursor.fetchmany(101):
                rows.append([str(v)[:512] if v is not None else None for v in row[:64]])
        affected = cursor.rowcount
        if data['mode'] == 'read':
            connection.rollback()
        else:
            connection.commit()
        return dict(columns=columns, rows=rows[:100], truncated=len(rows) > 100, affected=affected)
    finally:
        connection.close()


def capture(data):
    from PIL import Image, ImageGrab
    if data['kind'] == 'screen':
        if data['device'] != 0:
            raise ValueError('Only the explicitly selected primary screen is supported.')
        picture = ImageGrab.grab(all_screens=False)
    else:
        import cv2
        camera = cv2.VideoCapture(data['device'], cv2.CAP_DSHOW)
        try:
            ready, frame = camera.read()
            if not ready:
                raise ValueError('Camera frame unavailable.')
            picture = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        finally:
            camera.release()
    picture.thumbnail((960, 540))
    output = io.BytesIO()
    picture.save(output, format='JPEG', quality=65)
    if len(output.getvalue()) > 160000:
        raise ValueError('Capture exceeds bound.')
    return dict(image='data:image/jpeg;base64,' + base64.b64encode(output.getvalue()).decode('ascii'),
                width=picture.width, height=picture.height, synchronization='No OCR or external transfer performed')


def main():
    restore_standard_streams()
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        raw = sys.stdin.buffer.read(262145)
        if len(raw) > 262144:
            raise ValueError('Helper input too large.')
        packet = json.loads(raw)
        if set(packet) != {'kind', 'data'} or packet['kind'] not in ('sql', 'capture', 'plugin', 'python_script'):
            raise ValueError('Invalid native helper operation.')
        if packet['kind'] == 'plugin':
            data = packet['data']
            path = verified_source(data)
            sys.stdin = io.TextIOWrapper(io.BytesIO(json.dumps(data['request']).encode('utf-8')), encoding='utf-8')
            sys.argv = [str(path)]
            os.chdir(path.parent)
            runpy.run_path(str(path), run_name='__main__')
            return 0
        if packet['kind'] == 'python_script':
            from contextlib import redirect_stdout, redirect_stderr
            path = verified_source(packet['data'])
            output, errors = BoundedText(), BoundedText()
            sys.argv = [str(path)]
            sys.stdin = io.TextIOWrapper(io.BytesIO(b''), encoding='utf-8')
            os.chdir(path.parent)
            with redirect_stdout(output), redirect_stderr(errors):
                runpy.run_path(str(path), run_name='__main__')
            print(json.dumps({'ok': True, 'result': dict(exit_code=0, output=output.getvalue(), errors=errors.getvalue())}))
            return 0
        result = sql(packet['data']) if packet['kind'] == 'sql' else capture(packet['data'])
        print(json.dumps({'ok': True, 'result': result}, ensure_ascii=True, allow_nan=False))
    except Exception:
        # Never emit driver exception strings, connection strings, or private text.
        print('{"ok":false,"error":"Native helper failed or dependency unavailable"}')
        return 1
    return 0


class BoundedText(io.StringIO):
    def write(self, text):
        if self.tell() + len(text) > 32000:
            raise ValueError('Reviewed script output exceeds bound; effects may have completed.')
        return super().write(text)


def verified_source(data):
    path = Path(data['entry'])
    if not path.is_absolute() or path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
        raise ValueError('Invalid reviewed helper source.')
    content = path.read_bytes()
    if len(content) > 2097152 or hashlib.sha256(content).hexdigest() != data['sha256']:
        raise ValueError('Reviewed executable source changed.')
    return path


def restore_standard_streams():
    """Windowed PyInstaller has None streams; only the private helper restores pipes."""
    if os.name == 'nt' and (sys.stdin is None or sys.stdout is None or sys.stderr is None):
        import ctypes
        from ctypes import wintypes
        import msvcrt
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetStdHandle.argtypes = (wintypes.DWORD,)
        kernel.GetStdHandle.restype = wintypes.HANDLE
        for name, number, flags, mode in (('stdin', -10, os.O_RDONLY, 'r'), ('stdout', -11, os.O_WRONLY, 'w'),
                                          ('stderr', -12, os.O_WRONLY, 'w')):
            if getattr(sys, name) is None:
                handle = kernel.GetStdHandle(number & 0xffffffff)
                if not handle or handle == ctypes.c_void_p(-1).value:
                    raise ValueError('Owned helper pipe missing.')
                descriptor = msvcrt.open_osfhandle(handle, flags | os.O_BINARY)
                setattr(sys, name, open(descriptor, mode, encoding='utf-8', closefd=True))


if __name__ == '__main__':
    raise SystemExit(main())
