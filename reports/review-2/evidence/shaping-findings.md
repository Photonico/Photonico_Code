# Further Claude fix review: shaping

Compared previous built font (`baseline-audit/review-claude/generated/current-built.ttf`) with fresh `generated/current-raw.ttf` and `generated/current-built.ttf` under `/tmp/photonico-review-2/`. Source was immutable `latest.sfd`. No source/release font was modified. HarfBuzz 14.5.0 OpenType and CoreText shapers were used.

## Result

The two important issues from the previous review are fixed in tested cases:

- Overlay marks now use actual GPOS MarkToBase attachment, covering 2203 base glyphs. Both engines produce 1200 advance for `x̶`, `𝔼̶`, `◌̶`, and 2400 for `--̵`; the prior CoreText values were 1392, 1391, 1322 and 2750. Overlay anchor declarations are at source 81282 and 81315.
- Missing anchors on precomposed bases are substantially addressed: `ḁ́`, `ḍ́`/`ḍ́`, `ẍ́` now attach and stack the following acute. Source anchor lines 109895, 110152 and 105192. The 683-letter+circumflex sweep improves from 72 missing-attachment candidates to 5: `Ĳ̂`, `ĳ̂`, `ʹ̂`, `ͺ̂`, `ⁿ̂`. These remaining cases are uncommon ligature/modifier combinations and were already broken previously.

Regression coverage:

- 61 programming samples match previous glyph choices and positions exactly in both new outputs.
- 58 non-aalt GSUB feature tags tested with mixed programming text and all encoded scalars; no unexpected advance remains in this suite.
- 1733 printable non-mark/non-control/non-space scalars followed by U+0336 under 59 settings (default + 58 features): **102247 combinations**, all retain their unmarked text's advance and correctly place overlay at dx=-1200. U+2E3A/U+2E3B intentionally expand to two/three dash cells, so expectations use actual unmarked shaping width rather than assuming every Unicode scalar occupies one cell.
- 493 mapped canonical decomposition pairs remain at 25 glyph-identity differences, unchanged from previous; identity differences alone are not defects.
- Extended probes cover supplementary glyphs, programming ligatures, multiple mark orders, alternate letters and ignored Unicode controls.

## Remaining limitations and edge observations

1. **General mark-on-mark stacking remains incomplete (pre-existing).** `x + circumflex + acute` and `x + circumflex + macron` position both marks at dy=0, so they overlap rather than stack. The upper mkmk lookup accepts marks on only `uni0342`, `uni0308`, `uni030F`; it has no receiving anchor on circumflex. Source `uni0302` at 80949 has mark anchors at 80954–80955 but no basemark anchor. The lower mkmk receiver is only `uni0345`, so multiple below-marks also lack general stacking. This is distinct from the precomposed-base fixes, and identical behavior existed in the previous build. Supported combinations such as q+dieresis+acute do have mkmk positioning.

2. **Five rare base/circumflex combinations remain unanchored**, listed above. IJ/ij source blocks start 6184/11402, Greek ypogegrammeni 29946, superscript n 17766. Greek numeral sign normalizes to modifier prime, so its missing attachment belongs to that normalized glyph. These are coverage notes, not newly introduced regressions.

3. **Artificial ZWJ boundary edge case changed.** `x + U+200D + U+0335` now leaves the overlay at dx=0 (one cell to the right), whereas the prior unconditional SinglePos happened to place it on x. Other anchored accents, e.g. `x + U+200D + acute`, already behave this way, and CoreText returns missing glyphs for that artificial sequence in both versions. This was not found in ordinary base+mark, programming or optional-feature samples. If explicit ZWJ-in-Latin combining support is a requirement, it needs separate handling; do not undo the correct mark attachment fix to preserve the old accidental behavior.

4. Isolated U+0336 without a base still receives a 60-unit CoreText heuristic shift; it was already present and should not be conflated with supported base+overlay text, whose alignment now passes.

No new issue was found in ordinary programming text or supported base+overlay samples. This review does not claim exhaustive Unicode mark stacking or native Windows/Linux application validation.

## Reproducible evidence

- `audit_shaping.py`, `shaping_results.json`: baseline/raw/built comparison.
- `probe_extended.py`, `extended_results.json`: 683-base sweep and 33 extended samples in both engines.
- `probe_overlay_features.py`, `overlay_feature_results.json`: 102247 scalar/feature/overlay combinations, zero exceptions.
- `stacking_and_control_probes.json`: explicit old/new stacking and ZWJ observations.
