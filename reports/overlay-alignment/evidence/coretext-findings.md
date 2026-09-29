# Native CoreText geometric alignment verification

Both fonts were loaded directly by CGFont/CTFontCreateWithGraphicsFont. Native measurements use size 1950, equal to unitsPerEm, so the numbers below are font units. Separate before/after processes avoid same-name font-cache ambiguity.

All 15 tested sequences retain their exact total advances. Seven control sequences retain all glyph positions too: plain xx, q+acute+q, q+acute+overlay+q, dot/ring below on x, U+200B and U+FEFF. CoreText still identifies the font as monospaced.

Native overlay position changes match the five-anchor edit:

- x, short or long overlay: y 0 → -140, ink centre y 620 → 480. Both stacked-overlay orders also use -140, without moving the second x from cell 1200. Total remains 2400.
- -- plus short overlay: overlay origin x 1200 → 600, y 0 → -20; ink centre moves from (1800,620) to (1200,600), the whole ligature centre. Total remains 2400. This now fills the middle gap, consistent with centring the short stroke on the full ligature.
- Single hyphen plus short overlay: y 0 → -20; total remains 1200.
- Double-struck E plus long overlay: origin x 0 → -5, y 0 → 30; native ink centre becomes (596,650), versus source target (595,650).
- Dotted circle plus long overlay: y 0 → -20; native ink centre becomes (601,600), versus source target (600,600).

The one-unit horizontal differences for long overlays are the existing exported-outline/side-bearing rounding, not movement introduced by these anchor edits. For x the native long-overlay centre is similarly (601,480), source target (600,480).

Artifacts:

- `native-before-after.png`: eight rows with identical 1200-unit cell guides and native measured widths.
- `native-geometric-centers.png`: native base glyphs in black, overlays in red, and source target centres as green crosshairs. Both images were visually inspected.
- `before.txt`, `after.txt`, `center-measurements.txt`: exact native glyph positions and ink-centre measurements.
- `regression.json`: 15 cases with no advance changes and the seven unchanged controls.
- `shape_coretext.swift`, `render-comparison.swift`, `render-centers.swift`: reproduction scripts.

This verifies the specified glyphs and controls in local native macOS CoreText. It does not claim universal Windows/Linux rendering or exhaustive coverage of every base/mark combination.
