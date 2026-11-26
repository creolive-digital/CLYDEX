CLYDEX FINAL EDITION — Windows 10/11
=======================================
WHAT YOU GET
- CLYDEX Mini desktop flip clock with the Voice Agent’s cyan controls, icons, and local fonts.
- The desktop app pairs a live transcript with the Stitch wireframe acoustic core.
  Its rings, waveform, and frequency bars respond to microphone and speech playback audio.
- Text and voice requests, with local handling for common Windows commands and
  Codex for conversation and multi-step tasks.
- Multi-step Windows tasks, visible Chrome or Edge browsing and Outlook inbox summaries.
- Windows SAPI reads replies aloud. The spectrum measures the audio samples
  used for recording or playback and shows the energy in 36 bands.

REQUIREMENTS
- Microsoft Edge WebView2 Runtime for the desktop interface.
- Windows 10/11, Python 3.10+ (3.11 recommended), microphone and audio output.
- Codex CLI installed and logged in: codex --version && codex login status.
  Use a version with codex exec --ignore-user-config and --ephemeral (tested with 0.171).
- Internet for Codex and weather. First Whisper model use may download files.

SETUP
1. Unzip folder somewhere writable, e.g. Documents\CLYDEX_FINAL_EDITION.
2. Double-click scripts\windows\INSTALL_REQUIREMENTS.bat or in CMD: py -m pip install -r deployment\windows\requirements.txt
3. Check login: codex login status (log in with codex login if needed).
4. Double-click scripts\windows\START_CLYDEX.bat or scripts\windows\clydex_widget.pyw.
5. Click Agent on the clock. Type a prompt or click Use Live Mic, then Stop recording.
6. For errors, run in CMD: py scripts\windows\clydex_voice_agent.pyw

USE
- Try "Open Notepad", "Minimise Calculator" or "Which windows are open?"
  These single commands run locally. Other requests use Codex.
- Say "Which windows are open?", "Switch to Notepad", "Maximize Calculator"
  or "Restore window 2". If several windows match, choose one by number.
- Ask "What controls are available in Calculator?", then name the button
  to press. To dictate, try "Append Friday works for me to Notepad".
  CLYDEX shows the window, control, and proposed text before acting. You can
  also ask it to close a window and respond to the app's normal save prompt.
  Available controls depend on what each app exposes to Windows accessibility.
- Try "Show me the five largest files in Downloads" or "Create a folder named
  Receipts in Documents". CLYDEX describes each proposed PowerShell step in its
  window. Run task approves that step once. Cancel stops the remaining steps.
  Inspect PowerShell command shows the exact script. Commands run in the background
  with your Windows account's permissions, starting in your user profile.
- Try "Open Chrome at https://example.org and tell me what the site is for".
  CLYDEX reads the visible page in its own browser window. Install Chrome or ask
  for Edge. You can interact with that window and ask CLYDEX to reread the page.
- To read a page you already opened, select its tab in Chrome or Edge, keep
  the window open and unminimized, then switch to CLYDEX and ask "Read this tab".
  For example, open an email in Outlook on the web and ask "Summarize the
  message in my Outlook tab." The inbox list exposes previews. Open a message
  to read its body. CLYDEX uses the page text exposed through Windows
  accessibility in the frontmost matching browser window. This requires no
  Outlook account setup in CLYDEX and also works on other text-based pages.
- In Audio settings, English · fast is the default for spoken English, including
  English with a Sinhala accent. English · higher accuracy uses a larger English
  model (about 480 MB on first download) and may take longer on a CPU. Use
  Auto-detect language when speaking another language. CLYDEX remembers the
  selection for your Windows user. If speech is unclear, it asks you to repeat.
- Open Audio settings to toggle Speak replies or select and check the microphone.
  The microphone button starts recording and Stop finishes the message.
- Assistant voice comes from the installed Windows SAPI voice. Best with English;
  Sinhala speech synthesis requires compatible Windows speech voice/language support.
- Input speech recognition works offline AFTER its model is cached locally.
- Click the clock’s settings gear or right-click to change city, refresh weather,
  switch compact/full view or 12/24-hour time, toggle always on top, or close.
- Drag the mini widget by its header. Clock, Timer, Alarm and Stopwatch work
  in compact and full views. A dot beside a tab marks an active tool.
- Timer offers 5, 15 and 25 minute presets, custom durations (for example
  0:30), pause, resume and reset. Stopwatch shows elapsed time and the latest
  lap's timestamp. Both keep time while you use other tabs.
- Alarm uses local 24-hour time. A time that has passed rings the next day.
  Keep the widget running for alarms and countdowns. An alert sounds and
  stays on screen until dismissed. Alarms also offer a five-minute snooze.

OPTIONAL CONNECTED MAILBOX SETUP
- For direct mailbox access, ask "Summarize unread messages in my connected
  Outlook mailbox", then "Draft a reply to message 2 saying Friday works".
  This uses up to 12 matching inbox messages. Review and send in Outlook.
- Classic Outlook uses the default configured Windows Outlook profile.
- For new Outlook or Outlook.com with a Microsoft-hosted mailbox, register a
  desktop public client application in Microsoft Entra. Choose the account types
  you use, add http://localhost under Mobile and desktop applications and add
  delegated Microsoft Graph Mail.ReadWrite permission for reading and drafting.
  Set the following in CMD, then restart CLYDEX from a newly opened session:
    setx CLYDEX_OUTLOOK_CLIENT_ID "your-application-client-id"
  Sign in in the browser when first asked. Tokens stay in the running app's
  memory. Drafts are saved in Outlook. Your organization may require consent.
  Microsoft registration guide:
  https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app

PRIVACY/SAFETY
- Microphone recorded only after clicking START LISTENING; click STOP to finish.
- Speech is transcribed on the PC. Requests that need Codex include the current
  question and recent conversation, which can include earlier local commands.
- Codex receives the page text, inbox excerpts, window and control labels or command output needed to
  answer your request. Clear transcript also clears CLYDEX's inbox snapshot.
- Codex plans in a temporary, read-only session. The local Windows runner can
  access the files and applications your account can access. Review the described
  changes before approval. Canceling a later step leaves earlier changes in place.
- Microphone processing and Windows SAPI speech playback use in-memory audio.

NOTES
- Windows tasks use PowerShell 5.1. Spoken replies use the installed Windows SAPI voice.
- If the Windows output device does not support the synthesized sample rate,
  audio playback may fail: check sounddevice installation and Windows sound settings.
- Requires network access for weather and typical Codex CLI usage.
- UI/voice/codex end-to-end behavior must be tested on your own Windows PC.

V2 PHASE 01 DEVELOPMENT BRANCH
- Launcher filenames remain supported under scripts\windows\. Implementation is now packaged under
  src/clydex; deployment\windows\requirements.txt installs it in editable mode for development.
- Use a verified interpreter. On the development PC, python works while the
  default py launcher points at a missing installation. Do not reinstall Python
  just to work around that launcher; use an installed interpreter explicitly.
- Runtime storage is %LOCALAPPDATA%\CLYDEX\, outside the project. Copy
  config\clydex.example.json to settings\config.json under that runtime directory
  if you want to customize non-secret settings. Unknown settings are rejected.
  .env.example documents environment variables; .env files are not auto-loaded.
- Voice preferences are stored in the local metadata database; an existing HKCU
  recognition preference is read only as a fallback. No registry values are deleted.
- Sensitive reads, native drafts, PowerShell, close/control actions and private
  context transfers require an exact, expiring, one-time approval. Inspect the
  displayed action/data before approving. Rejecting a later step leaves any
  earlier completed changes in place. Approvals do not sandbox PowerShell.
- Stop task cancels pending reviews/work and requests interruption of active work.
  Native COM, audio/model code or external apps can take time to return; completed
  changes are not undone. Stopping recording normally still transcribes the clip.
- Set CLYDEX_ALLOW_CLOUD=false or CLYDEX_PRIVACY_MODE=true to block Codex calls.
  Deterministic local commands still work. disabled_scopes in config.json can
  disable individual capabilities (for example shell.powershell or mail.inbox).
  Restart after changing policy configuration. No cloud fallback is added.
- Only one Core instance may own a user's runtime directory. Close the existing
  assistant before opening another instance. The widget remains independent.
- Local SQLite stores allowlisted voice preferences and audit metadata only.
  Do not place credentials, conversations, private documents or audio in it.
  The credential storage API uses Windows Credential Manager; Codex still uses
  its existing CLI login. No new provider account is activated by this migration.
- Developer checks:
    python -m unittest discover -v
    python -m ruff check src tests
    python scripts/verify_windows_smoke.py --webview
  Install the optional lint tooling with: python -m pip install -e ".[dev]"
  Add --credentials to smoke-test native Credential Manager with a synthetic
  value that is deleted immediately. UI smoke tests disable weather/cloud/audio.
- Phase 02 and later features, React HUD, cloud account/sync, new AI providers,
  memory collection, wake word, new artwork, plugins and devices are not shipped
  by Phase 01. See docs\DEVELOPMENT_PROGRESS.md for evidence and remaining gates.

V1 ARCHIVE
- The original e65fe46 release is preserved independently in v1-old\, including
  its original launchers, modules, UI, artwork, requirements and build scripts.
  Run v1-old\START_CLYDEX.bat from the checkout root to use the original V1 application.
- Launchers under scripts\windows\ start active V2. V2's shared widget, theme and older
  hologram helper now live in src\clydex\desktop\. Its artwork is in assets\legacy\.
  V2's static studio_ui\ includes the current approval and Stop controls.
- V2 does not load code or resources from v1-old\. Archived files retain V1's
  original behavior and approval system. See v1-old\README_ARCHIVE.md.

CURRENT V2 FILE LOCATIONS
- Launchers and Windows setup/build shortcuts: scripts\windows\.
- PyInstaller specifications: installer\pyinstaller\.
- Inno Setup script and installer notes: installer\windows\.
- Desktop dependencies: deployment\windows\requirements.txt (run pip from the checkout root).
- Active static UI: frontend\legacy\; V2 business logic: src\clydex\.
- Obsolete root Python import facades were removed; import clydex package modules directly.
- Root contains project metadata and README.md; original V1 remains in v1-old\.
