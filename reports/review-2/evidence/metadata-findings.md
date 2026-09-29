# Latest Claude changes: native CoreText and metadata review

Reviewed source SHA-256: `c1db32b7c031ff93e4417891bb73fc2e04790188947b4297151f56d43d557ee2`. Build script is unchanged (`9245b3050cc4dafb2c99dc16a13296ddd7402b6854dab69bb84860331b031f41`). All new review artifacts are confined to `/tmp/photonico-review-2/metadata`; no source or prior audit artifacts were changed.

## Result

The previously demonstrated native macOS overlay advance defects are fixed in the latest script-built font. Fourteen targeted native CoreText cases pass their expected cell advances and ordinary controls remain unchanged:

- `x U+0336 x`: 2592 → 2400 units; second x now starts at 1200 instead of 1392.
- `-- U+0335`: 2750 → 2400 units.
- `x U+0335 U+0336 x` and reversed mark order: 2592 → 2400.
- Double-struck E U+1D53C plus U+0336: 1391 → 1200.
- Dotted circle U+25CC plus U+0336: 1322 → 1200.
- Plain xx, acute accents, short overlay on x, dot below, ring below, acute+overlay, U+200B and U+FEFF controls retain their expected widths.

See `coretext_before.txt`, `coretext_after.txt`, and visually checked `native-before-after.png`. `coretext_raw.txt` confirms the native targeted cases also shape correctly in the direct FontForge export.

The test loads each specific TTF with CGFont/CTFontCreateWithGraphicsFont and uses only kCTFontAttributeName on text. Measurements use a font size of 1950, equal to UPM, so values are font units. Before/after numerical tests ran in separate processes. The native PNG uses CTLine at 84 px with 1200-unit grid guides; its scaled totals agree with the independent 1950-unit tests.

## Metadata/build regression checks

- Native CoreText continues to identify the built font as monospaced; post.isFixedPitch=1 and PANOSE family/proportion=2/9 remain correct.
- Script-built advances match all source widths: 2204 glyphs at 1200, 26 at zero. No nonstandard advances.
- Direct FontForge export still changes 25 explicit zero advances to 1200; the unchanged build script repairs them. This is the prior build-path constraint, not a new regression. Native shapers can mask this raw hmtx difference by zeroing marks/ignorables.
- 2230 glyphs and 1784 Unicode mappings remain unchanged. All tables decode, per-table checksums and whole-font checksum pass, all glyphs draw through fontTools, no multiple-USE_MY_METRICS composite exists, and no excess Cyrillic codepage bits reappear.
- Version remains 1.6_alpha and revision≈1.6. Built output preserves the ttfautohint(v1.8.4) name suffix, 1627 instructed glyphs, fpgm=3596 bytes, prep=203 bytes, and gasp=15. Direct export is unhinted with gasp=10.
- The pre-existing minor head.flags bit-1 / 142 one-unit LSB/xMin discrepancies remain. They were not introduced by this patch and do not invalidate the native overlay fix.

No new material metadata or native CoreText regression was found within this targeted review. This is not a native Windows/Linux test, nor proof of every possible Unicode/feature combination.

## Reproduction

```sh
/opt/homebrew/Caskroom/miniconda/base/envs/py314/bin/python /tmp/photonico-review-2/metadata/audit_fonts.py
swift -module-cache-path /tmp/photonico-swift-cache /tmp/photonico-review-2/metadata/shape_coretext.swift /tmp/photonico-review-2/generated/current-built.ttf
swift -module-cache-path /tmp/photonico-swift-cache /tmp/photonico-review-2/metadata/render_compare.swift /tmp/photonico-review-2/baseline-audit/review-claude/generated/current-built.ttf /tmp/photonico-review-2/generated/current-built.ttf /tmp/photonico-review-2/metadata/native-before-after.png
```
