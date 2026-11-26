import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from clydex.automation.tasks import CancellationToken
from clydex.core.contracts import ProviderRequest
from clydex.core.errors import ProviderError
from clydex.providers.codex import CodexProvider, validate_response


SCHEMA = {'type': 'object', 'properties': {'message': {'type': 'string'}},
          'required': ['message'], 'additionalProperties': False}


class ProviderTests(unittest.TestCase):
    def test_response_schema_is_enforced_locally(self):
        for value in ({}, {'message': 2}, {'message': 'ok', 'tool': 'run'}, []):
            with self.subTest(value=value), self.assertRaises(ProviderError):
                validate_response(value, SCHEMA)
        validate_response({'message': 'ok'}, SCHEMA)

    def test_boolean_not_accepted_as_integer(self):
        with self.assertRaises(ProviderError):
            validate_response(True, {'type': 'integer'})

    def test_unconfigured_provider_fails_without_fallback(self):
        with patch('clydex.providers.codex.shutil.which', return_value=None):
            with self.assertRaises(ProviderError):
                CodexProvider().respond(ProviderRequest('answer', '{}', json.dumps(SCHEMA)), CancellationToken())

    def test_codex_flags_stdin_schema_and_temp_cleanup(self):
        seen = []
        def process(command, **kwargs):
            seen.append((command, kwargs))
            self.assertIn('--sandbox', command)
            self.assertIn('read-only', command)
            self.assertIn('--ephemeral', command)
            self.assertIn('--ignore-user-config', command)
            self.assertNotIn('private question', ' '.join(command))
            output = Path(command[command.index('--output-last-message') + 1])
            output.write_text('{"message":"hello"}', encoding='utf-8')
            return subprocess.CompletedProcess(command, 0, '', '')
        with tempfile.TemporaryDirectory() as folder:
            with patch('clydex.providers.codex.shutil.which', return_value='codex.exe'), \
                    patch('clydex.providers.codex.run_process', side_effect=process):
                answer = CodexProvider(Path(folder)).respond(
                    ProviderRequest('answer', '{"question":"private question"}', json.dumps(SCHEMA)),
                    CancellationToken())
            self.assertEqual(answer, {'message': 'hello'})
            self.assertEqual(list(Path(folder).iterdir()), [])
        self.assertIn('private question', seen[0][1]['input'])

    def test_timeout_and_malformed_response_fail(self):
        with patch('clydex.providers.codex.shutil.which', return_value='codex.exe'), \
                patch('clydex.providers.codex.run_process', side_effect=subprocess.TimeoutExpired('codex', 1)):
            with self.assertRaises(ProviderError):
                CodexProvider().respond(ProviderRequest('answer', '{}', json.dumps(SCHEMA)), CancellationToken())

    def test_invalid_plan_enum_rejected(self):
        from clydex.core.commands import PLAN
        value = {'steps': [{'action': 'send_email', 'target': '', 'detail': '', 'control': ''}], 'message': ''}
        with self.assertRaises(ProviderError):
            validate_response(value, PLAN)
