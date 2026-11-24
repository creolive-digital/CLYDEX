# Repository Guidelines

## Project Structure & Module Organization

This is a small Windows desktop application with a flat repository layout. `clydex_widget.pyw` implements the clock and weather widget; `clydex_voice_agent.pyw` implements the hologram chat and voice assistant. `clydex_hologram.png` is the assistant image asset. `requirements.txt` lists Python dependencies, while `INSTALL_REQUIREMENTS.bat` and `START_CLYDEX.bat` provide Windows setup and launch shortcuts. There is currently no test or package directory.

## Build, Test, and Development Commands

Run commands from the repository directory in Windows CMD or PowerShell:

- `py -m pip install -r requirements.txt` installs the voice assistant dependencies.
- `py clydex_widget.pyw` launches the widget (standard library only).
- `py clydex_voice_agent.pyw` launches the voice assistant with console output for troubleshooting.
- `START_CLYDEX.bat` starts the packaged app using the repository's intended launcher.

There is no build step or automated test command configured. The voice assistant requires Windows 10/11, Python 3.10+, audio devices, and a logged-in Codex CLI; consult `README_SETUP.txt` for setup details.

## Coding Style & Naming Conventions

Keep the existing flat layout and use descriptive `snake_case` names for Python files, functions, and variables. Follow the current four-space Python indentation and standard-library-first approach. Keep widget and voice-assistant changes in their respective modules unless a shared concern clearly requires otherwise. Preserve Windows `.pyw` launch behavior and update batch files or `requirements.txt` when runtime setup changes.

## Testing Guidelines

No test framework or coverage requirement is configured. For changes, run the affected `.pyw` entry point on Windows and manually check relevant behavior. For UI, audio, or weather changes, verify the feature in the running app; these integrations are platform and device dependent. Avoid claiming automated coverage unless tests are added and run.

## Commit & Pull Request Guidelines

This checkout has no Git metadata, so repository-specific commit conventions cannot be confirmed. Use a short imperative commit subject (for example, `Fix widget weather refresh`). Pull requests should describe the user-visible change, list manual verification and its Windows environment, note dependency or configuration changes, and include screenshots for visual changes.

## Security & Configuration Tips

Do not commit credentials, transcripts, or local configuration secrets. The voice assistant sends prompts to the Codex service; follow the privacy notes in `README_SETUP.txt` and avoid dictating sensitive information.
