"""Windows task execution, open-tab reading, and CLYDEX browser navigation."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
from urllib.parse import urlsplit


def read_browser_tab(title_hint='', channel=''):
    """Read the selected tab in the frontmost matching normal browser window."""
    import pywintypes
    import win32api
    import win32con
    import win32gui
    import win32process

    browsers = {'chrome.exe': 'chrome', 'msedge.exe': 'msedge'}
    title_hint = title_hint.strip().casefold()
    channel = channel.strip().casefold()
    if channel == 'edge':
        channel = 'msedge'
    windows = []
    win32gui.EnumWindows(lambda hwnd, _: windows.append(hwnd), None)
    for hwnd in windows:
        try:
            if (not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd)
                    or win32gui.GetClassName(hwnd) != 'Chrome_WidgetWin_1'):
                continue
            title = win32gui.GetWindowText(hwnd)
            if not title or title_hint not in title.casefold():
                continue
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = win32api.OpenProcess(
                win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
            try:
                exe = Path(win32process.GetModuleFileNameEx(process, 0)).name.lower()
            finally:
                process.Close()
            if exe not in browsers or (channel and channel != browsers[exe]):
                continue
        except pywintypes.error:
            continue  # An unrelated window may have closed or belong to another user.
        script = Path(__file__).with_name('read_browser_tab.ps1')
        try:
            read = subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                 '-File', str(script), str(hwnd)], capture_output=True, text=True, encoding='utf-8',
                errors='replace', timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError('The browser took too long to expose its page text. Select the tab and try again.') from exc
        if not win32gui.IsWindow(hwnd) or win32gui.GetWindowText(hwnd) != title:
            raise ValueError('The selected browser tab changed while I was reading it. Please ask again.')
        if read.returncode or not read.stdout.strip():
            raise ValueError('I could not read page text in that tab. Open the message or page, '
                             'let it load, and ask again.')
        return {'title': title, 'visible_text': read.stdout.strip()}
    raise ValueError('Select the tab you want in Chrome or Edge, keep the window open and '
                     'unminimized, then switch to CLYDEX and ask “Read this tab”.')


def run_windows_task(script, cancel=None):
    # Keep generated text out of the process arguments. Both pipe ends use UTF-8.
    wrapper = (
        '$utf8 = [Text.UTF8Encoding]::new($false); '
        '[Console]::InputEncoding = $utf8; [Console]::OutputEncoding = $utf8; '
        "$ErrorActionPreference = 'Stop'; "
        '& ([ScriptBlock]::Create([Console]::In.ReadToEnd())); '
        'if (-not $?) { exit 1 }'
    )
    try:
        from clydex.automation.tasks import CancellationToken
        from clydex.core.processes import run_process
        result = run_process(
            ['powershell.exe', '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', wrapper],
            input=script, cwd=Path.home(), timeout=120, cancel=cancel or CancellationToken())
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('PowerShell timed out. Some changes may already have happened.') from exc
    return {'exit_code': result.returncode, 'output': result.stdout[-8000:],
            'errors': result.stderr[-2000:]}


class DesktopBrowser:
    """Playwright and its browser stay on one thread across voice and text turns."""

    def __init__(self):
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix='clydex-browser')
        self.driver = self.browser = self.page = None
        self.channel = None

    def visit(self, url, channel):
        if url:
            parts = urlsplit(url)
            if (parts.scheme not in ('http', 'https') or not parts.hostname
                    or parts.username is not None or parts.password is not None):
                raise ValueError('Give CLYDEX an HTTP or HTTPS website address.')
        if channel not in ('chrome', 'msedge', ''):
            raise ValueError('Choose Chrome or Edge.')
        return self.worker.submit(self._visit, url, channel).result()

    def _visit(self, url, channel):
        from playwright.sync_api import sync_playwright

        if not url and (self.page is None or self.page.is_closed()):
            raise ValueError('Give me the address of the page to open first.')
        channel = channel or self.channel or 'chrome'
        if self.driver is None:
            self.driver = sync_playwright().start()
        if not self.browser or not self.browser.is_connected() or channel != self.channel:
            if self.browser and self.browser.is_connected():
                self.browser.close()
            self.browser = self.driver.chromium.launch(channel=channel, headless=False)
            self.channel = channel
            self.page = None
        if not self.page or self.page.is_closed():
            self.page = self.browser.new_page(accept_downloads=False)
        self.page.bring_to_front()
        if url:
            response = self.page.goto(url, wait_until='domcontentloaded', timeout=35000)
            if response and response.status >= 400:
                raise RuntimeError(f'The website returned HTTP {response.status}.')
        self.page.locator('body').wait_for(timeout=10000)
        # Wait for visible text on sites that render after DOMContentLoaded.
        self.page.wait_for_function("document.body.innerText.trim().length > 0", timeout=10000)
        return {'url': self.page.url, 'title': self.page.title(),
                'visible_text': self.page.locator('body').inner_text(timeout=10000)[:16000]}

    def close(self):
        def stop():
            if self.driver:
                self.driver.stop()
        self.worker.submit(stop)
        self.worker.shutdown(wait=False)
