# Platform branding refinement — 2026-09-29

Localized Pillow edits authorized by the user's response to the production-cleanup
request. Original generated Genesis source is preserved in `../genesis-model1/`;
pre-edit NES/SNES rasters are preserved in `before/`. Run
`.venv/bin/python design/branding-review/refine_branding.py` from the repository root
to reproduce the edits and comparison preview.

- NES: two red rules on each side of RetroVault; existing Nintendo registered mark retained.
- SNES: existing double purple rules preserved exactly; bottom platform TM replaced with ®.
- Genesis: two gold rules on each side of RetroVault; registered mark added after Genesis.

Nintendo's original SNES documentation identifies Nintendo and Super Nintendo
Entertainment System as registered trademarks:
https://www.nintendo.co.jp/clvs/manuals/common/pdf/CLV-P-SABTE.pdf

`verification.json` records output hashes and changed pixel bounds. Assertions check
that all original alpha values and all pixels outside the edited branding regions
are identical. These checks do not imply new live visual acceptance.

NES/SNES repository package images are updated, including the SNES image hash.
Genesis's revised design is `../genesis-model1/Genesis_Model1_branded.png`.
The user approved the final designs for integration and milestone closure. All three
packages are deployed through NativeVisualDeploymentService, with byte verification
and backups in build/milestone6/before-approved-bezels. Genesis production normalization
and manifest alignment are complete. See docs/milestone6_visual_qualification.md.

Follow-up: removed the generated RetroVault ® on SNES and ™ on Genesis.
NES RetroVault already had no legal symbol. Platform marks and paired rules are
preserved. The script reproduces these removals and refreshes the SNES image hash.
