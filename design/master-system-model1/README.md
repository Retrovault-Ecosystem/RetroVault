# Master System Model 1 — concept v1

User-selected appearance: **concept v1 approved**. The user chose the original
with: “Let's stick with the top one, your original sega master system bezel looks great!”
Concept v2 is retained as an unused alternative.

Generated with the built-in image-generation tool. Appearance approval does not
establish a deployed production package, calibrated viewport, or readiness.
The existing Genesis branded design supplied the branding-layout reference only;
no existing production image was modified.

Design direction: independent Master System charcoal/red/silver styling, angular
shell, vent panels and pause/reset details; metallic RetroVault wordmark with
double gold rules on both sides and no legal symbol; platform logo below with ®.
The generated opening remains opaque black. Its proportions and pixel bounds are
not a production specification. Actual content containment and a transparent
aperture require separate package preparation and qualification after approval.
The visual buttons are artwork, not interactive UI controls.

## Generation prompt

Create a NEW review-only Sega Master System Model 1 inspired emulator bezel concept for RetroVault. Use the supplied Genesis bezel ONLY as a reference for the bottom branding hierarchy and metallic RetroVault wordmark with DOUBLE parallel gold rules on BOTH sides. Do NOT retain Genesis design elements, 16-BIT badge, Genesis logo, circular shell or volume slider. New platform identity: angular charcoal-black molded plastic, distinctive Master System red stripe details, subtle silver labels and finely ribbed vent panels, restrained original-console industrial design. Straight-on flat 16:9 landscape composition, no perspective. Large central perfectly rectangular blank solid black gameplay opening, approximately 4:3, all four edges unobstructed; no game imagery or simulated scanlines in the opening. Broad side columns and modest bottom branding band. Bottom center exact text 'RetroVault' in metallic silver with two gold horizontal lines before and two after, NO legal symbol on RetroVault. Below it a Sega Master System logo reading 'SEGA MASTER SYSTEM' with a small registered symbol after the platform logo. Independent Master System red/black/silver style, retain only shared RetroVault gold branding accents. Hardware details outside the gameplay aperture only: small power switch/indicator left and pause/reset buttons right. Premium realistic textured raster artwork, legible clean labels. This is concept artwork for human design review, NOT calibrated production geometry. Preserve transparency outside outer casing if any; black opening remains opaque for this preview.

## Exact runtime cutout candidate

The user approved a scripted alpha-only cutout. Run
`python tools/prepare_master_system_artwork.py` from the repository using its
Pillow-equipped environment. Output: `Master_System_Model1_runtime_cutout.png`.
The adjacent JSON verifies full transparency inside the declared rectangle,
identical pixels outside, identical RGB channels throughout, and the untouched
source hash. This is the preferred technical candidate; the generated
`Master_System_alpha_candidate.png` is not selected. Native canvas remains
1672×941; production display geometry is still unqualified.

## Production disposition — 2026-10-18

The review-stage descriptions above are historical. The deterministic runtime
cutout is now the qualified Master System production artwork. Its normalized
1920×1080 aperture and two-fixture live acceptance are recorded in
[the Milestone #9 record](../../docs/usqe_milestone9_platform_expansion.md).
The approved source and unused alternatives remain preserved.
