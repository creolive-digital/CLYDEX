import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from clydex_engine import VoiceEngine, local_command


class VoiceRoutingTests(unittest.TestCase):
    def test_complete_window_command(self):
        self.assertEqual(local_command('CLYDEX, could you please minimise the Character Map window?'),
                         ('manage_window', 'Character Map', 'minimize'))
        self.assertEqual(local_command('Switch to window 2.'), ('manage_window', 'window 2', 'focus'))

    def test_only_direct_commands_skip_the_planner(self):
        for text in ("Don't open Notepad.", 'How do I open Chrome?', 'Open Chrome and read Outlook.',
                     'Close Notepad.', 'Click Send.', 'Open it.', 'Open Notepad if Excel is closed.'):
            with self.subTest(text=text):
                self.assertIsNone(local_command(text))

    def test_unclear_audio_cannot_be_dispatched_as_a_command(self):
        model = Mock()
        segment = SimpleNamespace(text='Open Notepad', avg_logprob=-1.2, no_speech_prob=0.8)
        model.transcribe.return_value = ([segment], None)
        with self.assertRaisesRegex(RuntimeError, 'confidently'):
            VoiceEngine.transcribe_audio(model, [0] * 16000, 'en')
        self.assertEqual(model.transcribe.call_count, 2)

    def test_confident_english_needs_one_decode(self):
        model = Mock()
        segment = SimpleNamespace(text='Restore Calculator.', avg_logprob=-0.3, no_speech_prob=0.01)
        model.transcribe.return_value = ([segment], None)
        self.assertEqual(VoiceEngine.transcribe_audio(model, [0] * 16000, 'en'), segment.text)
        self.assertEqual(model.transcribe.call_count, 1)
        self.assertEqual(model.transcribe.call_args.kwargs['language'], 'en')


if __name__ == '__main__':
    unittest.main()
