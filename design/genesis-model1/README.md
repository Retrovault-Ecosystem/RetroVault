# Genesis Model 1 visual design

User-requested extension to Milestone #6. Generated with the built-in imagegen tool;
reference NES/SNES images were used for overall layout only. The design uses black
Genesis Model 1 casing, graphite ribs, gold accents, a red power light, and bottom
RetroVault / Sega Genesis branding. Nintendo branding was subsequently refined as documented in ../branding-review/.

`Genesis_Model1_generated.png` is the unmodified generated source (1672×941 RGBA).
It is a design source, not yet a deployment-ready overlay. Its center alpha has
irregularities and its resolution differs from the production 1920×1080 canvas.
This immutable source is preserved for provenance. The production asset is built from
Genesis_Model1_branded.png using tools/generate_genesis_classic_artwork.py; its exact
aperture is X312 Y80 W1296 H770 on the 1920×1080 canvas.

## Generation prompt

Create a finished production raster bezel/overlay for RetroVault's Sega Genesis emulator platform, inspired by the original North American Sega Genesis Model 1 console. This is a NEW design, not a recolor of Nintendo. Use the two attached NES/SNES images ONLY as layout references: physical hardware surround, huge unobstructed rectangular game opening, and RetroVault plus platform logo stacked at bottom center. Do NOT reuse their gray/ivory/purple Nintendo palette or their hardware panel shapes. Genesis palette: deep black textured ABS plastic, dark graphite, restrained antique-gold 16-BIT accent and thin gold rim, white/silver branding, tiny red power indicator. Strong recognizable original Genesis Model 1 industrial character: ribbed ventilation, curved cartridge-deck-inspired molded arcs contained in the side panels, on/off slider, pale gray RESET button, subtle headphone volume slider. No extra slogans. Put tasteful small gold '16-BIT' at upper right of the outer casing. Bottom center: clearly legible RetroVault wordmark above an authentic-looking white SEGA GENESIS logo; keep both wholly outside the game aperture. Distinctive elegant realistic molded black console housing, polished restrained studio lighting, front-facing orthographic composition, symmetrical game opening, no tilt, no perspective distortion. Canvas exactly 1920x1080, 16:9. The viewport hole is exactly the rectangle x=330,y=70,width=1260,height=810, with straight square inner edges. This entire rectangle must be fully transparent, not black, not checkerboard painted, no glass, no gradient, no reflection, no game scene, no shadow inside. The surrounding bezel must be fully opaque and fill the canvas edge-to-edge, including corners. Subtle beveled lip OUTSIDE the aperture only. Leave bottom band y=910..1080 for logos and controls. Maintain generous game area. This must be an actual PNG with transparent alpha in the center opening, ready for overlay compositing.

## Branding refinement — 2026-09-29

`Genesis_Model1_branded.png` adds paired gold rules on both sides of RetroVault and
® after the Genesis logo, using the user-authorized localized Pillow cleanup.
The generated source above remains untouched. See `../branding-review/` for the
reproduction script, comparison preview and pixel-preservation evidence. Production
normalization, manifest alignment and deployment are complete; the user approved the
final design for integration and closure. Runtime evidence is recorded in
docs/milestone6_visual_qualification.md.
The branded revision also removes the generated ™ after RetroVault at the user's
request; the Genesis ® remains. The immutable generated source is archival only.
