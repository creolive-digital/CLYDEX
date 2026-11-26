# CLYDEX V1 archive

Standalone original release from commit `e65fe46e19e554066a43926f4a0e5335843096c8`, before the V2 foundation migration. Original tracked files were restored byte-for-byte from that commit; no runtime data or Git metadata is included. Keep these original files unchanged.

From this folder, run `python clydex_widget.pyw` or `python clydex_voice_agent.pyw`. `START_CLYDEX.bat`, the original requirements, artwork, UI, tests and installer scripts are included. Existing Windows/audio/Codex prerequisites still apply; see README_SETUP.txt. The original default `py` launcher may need an explicitly selected installed interpreter on this workstation.

This archive retains V1's original behavior and approval system. Active V2 is maintained in the parent directory under `src/clydex/`, with launchers under scripts/windows/, updated approval UI and V2 tests. V2 does not load code or assets from this archive. Shared widget functionality now has an active implementation in `src/clydex/desktop/widget.py`; V2 artwork is in `assets/legacy/` and its current static UI is in `frontend/legacy/`.

To run the original four tests independently: `python -m unittest discover -v` from this folder. Avoid mixing V1 and V2 imports in the same Python process.
