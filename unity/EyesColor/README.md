# EyesColor variants — re-baked in stage20

60 files: 5 eye expressions × 6 colors (Brown, Blue, Amber, Violet, Gray,
Red) × 2 sexes. File names match the Unity package:
`EyesColor_<EyesName>_<ColorName>.png`, one folder per sex (Female / Male).

Baked from the base `Eyes_*` layers with the Linux motor's `_ojos_tinte`
(`version-linux/motor.py`), which in stage20 also tints the iris's warm
lower disc and its grayish rim (fix D) — before stage20 those stayed amber
with any requested color. The green part of the iris is byte-identical to
the previous variants; only the disc and rim changed.

Apply to the Unity package in Google Drive (Textures/Female and
Textures/Male) ONLY when Stiven orders the Unity update, replacing the
files by Drive ID, without touching any `.meta` files.
