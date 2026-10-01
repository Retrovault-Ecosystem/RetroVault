# RVA1-C.17-B / A.4-C.8 — viewport authority repair

Status: automated validation complete; gameplay requalification pending.
Do not commit or push until live qualification passes.

Protected branch: `feature/rvdb-foundation`.
Protected HEAD: `a1b472317d0a4d18626eea0dc4b75d8a389c912f`.

## Current user requirement

Use the existing glass and bezel artwork. Preserve each game's intended display
proportions, show the complete source image, and keep it centered within the glass.
No horizontal/vertical stretching, clipping, or off-screen displacement.
Different image/glass aspects necessarily leave unused space.

The intermediate full-glass FILL candidate was superseded by the user's explicit
no-stretching requirement. Its enum, geometry branch, and NES manifest declaration
have been removed. The original aperture manifests and overlay images/descriptors
for NES, SNES, and Genesis are byte-identical to the protected HEAD.

The pre-existing uncommitted loaded-core-aspect change in `launcher.py` and its
regression test were preserved. Canonical production launches probe loaded content
even when the launch profile supplies an aspect hint; valid runtime aspect takes
precedence before proportional CONTAIN is calculated.

## Diagnosed causes and repair

1. RetroArch 1.22.2 (`69a4f0ea1e`) replaces repeated `--appendconfig` options.
   Both probe and visible launch now pass a single pipe-delimited ordered list.
   Visible order is session, overlay, optional cheats, final CONTAIN. This restores
   the session's core-options path instead of silently dropping it.
2. RetroArch adds viewport bias to custom coordinates. CONTAIN already computes
   absolute top-left positions; final X/Y biases are now zero to avoid a second
   translation.
3. The restored session baseline disables shaders. `--set-shader` selects a preset
   but does not enable the pipeline, so session generation explicitly enables it
   only when the launcher selects a shader.
4. Mega Bezel Auto aspect mode can independently refit the image. NES and SNES
   presets now select `HSM_ASPECT_RATIO_MODE = 6`, which uses FinalViewportSize
   with screen scale (1,1). The aspect-correct RetroArch viewport owns geometry;
   the shader adds CRT treatment without a second aspect fit. Genesis already
   uses a direct shader. Crop percentages remain zero.

Sources checked against the installed binary:

- [RetroArch CLI parser](https://github.com/libretro/RetroArch/blob/69a4f0ea1e/retroarch.c): `RA_OPT_APPENDCONFIG`, `RA_OPT_SET_SHADER`, pipe-delimited list.
- [RetroArch viewport implementation](https://github.com/libretro/RetroArch/blob/69a4f0ea1e/gfx/video_driver.c): `video_viewport_get_scaled_aspect2`.
- Installed Mega Bezel `shaders/base/cache-info.inc`: mode 6 uses the final viewport
  aspect and returns a screen scale of (1,1).

The installed NES manifest and NES/SNES presets match their repository source.
Deployment backups are in `build/a4c8/before-proportional-fit/` and
`build/a4c8/before-full-glass/`. Persistent RetroArch global configs are not edited.

## Scope of the shared fitting rule

The existing classes remain classic 4:3, widescreen 16:9, horizontal/vertical
arcade, handheld-native, dual-screen, and specialized. Proportional fitting is
independent of game name, platform name, and source raster identity. Regression
fixtures exercise 4:3, 8:7, 16:9, 3:2, 10:9, and vertical ratios, including 4:3 and
16:9 inputs sharing the same profile. Each result stays inside its own envelope,
is centered to within one pixel, and preserves aspect to pixel-rounding precision.

This does not qualify every platform or invent handheld/dual-screen apertures.
Only existing READY platforms have production packages. The visible launcher still
uses the aspect acquired at startup; automatic live viewport updates after later
in-game aspect changes are not claimed by this repair. Universal platform coverage
requires separate core/package/runtime qualification.

## Renderer evidence

Local diagnostic files are under `build/a4c8/` (Git-ignored). The GL trace records
actual viewport calls and captures the full EGL framebuffer before swap. Bounded
runs use isolated config/save paths and exit automatically. They are not human
qualification.

At 1920x1080, an identical 995x762 bias A/B measured:

| Case | GL rectangle (bottom-left origin) | Screen rectangle (top-left origin) |
| --- | --- | --- |
| Old 0.5 biases | 922,59,995,762 | 922,259,995,762 |
| Zero biases | 460,218,995,762 | 460,100,995,762 |

With the session/core options restored, NES reports 256x240 / aspect 1.219.
The current proportional viewport is 929x762 at (493,100), confirmed by actual
GL `(493,218,929,762)`. The game surface fills the glass height; side margins are
138 and 139 pixels. The CRT shader follows that viewport and the capture includes
all 1943 title/menu/copyright text.

Current NES evidence: `nes-proportional-evidence.json`, `nes-proportional.log`,
`nes-proportional-stderr.log`, `nes-proportional.frame.png`.
Current SNES evidence uses the corresponding `snes-proportional` prefix. SNES
reports aspect 1.333 and uses 1044x783 at (438,71), matching its existing glass.
Both final bounded NES/SNES runs exited 0 with CRT shaders active.
Earlier `1943-full-glass` evidence documents the superseded stretching candidate.

## Automated validation

- Final full suite: 1,833 passed in 38.25 seconds.
- Focused profile/glass/shader regressions: 42 passed.
- `git diff --check`: passed.
- Existing NES/SNES/Genesis glass/artwork/overlay descriptors: unchanged.
- HEAD/branch unchanged; nothing committed or pushed.

## Gameplay gate

Use a fresh RetroVault process. Test actual gameplay in 1943, Adventure Island,
and The Addams Family, checking all four edges/HUD, proportions, centering, and
scrolling. Also recheck SNES after removing its secondary shader aspect fit.
Exit/relaunch normally to check session isolation. Unused space where aspect ratios
differ and game-authored black pixels are expected; do not crop them automatically.

Keep all edits uncommitted until the user accepts the live result.


## Platform-specific adaptive opening — latest candidate

The user clarified that each platform must have its own bezel/opening, fitted to
its games without stretching, cropping, or misalignment. This supersedes the
fixed-opening/unused-margin acceptance above. Existing evidence remains historical.

NES now opts into `adaptive_frame` in its production manifest. Its maximum
aperture is still 355,100,1206,762, but the runtime opening is the proportional
viewport. `AdaptiveBezelRuntime` renders the original inner rim at that opening,
using package-declared housing material outside it. Outer controls, branding,
and artwork outside the declared frame rectangle remain unchanged. No game pixels
are passed through this artwork renderer. Generated PNG/overlay descriptors are
session-owned and removed on exit/failure, together with other launch artifacts.
Only NES opts in; no other platform borrows its art or frame geometry.

The original overlay remains available during aspect acquisition. The final
visible overlay is generated afterward and replaces that launch layer. The
last custom viewport and the opening use the same `contain_aspect` result.
The original shader descriptor remains selected, retaining the neutral CRT fit.
No title-name, ROM-name, or raster-specific geometry exceptions were added.

Regression coverage checks every pixel of the aperture for six aspect ratios:
transparent exactly inside the viewport, opaque everywhere else in the former
opening. It also verifies unchanged outer artwork, cleanup, invalid frame bounds,
opt-out packages, and the probe-to-visible-launch overlay replacement.

The NES manifest was installed with the previous version backed up at
`build/a4c8/before-adaptive-frame/`. The source PNG is unchanged. This remains a
1920x1080 startup-aspect candidate; mid-game geometry changes and other platforms
are not qualified. Game-authored black pixels remain part of the uncropped frame.

Final witness prefix: `build/a4c8/nes-adaptive-final`. Human gameplay gate remains
1943, Adventure Island, and The Addams Family: inspect all four edges and HUD,
proportions, scrolling, then exit/relaunch to check isolation. No commit or push
until that gate passes.

Latest validation: **1,841 passed in 43.13 seconds**. Final bounded RetroArch run exited 0; GL viewport `(493,218,929,762)` corresponds to top-left `(493,100,929,762)`, matching the generated opening. Final screenshot: `build/a4c8/nes-adaptive-final.frame.png`.

## Human NES acceptance and SNES follow-up

The user reported **"All check out ok!"** after the requested NES gameplay
checks in 1943, Adventure Island, and The Addams Family. The NES gate is passed
for that tested scope; this does not qualify every platform or aspect transition.
On 2026-09-28 the user separately reported a black vertical gap outside the right
gray SNES panel and requested that it meet the rim like the left panel.

### SNES right panel fill candidate (2026-09-28)

The user explicitly authorized a deterministic pixel repair and reserved visual
acceptance: "yes, but I will confirm or reject the fill."
The approved left panel edge at (287,71), 9x783, was mirrored into the right
panel gap at (1624,71), 9x783. Pixel comparison proves every pixel outside that
rectangle is unchanged; the entire alpha channel and gameplay opening are also
unchanged. The PNG hash in the manifest is updated. No viewport/shader/code change
was needed for this repair. Original repository and installed files are backed
up under `build/a4c8/before-snes-gap-fill/`.

SNES production asset/specification checks: 22 passed. The deployed candidate is
awaiting the user's visual approval and must not be described as accepted.
Render witness prefix: `build/a4c8/snes-gap-fill`.

### SNES exact mirrored panel revision

The user requested a more exact match to the left side after reviewing the narrow
fill. The complete left panel and adjacent rim at (278,58), 160x810, are now
mirrored into (1482,58), 160x810. Byte comparison verifies exact mirrored RGBA
identity across this entire region. This includes the upper rim's alpha shading;
the gameplay rectangle (438,71), 1044x783, is byte-identical to its previous state.
Every pixel outside the repair rectangle is unchanged. The narrow-fill candidate
is backed up at `build/a4c8/before-snes-panel-mirror/`; the original remains in
`before-snes-gap-fill/`. This revision supersedes the narrow fill and awaits user
visual acceptance. Witness prefix: `build/a4c8/snes-panel-mirror`.

SNES mirrored-panel visual acceptance: the user answered **"yes"** to the final
preview on 2026-09-28. The bezel repair is accepted. Its 22 asset/specification
checks passed and the bounded RetroArch witness exited 0. This acceptance covers
the mirrored bezel appearance, not broader SNES aspect-transition qualification.
Nothing committed or pushed.

## Launch bezel flash repair

The preliminary content-loaded aspect probe inherited the full presentation and
briefly opened RetroArch before the actual launch. It now appends a final,
probe-only config with null video/audio/input drivers, no shader/overlay, no
fullscreen, and isolated saves/history. Core/content and the production core
options are preserved. The shader CLI option is omitted for the headless probe.
The final visible launch and accepted artwork are unchanged. Probe cleanup now
also removes RetroArch-created save subdirectories.

Real core checks with deliberately unavailable Wayland/X display endpoints
succeeded: NES 1.219, SNES 1.333, Genesis 1.524. Evidence is under
`build/a4c8/headless-proof/`. These runs report the null display server.
Full regression suite: 1,841 passed in 41.76 seconds; final cleanup changes also
receive focused probe/launcher/lifecycle checks. Visible NES witness prefix:
`build/a4c8/nes-headless-launch`. User confirmation of the launch transition is
pending; no commit or push.


## Milestone #5 acceptance update — 2026-09-29

The earlier pending launch-transition acceptance is now closed for the observed NES/SNES/Genesis qualification fixtures. The user explicitly accepted NES/SNES presentation and startup transitions for all three systems. Genesis inversion and upper-right placement were corrected by restoring the standard RetroArch MVP shader transform, then visually confirmed by the user. See [Milestone #5 qualification](milestone5_runtime_qualification.md) for runtime evidence and scope limits. Historical pending statements above describe the earlier checkpoint.
