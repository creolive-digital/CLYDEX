# Digital Wireframe renderer and asset gate

## Supplied assets

Both expected reference PNGs exist at intake. They were owner-provided untracked files and remain unchanged:

| File | Bytes | SHA-256 |
|---|---:|---|
| `assets/branding/clydex_logo_reference.png` | 10,181 | `e49d7bdda1b73b24ce74c67e0e63be5f8a0e0e1735f7ce4b66757ef027c3754f` |
| `assets/avatars/clydex_avatar_reference.png` | 183,369 | `c9e20e5b061fc50c1cbf3fdf851f15ca6fcea9a008552ee7f0cf596685fc0d5f` |

Owner authorization supplies their project reference provenance, not evidence of third-party copyright ownership or a production model license. The avatar PNG contains screenshot corner controls; the presentation uses a CSS ellipse/vignette to hide those margins, without editing the file or substituting a face. Full production artwork/redistribution provenance and a matching rigged model remain owner deliverables. No model, texture pack, alternate character or generated image was downloaded.

## Implemented rendering

`features/avatar/Avatar.tsx` presents the exact face with state classes; `renderer.ts` defines AvatarSignal/AvatarRenderer and the Three.js HologramField. This WebGL scene draws surrounding point particles and a holographic floor ring. CSS supplies scan lines, subtle whole-reference drift, glow, materialization, sleep/wake presentation and explicit state labels. Standby, wake detected, listening, transcribing, thinking, waiting for approval, speaking, interrupted, sleeping and error come from the real voice snapshot. Synthetic UI fixtures live only in tests.

Actual PCM amplitude, frequency bands and waveform from Studio/Phase 03 drive the field/envelope/spectrum. No background oscillation is labeled measured audio. A silent buffer renders zero measured energy. The collector preserves observed playback sample rate, final frames played and completion; the renderer interface and caption expose those counters. They are emitted at real playback start/stop, not interpolated as continuous phoneme timing. No phoneme/viseme timings are currently produced. The envelope beneath the face is an energy indicator, not an animated mouth or precise lip sync. The static eyes do not blink and the face is not articulated. Full-body humanoid animation, eye/head/jaw rigging, expression and viseme animation are explicitly pending a suitable approved model.

Three loads lazily. The scene caps geometry to 500 points; detail bounds pixel ratio; configured FPS caps actual rendering, rather than claiming achieved performance. Idle/sleep, focus/gaming/resource saving reduce rate/particles; hidden/minimized/tray and disabled/reduced motion stop continuous rendering. Navigation unmount cancels RAF, disconnects ResizeObserver and visibility listeners, disposes geometry/materials/renderer and loses the owned context. Context loss preserves the approved image, explicit fallback label and operational controls. This follows [Three.js resource cleanup guidance](https://threejs.org/manual/pages/cleanup.html).

## Evaluated production routes (official documentation checked 2026-11-27)

| Route | Licensing / engineering assessment | Selection status |
|---|---|---|
| Original owner-commissioned glTF/GLB face/body/rig matching this reference | Require explicit source/artwork/redistribution rights, documented morph/bone names, neutral topology, idle/blink clips and optional visemes. Three.js can consume a web-optimized export; target budgets must be measured on this workstation. | Preferred engineering route; no commissioned asset or approval inferred. |
| MakeHuman / MPFB core assets | [Official license](https://www.makehumancommunity.org/about/license.html) separates software licensing from CC0 core assets. Community extras must be checked individually. A generated generic face would still violate the confirmed identity without owner approval and artist adaptation. | Possible licensed base only; not downloaded, fitted or validated. |
| MetaHuman | [Official current licensing page](https://www.metahuman.com/license?lang=en-US) permits use with other engines under applicable Unreal terms; revenue/seat conditions require owner assessment. Export, web optimization, performance and preserving this specific face are additional work. | Evaluated, not selected; no account, paid dependency or asset download. |

No generic third-party face is silently substituted. The current reference path is the user-authorized fallback and is visually labeled. Before a production rig can be accepted, the owner must approve identity match and rights, provide optimized model/rig/animations and approve any asset download. Then verify actual GPU memory, FPS, WebGL fallback, loading/disposal, audio frame alignment, expression quality and installed-language typography. Precise lip sync additionally needs actual phoneme/viseme timing with a documented timebase, not estimated text mouth shapes.
