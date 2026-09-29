# Metadata and binary audit (2026-09-29)

> 历史检查快照：结论与源码行号对应当时的字体版本。报告已从 `audit/` 迁移；旧复现命令与未单独展开的中间文件完整保存在[原始证据压缩包](../../archive/font-audit-2026-09-29.zip)，解压后可还原原目录。最新结论请看 reports 的总索引。


Scope: primary `00_Regular.sfd`, unchanged current-source export `audit/generated/Photonico-current.ttf`, and 20 archived TTFs. `release_metadata.json` contains all evidence. No source/release was changed. Tools: fontTools 4.61.1, HarfBuzz, Fontconfig. Linux/Windows application behavior has not been run on those operating systems.

## Material source findings

1. Monospace metadata remains wrong: post.isFixedPitch=0, all PANOSE fields=0 (source line 35); current and release 1.5 have only two nonzero advance exceptions, dollar.spacer and dollar.ss04, both 1206. All encoded ordinary glyphs have width 1200 and 22 marks/control glyphs have zero width. [OpenType post specification](https://learn.microsoft.com/en-us/typography/opentype/spec/post) defines nonzero isFixedPitch for monospaced fonts. Native macOS CoreText reports symbolic traits=0 and traitMonoSpace=false for the current export and release 1.5 (`coretext_scan.txt`). However, **Fontconfig reports spacing=100 (monospace)** even with the flag 0. Do not repeat the screenshot's broad claim that every system fails to recognize it; Windows Terminal filtering is plausible but not runtime-tested. Fix exceptional widths, export and check flag, then set coherent PANOSE.


2. Four Unicode combining marks incorrectly occupy a full 1200-unit cell: U+0323 (source line 112006), U+0325 (112097), U+0335 (83991), U+0336 (84024). Current generated GDEF classes are base/base/unclassified/unclassified, respectively. None is a mark class. HarfBuzz reproduces `x̶x` as x(+1200), uni0336(+1200), x(+1200); the strike is placed in its own cell instead of overlaying x. Same issue for the other three marks. Fix requires zero advance, correct mark classification and positioning anchors/attachment; changing width alone is insufficient. Evidence: `combining_shape.txt`.


3. `Ccedilla` has USE_MY_METRICS on **both** component references (SFD lines 9056–9057). Generated gid 138 has component flags 0x1204 on cedilla and C. Their LSBs differ: cedilla=329, C=110; parent=110. FontForge warns this is bad glyf/loca. Keep the metric-owner flag only on the C base component. Current and release 1.5 are affected. Evidence: `current_multiple_metrics.json`. [OpenType glyf specification](https://learn.microsoft.com/en-us/typography/opentype/spec/glyf) defines the flag as taking advance and side bearings from that component. It does not explicitly state the maximum count; the concrete validator error is stronger evidence than claiming that all renderers fail.


4. Version metadata remains inconsistent: SFD `Version: 1.6_alpha` (line 7), `sfntRevision: 0x0000199a` (line 14, 0.100006), and name IDs 3/5 still `1.4; PhotonicoCode-Regular` / `Version 1.4` (line 8282). The current export embeds the stale 1.4 version. Synchronize the numeric revision, internal version/unique ID, source version and release filename on publication. No installed-font cache malfunction was reproduced.


5. No glyph instructions: 0/2230 generated glyphs have TrueType instructions, although fpgm=3605 bytes, prep=214 bytes and cvt=86 entries remain. gasp is 65535:15, requesting grid fitting and antialiasing across all PPEM. Source fpgm/prep lines 4586/4400, gasp line 8283. This confirms missing glyph hinting and leftover tables, but does not by itself prove a specific 13px rendering defect or guarantee macOS is unaffected. Compare native Windows and FreeType hinted/unhinted rendering before choosing ttfautohint or clean unhinted export.


6. Cyrillic codepage declarations are stale: source line 62 declares bits 2 (1251), 49 (866), 57 (855), while current cmap has 0/96 U+0400–045F. FontTools-derived codepage bits differ by exactly those three bits. Unicode-range bits do not have excess flags under FontTools's membership check. Recompute codepages without those bits unless Cyrillic is restored.

## Additional precision / lower-priority findings

- Stored TrueType bounding boxes include isolated point contours. G has yMin=-911; root source audit identifies the corresponding isolated point. The stored bbox is faithful to coordinates, but not useful visible-ink bounds. Fix geometry first, then recompute metrics. Current head bbox is (-3610,-1000,3517,2400); negative x for ligatures is not inherently erroneous.
- `head.flags` includes bit 1 (LSB equals xMin for all glyphs) despite 142 glyphs differing by one unit (e.g. copyright LSB=0, xMin=-1). FontTools maxp.recalc changes flags 11→9 and leaves every maxp value unchanged. Low-impact export inconsistency; not evidence of visible glyph breakage. Clear flag or export rounded bounds consistently.
- `uniD53E` is actually mapped correctly to U+1D53E DOUBLE-STRUCK CAPITAL G, but its PostScript glyph name convention implies U+D53E (Hangul). Source line 88820. Low-priority naming fix to `u1D53E`; current Unicode cmap is correct.
- Coverage: 1784 Unicode mappings / 2230 glyphs; printable ASCII 95/95; Latin-1 U+00A0–00FF 96/96; Greek block 121/144 codepoint slots (slots include unassigned codepoints, so this is not a missing-required-character claim); Box Drawing 128/128; Block Elements 32/32; Combining Diacritics 23/112; Braille 0/256. Absence of Braille is an optional coverage limitation, not a corrupt font.
- All current tables decode successfully; per-table checksums and whole font checksum are correct. Every glyph can be drawn by fontTools. These checks do **not** override the separate double-USE_MY_METRICS validator failure.

## Historical archive notes

- All 20 releases 0.1–1.5 have post.isFixedPitch=0 and head.fontRevision≈0.1.
- Release 1.0 names itself Version 1.1; release 1.5 names itself Version 1.4.
- Hinting is already absent from 1.1, not only from 1.2 onward. 0.1=1264 hinted glyphs; 1.0=175; 1.1–1.5=0.
- Release 0.9 only: zero.cv13 throws fontTools draw IndexError (empty/invalid contour). This does not affect current source/current export.

## Native classification reproduction

```sh
swift -module-cache-path /tmp/photonico-swift-cache audit/metadata/coretext_check.swift 'Releases/Photonico 1.5 Regular.ttf' audit/generated/Photonico-current.ttf
fc-scan --format '%{family}: spacing=%{spacing}\n' audit/generated/Photonico-current.ttf
```

The Swift test loads each file directly with CGDataProvider → CGFont → CTFontCreateWithGraphicsFont, so it does not depend on font installation or font-cache selection. Both files report `traits=0 monoSpace=false`; Fontconfig reports `spacing=100`.
