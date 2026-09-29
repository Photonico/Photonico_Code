# Claude change review: shaping

> 历史检查快照：结论与源码行号对应当时的字体版本。报告已从 `audit/` 迁移；旧复现命令与未单独展开的中间文件完整保存在[原始证据压缩包](../../archive/font-audit-2026-09-29.zip)，解压后可还原原目录。最新结论请看 reports 的总索引。


Inputs: pre-change `audit/generated/Photonico-current.ttf`; new direct FontForge output `audit/review-claude/generated/current-raw.ttf`; new build-script output `current-built.ttf`. No source or release font was modified by this audit.

## Confirmed successful changes

- Both new outputs now attach grave/caron and the four previously spaced combining marks correctly in HarfBuzz OpenType shaping. `x̀`, `x̌`, `x̣`, `x̥`, `x̵`, `x̶` each consume exactly 1200.
- New base anchors fix the important `r̂`, `Λ̂`, `ϕ̂`, `œ̂` cases. `r̂` mark offset is -1135 rather than 0; the 65-unit difference from -1200 reflects the new anchor's x=665. `ss01` r and tested `cv01` a / `cv03`–`cv06` i variants retain working attachment.
- `<$>` now consumes 3600; `$>` consumes 2400; `ss04` dollar now has 1200 advance. In 61 programming samples the only shaping differences from baseline were those intended dollar widths. No unexpected new glyph substitutions were observed.
- Tested all 58 non-`aalt` GSUB feature tags using both a mixed programming corpus and one encoded scalar per line. No non-grid advance remained in those feature tests.
- The same 493 canonical decomposition pairs were examined before/after; the number of glyph-identity differences remains 25. Differences in glyph identities alone are not counted as errors.

## Remaining issue 1: overlay fix is not sufficient for macOS CoreText

The new `mark` lookup is a SinglePos adjustment (source line 468), with `dx=-1200` on `uni0335`/`uni0336` (79707 and 79741). It fixes HarfBuzz placement but does not provide mark-to-base attachment that suppresses CoreText's own fallback positioning.

Reproduction:

```sh
/opt/homebrew/bin/hb-shape audit/review-claude/generated/current-built.ttf 'x̶x' --shapers=ot --output-format=json
/opt/homebrew/bin/hb-shape audit/review-claude/generated/current-built.ttf 'x̶x' --shapers=coretext --output-format=json
```

OpenType total advance is 2400. CoreText is **2592**, and the second x begins at 1392 instead of 1200. U+0335 alone after x happens to retain width but is vertically repositioned; other contexts also drift: `--̵` is 2750 instead of 2400, `𝔼̶` is 1391 instead of 1200. Both raw and built outputs behave this way. The same issue existed in baseline, so this is an **incomplete repair, not a newly introduced regression**.

All six single-mark `x + mark + x` sequences were compared between engines. CoreText now gets U+0300, U+030C, U+0323, U+0325 and U+0335 advances right; U+0336 remains 2592. `x + U+0335 + U+0336 + x` and reversed overlay order are also 2592. Adding an anchored circumflex or dot-below happens to suppress the fallback and returns 2400; this context dependence reinforces the need for attachment rather than a fixed positioning delta. Results: `mark_engine_comparison.json`.

A **diagnostic-only** copy with a minimal proper GPOS Type4 MarkToBase lookup fixes all these samples in both engines. File: `diagnostic-overlay-markbase.ttf`; generator: `probe_overlay_attachment.py`; measurements: `diagnostic-overlay-markbase.json`. This file intentionally replaces the rest of GPOS and must not be distributed. The independent metadata audit also loaded it directly with native CoreText: `x̶x` total2400, x positions0/1200, mark position0. Native evidence is in `../metadata/coretext_diagnostic.txt`.

Suggested repair: create a dedicated overlay anchor class, attach both overlay glyphs to each relevant base/alternate/ligature cell, preserving the selected overlay y coordinate. Then regenerate through the supported build and recheck native CoreText as well as HarfBuzz. Do not simply widen cells or trust zero hmtx advance as proof of actual run alignment.

## Remaining issue 2: composed base glyphs still lose following accents

The Latin/Greek letter + circumflex sweep improved from **108 to 72 missing-attachment sequences out of 683**. These counts include uncommon combinations, so they are coverage diagnostics rather than 72 equally serious bugs.

Concrete remaining examples:

- `ḁ́` (a + ring below + acute) normalizes to `uni1E01` + `acutecomb`; acute dx=0, drawn in the following cell. Source `uni1E01` begins at107774.
- `ḍ́` and decomposed `ḍ́` both normalize to `uni1E0D` + `acutecomb`; acute dx=0. Source `uni1E0D` begins at108018.
- `ẍ́` normalizes to `uni1E8D` + `acutecomb`; same defect. Source `uni1E8D` begins at103245.

These precomposed base glyphs have no anchors. Adding anchors to plain d/x/a does not address them because shaping retains the precomposed glyph. They also existed before these edits. Results: `extended_results.json` -> `missing_attachment` / `extended_probes`.

More generally, multiple upper/lower marks do not have complete stacking support; e.g. x + circumflex + acute places both at the same dy. This is an existing coverage/design limitation, not a regression from the new patches. New overlay tests with supplementary glyphs, ignored Unicode characters, alternate glyphs and multiple mark orders did not reveal an additional HarfBuzz width regression.

## Artifacts

- `audit_shaping.py` / `shaping_results.json`: main three-font regression audit.
- `probe_extended.py` / `extended_results.json`: 683-letter sweep, 33 extended samples, feature variants and CoreText comparison.
- `changed_positioning.json`: source field changes for84 glyphs.
- `mark_engine_comparison.json`: focused old/new combining mark checks in OpenType/CoreText.
- `probe_overlay_attachment.py`: small diagnostic demonstrating the attachment fix direction.
