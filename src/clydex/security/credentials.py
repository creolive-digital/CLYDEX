"""Windows Credential Manager; no unencrypted storage fallback."""
import os
import re


class CredentialStore:
    @staticmethod
    def _target(name: str) -> str:
        if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9_.-]{0,63}', name):
            raise ValueError('Invalid credential identifier.')
        return 'CLYDEX/' + name

    def get(self, name: str) -> str | None:
        target = self._target(name)
        if os.name != 'nt':
            raise RuntimeError('Windows Credential Manager is required for durable secrets.')
        import win32cred
        import pywintypes
        try:
            value = win32cred.CredRead(target, win32cred.CRED_TYPE_GENERIC)
        except pywintypes.error as exc:
            if exc.winerror == 1168:
                return None
            raise
        blob = value['CredentialBlob']
        return blob.decode('utf-16-le') if isinstance(blob, bytes) else blob

    def set(self, name: str, secret: str) -> None:
        target = self._target(name)
        if not isinstance(secret, str) or not secret or len(secret.encode('utf-16-le')) > 2560:
            raise ValueError('Invalid credential value.')
        if os.name != 'nt':
            raise RuntimeError('Windows Credential Manager is required for durable secrets.')
        import win32cred
        win32cred.CredWrite({'Type': win32cred.CRED_TYPE_GENERIC, 'TargetName': target,
                            'UserName': 'CLYDEX', 'CredentialBlob': secret,
                            'Persist': win32cred.CRED_PERSIST_LOCAL_MACHINE}, 0)

    def delete(self, name: str) -> None:
        target = self._target(name)
        if os.name != 'nt':
            raise RuntimeError('Windows Credential Manager is required for durable secrets.')
        import win32cred
        import pywintypes
        try:
            win32cred.CredDelete(target, win32cred.CRED_TYPE_GENERIC, 0)
        except pywintypes.error as exc:
            if exc.winerror != 1168:
                raise
