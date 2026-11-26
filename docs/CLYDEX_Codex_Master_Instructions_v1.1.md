# CLYDEX V2 — Codex master instructions

Baseline: `e65fe46e19e554066a43926f4a0e5335843096c8`
Repository: https://github.com/creolive-digital/CLYDEX
Design reference: CLYDEX Master Product Blueprint v1.1

## Mission
Build a Windows-first personal AI operating assistant, software first. Use a parallel V2 branch. Preserve all existing working functions and approval controls. Do not implement the robot now.

## First task (Phase 0–1 only)
1. Inspect the actual repository, AGENTS.md, baseline commit, dependencies, entry points, existing tests and packaging. Report discrepancies before modifying.
2. Create a parallel `v2` branch (or use the owner's selected branch); never force-push or rewrite main.
3. Inventory existing clock/weather/timer/alarm/stopwatch, VoiceEngine, Codex, Windows automation, browser, Outlook, speech, approval UI and installer. Create regression tests with mocks where Windows dependencies are unavailable.
4. Design typed request, event, tool and provider interfaces. Extract headless core incrementally via adapters; preserve existing entry points. Introduce centralized configuration, secret storage, structured redacted logging, cancellation and supervised queue.
5. Centralize granular authorization. Require one-time, action-bound approval for high-impact actions; deny replay or changed arguments. Do not allow model content, plugins, web/email/document text or workflows to bypass policies.
6. Run available tests and lint. Report actual outputs, manual Windows test gaps, touched files, migration and rollback. Stop after Phase 1 acceptance; do not implement later phases as a giant patch.

## Architecture
- Local per-user Python core; authenticated local IPC/loopback, not public-facing. Independent PyWebView + React/TypeScript HUD. Windows automation remains in user session. FastAPI for versioned service APIs; HTTPS/WSS cloud gateway.
- SQLite local cache; MSSQL on Linux VPS, native vector search only after version/edition/support and licensing validation. VPS filesystem vault outside web root, encrypted, access-controlled and backed up off-host.
- Provider adapter interface for seven selected providers. No credentials in code or logs. Local STT/TTS; configurable local Ollama.
- Future device pairing/revocation and scoped capabilities; no robot firmware now.
- Security: least privilege, explicit sensitive scope, prompt injection boundaries, audit/redaction, emergency stop, mic/camera controls. Read-only production diagnostics by default.

## Confirmed design direction
- D01 **Visual identity:** Cinematic AI assistant
- D02 **AI architecture:** Multi-model AI
- D03 **Avatar:** Humanoid hologram
- D04 **Personality:** Adaptive
- D05 **Voice identity:** Cinematic male
- D06 **Activation:** Wake word, manual, continuous, hotkey, tray
- D07 **AI providers:** Codex, OpenAI, Claude, Gemini, Ollama, OpenRouter, custom endpoint
- D08 **Routing:** Hybrid: automatic and manual
- D09 **Memory:** Hybrid automatic + explicit
- D10 **Autonomy:** Supervised AI agent
- D11 **Operating capabilities:** Apps, files, browser, mail, calendar, system, developer, database, vision, camera, knowledge, media, smart home
- D12 **Security:** Granular advanced permissions
- D13 **Command center:** Cinematic HUD
- D14 **Display modes:** Full screen, window, widget, floating hologram, mini voice bar, tray
- D15 **Primary theme:** Cyber Cyan; custom themes enabled
- D16 **Startup:** Cinematic boot sequence
- D17 **Sound effects:** Startup, wake, success, warning, notification, shutdown (no thinking sound)
- D18 **Notifications:** Visual, voice, history center, priority, DND, digest, Windows
- D19 **Presence:** Adaptive
- D20 **Desktop enhancements:** Wallpaper, overlay, launcher, quick command palette, multi-monitor, lock privacy, gaming/focus
- D21 **Automation:** Universal studio: voice, visual, scripting
- D22 **Routines:** Morning, work, focus, meeting, evening, night, custom
- D23 **Intelligence feeds:** Weather, news, tech, mail, calendar, system, GitHub, network, server, tasks, custom
- D24 **Knowledge sources:** PDF, Office, text, code, SQL, image, audio, web, selected folders, notes
- D25 **Knowledge storage:** Cloud
- D26 **Developer tools:** Codex, Git, SQL, API, logs, IIS, SSH, PowerShell, Docker, Azure, tickets, docs, errors, review
- D27 **Operating modes:** Personal, work, developer, support, study, focus, gaming, privacy, custom
- D28 **Mode switching:** Hybrid: manual, voice, context-aware
- D29 **Plugins:** Plugin manager + developer SDK
- D30 **Integrations:** Microsoft, Google, GitHub, Telegram, Discord, official WhatsApp API, Home Assistant, MQTT, REST, MCP, webhooks
- D31 **Architecture:** Hybrid modular
- D32 **Frontend:** Python + PyWebView + React/TypeScript
- D33 **Database:** SQLite + Microsoft SQL Server
- D34 **Cloud hosting:** Self-hosted VPS
- D35 **Cloud sync:** Knowledge, memory, history, preferences, workflows, devices, themes; no notification history
- D36 **Offline capabilities:** Local AI, STT, TTS, Windows, clock/timer/alarm/stopwatch, cache, memory, automation, system
- D37 **Performance:** Adaptive resource management
- D38 **Speech engine:** Local TTS (SAPI or local neural model)
- D39 **Installer:** Intelligent setup wizard
- D40 **Updates:** Smart update notification and approved install
- D41 **Backup:** Scheduled, manual, encrypted, export, rollback, recovery, migration, reset
- D42 **Device management:** Universal secure device hub
- D43 **Accounts:** Personal cloud account
- D44 **Logo:** Intelligence Core — owner-approved circular cyan energy core reference
- D45 **Tagline:** Your Personal Digital Intelligence
- D46 **Typography:** Hybrid: Orbitron + Space Grotesk + monospace
- D47 **Character:** Digital wireframe — owner-approved masculine cyan mesh/particle face reference
- D48 **Avatar presentation:** Adaptive head/bust/full-body
- D49 **Animations:** Lip, blink, head, emotion, breathing, audio, particles, scans, transitions, gaze, materialization, sleep
- D50 **Languages:** English, Sinhala, Singlish, Tamil, additional provider-supported languages
- D51 **Addressing:** Personal name selected; actual name not supplied (OPEN)
- D52 **Response behavior:** Adaptive
- D53 **VPS OS:** Ubuntu Linux
- D54 **Vector search:** SQL Server native vector search; feasibility validation required
- D55 **File storage:** VPS filesystem
- D56 **Testing:** Unit, integration, UI, voice, security, performance, offline, recovery, end-to-end, device, regression
- D57 **Development strategy:** Parallel V2 development
- D58 **Development priority:** Foundation first

## Approved visual assets (revision 1.1)
Use the owner-supplied Intelligence Core logo and Digital Wireframe avatar shown in the v1.1 blueprint, pages 1, 5 and 6. Preserve the circular segmented cyan rings, central energy core, CLYDEX wordmark, and the distinctive face and glowing mesh/particles. Do not substitute the previous CX monogram or a generic face. The supplied screenshots are visual references, not production vector/3D assets; screenshot UI controls must not appear in production artwork. Create and validate licensed vector/icon and rigged 3D assets before shipping.

## Delivery phases
0 baseline; 1 foundation; 2 intelligence/memory; 3 voice/personality; 4 cinematic HUD; 5 cloud vault/sync; 6 tools/automation/plugins; 7 release readiness; 8 future devices. Each phase requires tests, documented acceptance and rollback.

## Open items
Preferred name missing; neutral greeting until supplied. VPS sizing/budget, SQL Server version/edition and vector support, local voice quality/language support, actual providers, credential scopes, reference hardware, signing, retention and backup destination require owner/technical validation. Do not silently substitute a technology.

## Required handoff
Summarize what changed, what was tested, failures, untested Windows-specific cases, risks, commands to run, and next bounded implementation task. Never claim an action succeeded without evidence.
