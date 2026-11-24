CLYDEX FINAL EDITION — Windows 10/11
=======================================
WHAT YOU GET
- CLYDEX Mini desktop flip clock with the Voice Agent’s cyan controls, icons, and local fonts.
- The desktop app pairs a live transcript with the Stitch wireframe acoustic core.
  Its rings, waveform, and frequency bars respond to microphone and speech playback audio.
- Text chat and mic -> local Whisper transcription -> Codex CLI response.
- Windows System.Speech reads replies aloud. The spectrum measures the audio samples
  used for recording or playback and shows the energy in 36 bands.

REQUIREMENTS
- Microsoft Edge WebView2 Runtime for the desktop interface.
- Windows 10/11, Python 3.10+ (3.11 recommended), microphone and audio output.
- Codex CLI installed and logged in: codex --version && codex login status
- Internet for Codex and weather. First Whisper model use may download files.

SETUP
1. Unzip folder somewhere writable, e.g. Documents\CLYDEX_FINAL_EDITION.
2. Double-click INSTALL_REQUIREMENTS.bat or in CMD: py -m pip install -r requirements.txt
3. Check login: codex login status (log in with codex login if needed).
4. Double-click START_CLYDEX.bat or clydex_widget.pyw.
5. Click Agent on the clock. Type a prompt or click Use Live Mic, then Stop recording.
6. For errors, run in CMD: py clydex_voice_agent.pyw

USE
- Ask naturally to open an installed app. Codex interprets the request and Clydex opens the matching Windows Start menu entry.
- Open Audio settings to toggle Speak replies or select and check the microphone.
  The microphone button starts recording and Stop finishes the message.
- Assistant voice comes from the installed Windows SAPI voice. Best with English;
  Sinhala speech synthesis requires compatible Windows speech voice/language support.
- Input speech recognition works offline AFTER its model is cached locally.
- Click the clock’s settings gear or right-click to change city, refresh weather,
  switch compact/full view or 12/24-hour time, toggle always on top, or close.
- Widget header can be dragged.

PRIVACY/SAFETY
- Microphone recorded only after clicking START LISTENING; click STOP to finish.
- Captured question is sent to Codex's online model service. Transcript and chat
  may therefore be handled by the service; don't dictate secrets.
- Codex uses --sandbox read-only and a temporary working directory, with instructions
  to answer questions or select an app for Clydex to launch.
- Windows SAPI speech synthesis generates a temporary WAV file, then plays it.
  Temp audio files are removed after playback.

NOTES
- Windows PowerShell 5.1 and System.Speech are included on typical Windows systems.
- If the Windows output device does not support the synthesized sample rate,
  audio playback may fail: check sounddevice installation and Windows sound settings.
- Requires network access for weather and typical Codex CLI usage.
- UI/voice/codex end-to-end behavior must be tested on your own Windows PC.
