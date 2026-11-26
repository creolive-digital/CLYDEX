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
2. Double-click INSTALL_REQUIREMENTS.bat or in CMD: py -m pip install -r requirements.txt
3. Check login: codex login status (log in with codex login if needed).
4. Double-click START_CLYDEX.bat or clydex_widget.pyw.
5. Click Agent on the clock. Type a prompt or click Use Live Mic, then Stop recording.
6. For errors, run in CMD: py clydex_voice_agent.pyw

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
