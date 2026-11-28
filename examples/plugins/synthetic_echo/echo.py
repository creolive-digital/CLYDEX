"""Original CLYDEX SDK example; synthetic input only."""
import json
import sys


def main():
    packet = json.loads(sys.stdin.buffer.read(16385))
    if packet.get('sdk_version') != 1 or packet.get('operation') != 'tool' or packet.get('tool') != 'echo.text':
        raise ValueError('Unsupported SDK request.')
    arguments = packet['arguments']
    if set(arguments) != {'text'} or type(arguments['text']) is not str or len(arguments['text']) > 1000:
        raise ValueError('Invalid synthetic text.')
    print(json.dumps({'sdk_version': 1, 'result': {'text': arguments['text']}, 'logs': ['complete']}, ensure_ascii=True))


if __name__ == '__main__':
    main()
