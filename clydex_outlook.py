"""Read a bounded Outlook inbox snapshot and create native, unsent replies."""
from contextlib import contextmanager
import os
from urllib.parse import quote
import webbrowser


@contextmanager
def classic_session():
    import pythoncom
    from win32com.client import Dispatch

    pythoncom.CoInitialize()
    try:
        try:
            namespace = Dispatch('Outlook.Application').GetNamespace('MAPI')
        except Exception as exc:
            raise RuntimeError('Open classic Outlook with a configured profile, or connect '
                               'Microsoft 365 / Outlook.com as described in README_SETUP.txt.') from exc
        yield namespace
    finally:
        pythoncom.CoUninitialize()


class OutlookInbox:
    def __init__(self):
        self.client_id = os.getenv('CLYDEX_OUTLOOK_CLIENT_ID')
        self.client = None
        self.messages = []

    def _graph(self, method, path, **kwargs):
        import msal
        import requests

        if self.client is None:
            self.client = msal.PublicClientApplication(
                self.client_id, authority='https://login.microsoftonline.com/common')
        scopes = ['Mail.ReadWrite']
        accounts = self.client.get_accounts()
        token = self.client.acquire_token_silent(scopes, accounts[0]) if accounts else None
        if not token or 'access_token' not in token:
            token = self.client.acquire_token_interactive(scopes=scopes, timeout=120)
        if 'access_token' not in token:
            raise RuntimeError('Outlook sign-in did not complete. Check the app registration and account.')
        response = requests.request(
            method, 'https://graph.microsoft.com/v1.0/me/' + path, timeout=30,
            headers={'Authorization': 'Bearer ' + token['access_token'],
                     'Prefer': 'outlook.body-content-type="text"'}, **kwargs)
        if not response.ok:
            raise RuntimeError(f'Outlook returned HTTP {response.status_code}. Check Microsoft account access.')
        return response.json()

    def recent(self, unread=False):
        self.messages = []
        rows = []
        if self.client_id:
            params = {'$top': 12, '$select': 'id,from,subject,body,receivedDateTime,importance,isRead',
                      '$orderby': 'receivedDateTime desc'}
            if unread:
                params['$filter'] = 'receivedDateTime ge 1900-01-01T00:00:00Z and isRead eq false'
            for item in self._graph('GET', 'mailFolders/inbox/messages', params=params)['value']:
                sender = (item.get('from') or {}).get('emailAddress', {})
                rows.append((item['id'], {'sender': sender, 'subject': item['subject'],
                             'received': item['receivedDateTime'], 'importance': item['importance'],
                             'body': item['body']['content'][:2400]}))
        else:
            with classic_session() as namespace:
                inbox = namespace.GetDefaultFolder(6)
                items = inbox.Items.Restrict('[Unread] = True') if unread else inbox.Items
                items.Sort('[ReceivedTime]', True)
                for item in items:
                    if item.Class == 43:  # olMail
                        rows.append(((item.EntryID, inbox.StoreID),
                                     {'sender': item.SenderName, 'subject': item.Subject,
                                      'received': str(item.ReceivedTime), 'importance': item.Importance,
                                      'body': (item.Body or '')[:2400]}))
                    if len(rows) == 12:
                        break
        self.messages = rows
        return self.snapshot()

    def snapshot(self):
        return [dict(data, number=i) for i, (_, data) in enumerate(self.messages, 1)]

    def draft(self, number, body):
        if type(number) is not int or not 1 <= number <= len(self.messages) or not body.strip():
            raise ValueError('Choose one message from the last inbox summary and give a reply.')
        key, data = self.messages[number - 1]
        if self.client_id:
            result = self._graph('POST', 'messages/' + quote(key, safe='') + '/createReply',
                                 json={'comment': body})
            link = result.get('webLink', '')
            if link.startswith('https://'):
                webbrowser.open(link)
        else:
            with classic_session() as namespace:
                reply = namespace.GetItemFromID(*key).Reply()
                reply.Body = body + '\r\n\r\n' + (reply.Body or '')
                reply.Save()
                reply.Display(False)
        return f'Prepared a reply to “{data["subject"]}”. Review it in Outlook Drafts and click Send to approve.'
