# Review of Claude changes: metadata, build and native macOS (2026-09-29)

> 历史检查快照：结论与源码行号对应当时的字体版本。报告已从 `audit/` 迁移；旧复现命令与未单独展开的中间文件完整保存在[原始证据压缩包](../../archive/font-audit-2026-09-29.zip)，解压后可还原原目录。最新结论请看 reports 的总索引。


Primary source: current modified `00_Regular.sfd`. Baseline: prior unchanged export `audit/generated/Photonico-current.ttf`. Review exports: `audit/review-claude/generated/current-raw.ttf` (FontForge direct) and `current-built.ttf` (`scripts/build.py` pipeline). No source or release file was edited in this review. Existing audit outputs were preserved.

## Outstanding material finding

**The long combining overlay still breaks the monospaced grid on native macOS CoreText.** In the newly built font, `x + U+0336 + x` measures 2592 font units; the second x begins at 1392, rather than total 2400 / second x at 1200. HarfBuzz's normal OpenType backend gives the expected 2400. This is a persistent issue, not a new regression introduced by Claude. Source's new Overlay Marks GPOS single-position lookup does not resolve native CoreText attachment.

Evidence: `coretext_built_only.txt`, `shape_coretext.swift`, `coretext_overlay.png`. The test loads the specific font with CGFont and CTFontCreateWithGraphicsFont. The attributed string sets only kCTFontAttributeName; no language, tracking, or feature overrides. Measuring at font size 1950 (the font's UPM) makes reported dimensions equal to font units. Built-font-only execution in a fresh process reproduces the same result. The PNG uses the same native CTLine renderer at 96 px and vertical guides at 1200-unit cell boundaries. U+0336 visibly shifts the second x; short overlay, dot below and ring below samples align.

The shaping audit's diagnostic `diagnostic-overlay-markbase.ttf` uses an actual GPOS Type 4 MarkToBase attachment. Independent native CoreText testing produces total 2400 / second x at 1200 for x̶x (`coretext_diagnostic.txt`). This supports the repair direction. That diagnostic replaces other GPOS data and is not a release candidate.

## Build-path caveat

The SFD cannot currently be exported directly and assumed to have the same advances as the script-built TTF. This is confirmed behavior, matching the explanation in `scripts/build.py`:

- Current SFD has 25 explicit zero-advance glyphs; FontForge adds one extra zero-advance glyph.
- Direct export has **25 mismatches**: the explicit zero-advance combining marks, U+200B and U+FEFF become width 1200. Raw width counts are 2229 at 1200 and one at 0.
- `scripts/build.py` restores source widths successfully. Built counts are 2204 at 1200 and 26 at 0. Every SFD glyph's advance matches the built font.
- Normal HarfBuzz and CoreText shaping automatically suppress/reassign advances for many marks and default ignorables, so ordinary text examples can conceal the raw hmtx mismatch. Do not claim that all 25 characters visibly fail in every app.
- The raw export is unhinted; the script-built output has new ttfautohint instructions. Release/distribution therefore depends on the script pipeline.

Evidence: `source_output_comparison.json` lists every glyph mismatch. `scripts/build.py` lines 78–84 perform the needed repair before ttfautohint.

## Verified fixes

- **Monospace classification fixed:** both raw and built post.isFixedPitch=1, PANOSE family=2/proportion=9. Native CoreText now reports traits=1024, monoSpace=true (baseline false). Fontconfig still recognizes spacing=100. See `coretext_scan.txt`.
- **Version consistency fixed:** source/raw head.fontRevision≈1.6; name ID 5 is Version 1.6_alpha; built name ID 5 adds the normal ttfautohint(v1.8.4) suffix. Unique ID contains 1.6_alpha. This is coherent and not the previous stale-1.4 problem.
- **Cyrillic false codepage bits removed:** no excess bits against the FontTools-derived codepage set.
- **Ç double USE_MY_METRICS fixed:** no composite in either new output has multiple component metric-owner flags.
- **Four combining glyph classifications fixed:** U+0323/U+0325/U+0335/U+0336 are GDEF class 3, and built advance zero. Current HarfBuzz x+mark+x examples occupy 2400 units. Native CoreText dot/ring examples also occupy 2400. The long overlay attachment issue above remains.
- **Hinting pipeline works:** baseline 0 hinted glyphs; raw 0 and no fpgm/prep; built 1627/2230 glyphs carry instructions, fpgm=3596 bytes/prep=203 bytes. Composite and blank glyphs need not all have independent instructions. Raw gasp=10 (smoothing), built gasp=15 (grid fit+smoothing), consistent with their unhinted/hinted status. No Windows rendering result is implied.
- **Binary integrity remains good:** all tables decode; correct table/whole-font checksums; all glyphs can be drawn; recomputed maxp fields match exactly; cmap coverage remains 1784 mappings, glyph count 2230.

## Remaining minor metadata issue

142 glyphs still have LSB differing from stored xMin by one unit, while head.flags bit 1 claims equality. Raw flags=11; built flags=15; fontTools recomputation clears this bit (to 9 / 13). This was already present before Claude's edits and is low impact; no visible defect is inferred from it.

## Build implementation review

The script was read before execution. It writes temporary artifacts, repairs widths, invokes ttfautohint, checks advance constraints and required tables, then copies the validated artifact to the requested output. Root executed it successfully with ttfautohint 1.8.4. No additional material script failure was found in this review. The successful checks verify widths and table presence, **not platform shaping**; the native overlay defect passes them.

Reproduction:

```sh
/opt/homebrew/Caskroom/miniconda/base/envs/py314/bin/python audit/review-claude/metadata/audit_current.py
swift -module-cache-path /tmp/photonico-swift-cache audit/metadata/coretext_check.swift audit/review-claude/generated/current-raw.ttf audit/review-claude/generated/current-built.ttf
swift -module-cache-path /tmp/photonico-swift-cache audit/review-claude/metadata/shape_coretext.swift audit/review-claude/generated/current-built.ttf
swift -module-cache-path /tmp/photonico-swift-cache audit/review-claude/metadata/render_coretext.swift audit/review-claude/generated/current-built.ttf audit/review-claude/metadata/coretext_overlay.png
```
