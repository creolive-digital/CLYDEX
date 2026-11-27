# Phase 04 frontend architecture

React/TypeScript/Vite replaces the primary Studio presentation incrementally. `frontend/legacy` remains unchanged and launchable with `python scripts/windows/clydex_voice_agent.pyw --legacy`. A missing HUD build selects that fallback. Both presentations use the existing CoreApplication; there is no new AI, voice, conversation, memory or permission engine.

## Build and source boundaries

```powershell
npm --prefix frontend ci
npm --prefix frontend test
npm --prefix frontend run build
python scripts/windows/clydex_voice_agent.pyw
```

Node 24 is used in CI. Exact dependency versions and integrity checks are in `frontend/package-lock.json`. Vite uses relative URLs and emits only to ignored `deployment/windows/artifacts/frontend`. JavaScript, fonts, images, icons, license notices and CSS ship locally. No CDN, paid API, downloaded speech model or character asset is needed to render the HUD. PyInstaller copies that directory to `frontend/hud` alongside the legacy UI and embedded bridge JSON. The agent includes Tk because the shared time-tools adapter reuses the existing widget. Windows `.js` MIME associations are overridden for the local asset server: this workstation classified modules as `text/plain`, which blocked native loading until corrected.

`src/app` composes navigation and display layouts; `components` contains reusable forms, panels and dialogs. Features contain chat, intelligence/history, memory, voice/personality, avatar, settings/widget, permissions and notifications. `services/bridge` validates inbound frames and wraps typed commands; `stores/desktop` owns one polling subscription; `hooks/useRead` loads management sections. Tokens/styles, accent contrast and the renderer are separate. Only implemented modules exist; there are no future-feature page placeholders.

## Bridge and ownership

Only `HudBridge.hud_snapshot()`, `hud_read(section, params)` and `hud_command(action, payload)` are exposed to the new WebView. `src/clydex/desktop/hud_contract.json` defines version 1 and the exact operation/argument inventory; TypeScript imports the same JSON and declares precise call-site payloads. Python rejects unknown operations/fields, wrong primitive types, non-finite JSON and requests above 64 KiB. Nested values are validated by the existing provider/voice/data services and typed preferences. There is no arbitrary attribute dispatch, shell, Python, filesystem or credential retrieval method.

Reads cover bootstrap, intelligence, voice, memories, histories/export, preferences, permissions and widget state. Commands cover text chat/clear, voice controls/configuration/model review, provider/routing configuration/check review, personality, conversation/memory actions, exact approval, display/monitor selection, presentation/capability restrictions and bounded time-tool actions. Provider keys are accepted only for reviewed replacement; existing keys never return to JavaScript. The CSP permits local assets, forbids remote scripts/frames/forms and avoids HTML interpolation of external text.

A Core-owned collector is the sole consumer of Studio's draining event channel. It retains at most 100 transient messages and 100 generic notifications. The frontend requests snapshots every 120 ms when visible and every second when hidden; only one request runs at a time. Generation guards discard responses after cleanup. A failed bridge clears visible private state. Native tray Stop/mute remain available when configured; the legacy launcher remains the recovery route if rendering fails before tray configuration.

Assistant operating actions and reviewed settings/data changes reuse Studio, the supervised serial queue, trusted ToolSpecs, the central executor and existing exact-action reviews. Ordinary navigation/window layout and clearing generic notification presentation remain local view controls. Added scopes are `desktop.settings`, `security.settings`, `desktop.time_tools` and `desktop.weather`; the first two require review, local time controls retain low-risk handling, weather explicitly reviews the city/destination. Runtime disabled scopes are unioned with startup restrictions, so the UI cannot relax the startup ceiling. Presentation/profile edits cannot activate memory, capture or a provider. Browser input is not authentication.

## Window, privacy and lifecycle

DisplayController changes one native window between standard, full-screen, Smart Widget, Floating Hologram, Mini Voice Bar and tray. It never constructs a second Core, microphone, queue or engine. Tray hiding requires a successfully running reviewed native tray service. Compact/hide requests are refused during approval; native collection restores a full window for a new review without depending on hidden browser timers. Every visible mode retains Stop/microphone controls; the tray menu retains Stop/mute/open. Geometry is bounded to enumerated logical monitor rectangles, including negative origins, and stored atomically outside source. WebView2 handles native scaling; real multi-monitor/mixed-DPI qualification remains external.

The Smart Widget lazily owns one Tk thread adapting the unchanged widget's clock/weather/timer/alarm/stopwatch methods. Every HUD mode shares those objects; switching views preserves timers. Its hidden Tk UI performs no automatic weather request, bell or visual animation. Explicit weather uses the existing bounded requests after review. Native state pumping, resource disposal and joining remain part of Core ownership. Standalone widget fallback remains an independent application; do not run two widgets expecting synchronized clocks/tools.

VoicePrivacy's native watcher and action-time checks remain authoritative. On lock, the HUD clears transient chat/reviews/notifications and unmounts every management form, including unsaved keys. A synthetic lock-probe test establishes UI behavior, not physical lock-screen certification. No raw audio, prompts or private titles are added to diagnostic logs. Preferences (`desktop.json`, `display.json`, `display-monitor.json`, `desktop-permissions.json`) contain non-secret values under `%LOCALAPPDATA%/CLYDEX/settings`; encrypted data and secret storage remain unchanged. Startup restores standard-window bounds/monitor, never silently restores a hidden or on-top capture mode. Windows on-top changes are explicitly invoked on the WinForms thread to avoid an observed PyWebView cross-thread hang.

## Startup, notifications and verification

Bootstrap reports constructed Core/config/database as ready, voice as gated, and provider health as unverified; it makes no connectivity/inference request. Startup supports skip, reviewed animation/silent/reduced-motion preferences and an optional neutral local greeting subject to voice privacy. Procedural original oscillator cues need a user gesture and respect mute, volume, DND, visibility and lock policy. Native tray balloons contain generic text, not prompt/message content.

`frontend/tests` covers contracts, literal text rendering, controls, review IDs, memory consent, polling teardown, startup timing and renderer teardown/fallback. `tests/test_hud.py` covers Python contracts/privacy/reviews/scopes/geometry. `scripts/verify_hud_smoke.py --output <outside-source-directory>` runs the actual production build in Windows WebView2 with a disposable profile and no audio/provider/weather calls. It captures only the application's client area using WebView2 CapturePreview, never the user's desktop. See the completion report for actual outcomes, screenshots and acceptance boundaries.
