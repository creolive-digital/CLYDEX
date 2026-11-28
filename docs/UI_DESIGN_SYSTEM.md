# CLYDEX HUD design system

## Phase 06 additions (2026-11-28)

The original SVG graph uses the existing Cyber Cyan panels, typography, focus states, controls and review dialogs. Nodes expose keyboard/drag positioning and labeled connection/parameter controls. Nine operating views reuse the existing navigation, emergency Stop/mute and native approval restoration. Literal untrusted tool/MCP content never becomes HTML. Source/credential settings remain reviewable; stored credentials are not displayed. Responsive overflow and real WebView2 screenshots are recorded in PHASE_06_COMPLETION_REPORT; optional capture previews are explicitly RAM-only and do not imply OCR/lip-sync/avatar acceptance.

## Phase 05 additions (2026-11-28)

Cloud, Knowledge Vault, Devices and Synchronization reuse the Cyber Cyan panels, hybrid fonts, existing icons, review dialogs and persistent Stop/mute controls. New source/citation, file, quota, structured-data and device rows preserve keyboard labels and literal text rendering. Navigation scrolls vertically at smaller heights; no external CDN, replacement logo, avatar face or new renderer is introduced. Native 1360/760-pixel screenshots and component evidence are in the Phase 05 report; production avatar and acoustic acceptance are unchanged.

Cyber Cyan remains the default identity. The owner-supplied Intelligence Core logo and Digital Wireframe masculine face are preserved byte-for-byte. The UI does not invent an alternative logo, face, personal name, live task, provider status or system metric. The avatar is explicitly labeled as an approved reference with a production rig pending.

## Tokens and composition

`frontend/src/styles/tokens.css` defines dark background `#060c14`, panel `#0c1722`, raised panel `#102432`, primary text `#e1edf3`, secondary text `#93a9b8`, accent `#00d9ff`, borders, 12 px panel radius, 22 px spacing and 160/500 ms motion durations. `app.css` composes the navigation rail, top status bar, central presence/chat split, emergency dock, forms, dialogs and compact displays. Common Panel, Field, Toggle, ReviewButton, ErrorNotice, Dialog and icon controls maintain consistent behavior.

Orbitron is used sparingly for cinematic identity/state display, Space Grotesk for readable UI, and installed Consolas/Cascadia Mono for technical data and exact arguments. Orbitron is bundled with its SIL Open Font License from the official Google Fonts repository; the existing Space Grotesk and its OFL are reused. Lucide icons are bundled by the frontend with their ISC license. React and Three.js notices accompany the production bundle. No external font service is used. Sinhala/Tamil rendering relies on installed system fallback fonts; actual multilingual typography review remains an owner acceptance gate.

Three themes (Cyber, Midnight, Graphite) and reviewed custom RGB accents share the same identity. Foreground accent colors are lightened as needed to maintain at least 4.5:1 against the default raised panel; decorative glow retains the chosen color. Unit checks cover dark and saturated custom colors. Full theme-wide human contrast/accessibility certification is still required. Critical states always include text/icons, rather than color alone.

## Interaction and motion

Settings and sensitive operations use the existing exact review; the redesigned dialog shows action, target/destination, consequences, expiry, digest and an expanded literal snapshot. Cancel receives initial focus, Escape cancels, and Approve once sends only the current ID. Expired approval is disabled. Native modal focus containment is used. Inputs have linked labels and separate hint descriptions; buttons have visible focus outlines and icon-only controls have accessible names. Chat treats model/tool text as literal text and preserves full answers separately from concise speech.

Navigation and forms remain keyboard-operable. Layouts collapse at 1150/950/760 px; narrow standard windows scroll vertically, and compact modes use dedicated layouts. Smart Widget and mini/floating presentations preserve voice and emergency controls. The native title bar remains available for standard resizing; the Floating Hologram is an on-top framed window, not an unverified transparent desktop compositor.

Idle/sleep, focus/gaming and resource saving constrain the WebGL field; hidden/minimized presentation suspends it. Users can select 15/30/60 frame-rate caps, particle count, low/balanced/high detail, animation disable and reduced motion. OS reduced-motion preference is honored. CSS materialization, scan, breathing/drift and orbit effects stop when motion is disabled. Motion describes the reference presentation and surroundings; there is no fabricated blinking, articulated head animation or accurate facial phoneme motion.

## Screens and evidence

Overview combines true voice state, approved reference, temporary chat, route information, consent status and sampled OS counters. Conversation includes histories; Intelligence configures seven providers and routing profiles; Memory exposes explicit local consent/review; Voice exposes devices/models/languages/activation; Personality exposes nine existing profiles; Settings covers presentation/permissions; Notifications contains actual generic local events. No future module is advertised as working.

Actual native client-area images are in `docs/evidence/phase04/` after verification. They show a disposable local profile, with microphone disabled/muted and no inference. Their window dimensions describe native outer sizes; client areas are slightly smaller due to title bars/borders. The screenshots establish developed visual output, not acoustic quality, final artwork rights clearance, native screen-reader certification or full production acceptance.
