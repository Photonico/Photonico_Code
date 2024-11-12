# Width check

# Set the standard width to 1200
standard_width = 1200

font = fontforge.activeFont()
for glyph in font.glyphs():
    if glyph.width != standard_width:
        print(f"Glyph '{glyph.glyphname}' has a width of {glyph.width}, which differs from the standard width of {standard_width}.")
