# Shaping audit — 2026-09-29

> 历史检查快照：结论与源码行号对应当时的字体版本。报告已从 `audit/` 迁移；旧复现命令与未单独展开的中间文件完整保存在[原始证据压缩包](../../archive/font-audit-2026-09-29.zip)，解压后可还原原目录。最新结论请看 reports 的总索引。


Inputs: release `Releases/Photonico 1.5 Regular.ttf` and fresh unchanged-source `audit/generated/Photonico-current.ttf`. Engine: HarfBuzz 14.5.0, OpenType shaper. All findings below reproduce in both unless stated otherwise. Font sources/releases were not modified.

Run:

```sh
/opt/homebrew/Caskroom/miniconda/base/envs/py314/bin/python audit/shaping/audit_shaping.py
/opt/homebrew/bin/hb-shape audit/generated/Photonico-current.ttf 'x̀ q̌ r̂ x̂ Λ̂ ϕ̂ x̣ q̥ x̵ x̶' --shapers=ot --output-format=json
```

## New confirmed defects

1. **Four nonspacing marks occupy an extra cell.** U+0323 dot below, U+0325 ring below, U+0335 short stroke overlay, U+0336 long stroke overlay have advance 1200, missing mark anchors and are not classified as marks in compiled GDEF. `x̣`, `q̥`, `x̵`, `x̶` each shape to advance 2400. The mark is at `dx=0` after a base of advance 1200, so it is drawn in the following cell. Source width lines: 112008, 112099, 83993, 84026. This is independent of dollar widths and remains even if every glyph has nominal advance 1200: combining marks need zero advance, mark classification and attachment.

2. **Missing combining anchors put accents in the next cell.** Mark glyphs U+0300 `gravecomb` (83577–83611) and U+030C `uni030C` (83709–83750) have zero width but no `AnchorPoint` definitions. Thus `x̀`/`q̌` return mark `dx=0` rather than about `-1200`; their positive x-bounds then lie in the following character cell. Compare U+0301 `acutecomb`, whose anchors are present at 83618–83619.

3. **Missing base anchors affect scientific notation and extended letters.** `r̂`, `Λ̂`, `ϕ̂`, `œ̂` produce the same next-cell displacement for otherwise correctly anchored circumflex. `x̂` returns `uni0302 dx=-1200`; `r̂` returns `uni0302 dx=0`. `r` (16965–17027), `Lambda` (21898–21967), `phi1` (30370–30464), and `oe` (16654–16718) have no anchor definitions. Compare `x` base anchors at 18044–18045. A sweep of 683 encoded scalars whose Unicode category is Letter and name contains LATIN or GREEK, each followed by U+0302, found 108 sequences with a final separate mark at dx=0. This is a diagnostic coverage count, **not 108 equally common text failures**; it includes extended/IPA and already-accented combinations. Results: `latin_greek_mark_base_gaps.json`.

The six mark defects and the missing base anchors are related but separate repairs: fixing mark width alone does not attach it, and fixing mark anchors alone does not supply missing anchors on `r` etc.

## Reconfirmed screenshot items

- `<$>` advances 3606 and `$>` advances 2406 due `dollar.spacer=1206`. Normal grid width is 1200. `ss04=1` changes ordinary `$` to `dollar.ss04=1206`.
- Double/triple backticks use `grave.case` in release 1.5; the current source build uses `grave`, confirming source repair.
- NFC and decomposed NFD `ý` / `ÿ` both normalize to the same `yacute` / `ydieresis`, so typing decomposed text does not bypass the defective composite glyphs.

## Coverage / limits

- Tested 61 programming samples with default shaping and `calt=0`; only `<$>` and `$>` changed total grid width unexpectedly in that corpus. The corpus also exercises arrows, equality, comments, Markdown backticks and punctuation.
- Enumerated 59 GSUB feature tags. Tested a mixed ASCII/programming corpus for 58 opt-in tags (excluded `aalt`), and tested each encoded scalar individually under these 58 tags. The only non-grid nominal glyph advance found in this optional-feature sweep was `$` with `ss04` (1206). This does not claim every contextual combination was exhaustively tested.
- Tested all 23 encoded combining marks with `x`; some normalize to precomposed glyphs, so this is a practical text check, not exhaustive anchor validation.
- Tested 493 mapped characters with mapped canonical decompositions. 25 used different glyph identities; glyph-name differences alone are not defects. Several Greek oxia/tonos forms and the ohm sign differ visually: e.g. U+2126 `uni2126` yMax=1220 versus U+03A9 `uni03A9` yMax=1320. Treat these as a design/canonical-equivalence review, not a newly proven spacing bug.
- Also ran the macOS CoreText shaper. Its fallback heuristics repair grave/caron placement, so those errors are engine-dependent. U+0323/U+0325 still consume 2400 under CoreText. U+0335/U+0336 give different heuristic advances there, further supporting proper font-level repair. No native Windows/Linux application session was available in this sub-audit; HarfBuzz reproduction is not a substitute for platform UI testing.

Full results: `shaping_results.json` (~all feature samples and machine-readable glyph positions).
