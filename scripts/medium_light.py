# Derive Photonico Code Medium Light from a built Regular TTF
#
#   python3 scripts/medium_light.py REGULAR.ttf [output.ttf]
#
# Needs fontTools and skia-pathops in this Python (pip install fonttools skia-pathops),
# plus the ttfautohint command. TTFAUTOHINT overrides where it is found.
# The Regular TTF is only read, never written.
#
# Steps:
#   1. Every simple glyph is thinned by OFFSET font units on each side: the outline
#      minus a round-joined stroke of width 2 * OFFSET. Regular strokes are 140 units
#      wide; OFFSET = 10 gives the Medium Light stroke of 120 units. Advance widths,
#      composites, features and anchors are unchanged.
#      - Box drawing and bracket pieces must still meet their neighbours. Where such a
#        glyph reaches beyond the cell or the line, its ends are mirrored outwards before
#        thinning and cut back afterwards, so only the line width changes.
#      - Block elements and Powerline glyphs are solid fills and keep the Regular outline.
#      - Slivers smaller than 4 * OFFSET**2 square units are dropped. A glyph whose
#        contour count would still change keeps the Regular outline.
#   2. The names become Photonico Code Medium Light, with the typographic family
#      Photonico Code and subfamily Medium Light, and the OS/2 weight class is 350.
#   3. The Regular hinting does not fit the new outlines. It is removed, and
#      ttfautohint hints the result again.
#   4. The checks of build.py are repeated.

import os
import shutil
import subprocess
import sys
import tempfile

import pathops
from fontTools.pens.basePen import BasePen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFSET = 10
WEIGHT_CLASS = 350
FAMILY = "Photonico Code"
STYLE = "Medium Light"
CELL = 1200
CONNECT = ((0x2500, 0x257F), (0x2320, 0x2321), (0x239B, 0x23B3), (0x23AF, 0x23AF), (0x23D0, 0x23D0))
KEEP = ((0x2580, 0x259F), (0xE0A0, 0xE0D7))
FAR = 10000


class SkiaPen(BasePen):
    """Feeds a TrueType outline into a skia path; BasePen resolves implied on-curve points."""

    def __init__(self, path):
        super().__init__(None)
        self.path = path

    def _moveTo(self, pt):
        self.path.moveTo(*pt)

    def _lineTo(self, pt):
        self.path.lineTo(*pt)

    def _qCurveToOne(self, pt1, pt2):
        self.path.quadTo(*pt1, *pt2)

    def _curveToOne(self, pt1, pt2, pt3):
        self.path.cubicTo(*pt1, *pt2, *pt3)

    def _closePath(self):
        self.path.close()

    def _endPath(self):
        self.path.close()


def op(one, two, operator):
    return pathops.op(one, two, operator, fix_winding=True, keep_starting_points=False, clockwise=True)


def rect(x0, y0, x1, y1):
    path = pathops.Path()
    path.moveTo(x0, y0)
    path.lineTo(x0, y1)
    path.lineTo(x1, y1)
    path.lineTo(x1, y0)
    path.close()
    return path


def mirrored(path, axis, at):
    out = pathops.Path()
    matrix = (-1, 0, 0, 1, 2 * at, 0) if axis == "x" else (1, 0, 0, -1, 0, 2 * at)
    path.draw(TransformPen(out.getPen(), matrix))
    return out


def outline(glyph_set, name):
    path = pathops.Path()
    glyph_set[name].draw(SkiaPen(path))
    return pathops.simplify(path, fix_winding=True, keep_starting_points=False, clockwise=True)


def eroded(path, offset):
    band = pathops.Path()
    path.draw(band.getPen())
    band.stroke(2 * offset, pathops.LineCap.BUTT_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    band.convertConicsToQuads()
    return op(path, band, pathops.PathOp.DIFFERENCE)


def thinned(path, offset, connect, line):
    """Erosion; for connecting glyphs the ends beyond the cell or the line keep their reach."""
    if not connect:
        return eroded(path, offset)
    x0, y0, x1, y1 = path.bounds
    margin = 3 * offset
    sides = []
    if x0 <= 0:
        sides.append(("x", x0, rect(x0, y0 - 1, x0 + margin, y1 + 1)))
    if x1 >= CELL:
        sides.append(("x", x1, rect(x1 - margin, y0 - 1, x1, y1 + 1)))
    if y0 <= line[0]:
        sides.append(("y", y0, rect(x0 - 1, y0, x1 + 1, y0 + margin)))
    if y1 >= line[1]:
        sides.append(("y", y1, rect(x0 - 1, y1 - margin, x1 + 1, y1)))
    extended = path
    for axis, at, strip in sides:
        part = op(path, strip, pathops.PathOp.INTERSECTION)
        extended = op(extended, mirrored(part, axis, at), pathops.PathOp.UNION)
    clip = rect(x0 if x0 <= 0 else -FAR, y0 if y0 <= line[0] else -FAR,
                x1 if x1 >= CELL else FAR, y1 if y1 >= line[1] else FAR)
    return op(eroded(extended, offset), clip, pathops.PathOp.INTERSECTION)


def without_slivers(path, min_area):
    out = pathops.Path()
    for contour in path.contours:
        if abs(contour.area) >= min_area:
            contour.draw(out.getPen())
    return out


def tt_glyph(path):
    pen = TTGlyphPen(None)
    path.draw(Cu2QuPen(pen, 1.0))
    glyph = pen.glyph()
    glyph.recalcBounds(None)
    return glyph


def in_ranges(codepoints, ranges):
    return any(lo <= cp <= hi for cp in codepoints for lo, hi in ranges)


def thin_outlines(font, offset):
    glyph_set = font.getGlyphSet()
    glyf, hmtx = font["glyf"], font["hmtx"]
    line = (font["hhea"].descent, font["hhea"].ascent)
    codepoints = {}
    for cp, name in font.getBestCmap().items():
        codepoints.setdefault(name, []).append(cp)
    min_area = 4 * offset ** 2
    kept, unchanged = [], 0
    for name in font.getGlyphOrder():
        glyph = glyf[name]
        if glyph.isComposite() or glyph.numberOfContours <= 0:
            continue
        cps = codepoints.get(name, [])
        if in_ranges(cps, KEEP):
            unchanged += 1
            continue
        base = outline(glyph_set, name)
        new = without_slivers(thinned(base, offset, in_ranges(cps, CONNECT), line), min_area)
        base_count = len([c for c in base.contours if abs(c.area) >= min_area])
        if len(list(new.contours)) != base_count or abs(new.area) < 0.5 * abs(base.area):
            kept.append(name)
            continue
        new_glyph = tt_glyph(new)
        glyf[name] = new_glyph
        hmtx[name] = (hmtx[name][0], new_glyph.xMin)
    return kept, unchanged


def remove_hinting(font):
    for name in font.getGlyphOrder():
        glyph = font["glyf"][name]
        if hasattr(glyph, "program"):
            glyph.program = ttProgram.Program()
            glyph.program.fromBytecode(b"")
    for tag in ("fpgm", "prep", "cvt ", "hdmx", "LTSH", "VDMX"):
        if tag in font:
            del font[tag]


def rename(font):
    names = font["name"]
    version = names.getDebugName(5).split(";")[0].strip()
    number = version.replace("Version", "").strip()
    full = "%s %s" % (FAMILY, STYLE)
    postscript = "%s-%s" % (FAMILY.replace(" ", ""), STYLE.replace(" ", ""))
    platforms = {(r.platformID, r.platEncID, r.langID) for r in names.names if r.nameID == 1}
    for platform in platforms:
        for name_id, text in ((1, full), (2, "Regular"), (3, "%s; %s" % (number, postscript)),
                              (4, full), (5, version), (6, postscript),
                              (16, FAMILY), (17, STYLE)):
            names.setName(text, name_id, *platform)
    font["OS/2"].usWeightClass = WEIGHT_CLASS


def check(font):
    errors = []
    marks = {g for g, c in font["GDEF"].table.GlyphClassDef.classDefs.items() if c == 3}
    for name in font.getGlyphOrder():
        adv = font["hmtx"][name][0]
        if adv not in (0, CELL):
            errors.append("%s is %d wide" % (name, adv))
        if name in marks and adv != 0:
            errors.append("combining mark %s is %d wide" % (name, adv))
    if font["post"].isFixedPitch != 1:
        errors.append("post.isFixedPitch is not set")
    if "fpgm" not in font or "prep" not in font:
        errors.append("ttfautohint added no hinting")
    return errors


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 scripts/medium_light.py REGULAR.ttf [output.ttf]")
    regular = os.path.abspath(sys.argv[1])
    default_out = os.path.join(ROOT, "build", "PhotonicoCode-MediumLight.ttf")
    out = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else default_out)
    if out == regular:
        sys.exit("the output would overwrite the Regular TTF")
    ttfautohint_bin = os.environ.get("TTFAUTOHINT") or shutil.which("ttfautohint")
    if not ttfautohint_bin:
        sys.exit("cannot find ttfautohint (set TTFAUTOHINT)")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        unhinted = os.path.join(tmp, "unhinted.ttf")
        hinted = os.path.join(tmp, "hinted.ttf")

        font = TTFont(regular)
        kept, unchanged = thin_outlines(font, OFFSET)
        remove_hinting(font)
        rename(font)
        font["maxp"].recalc(font)
        font.save(unhinted)

        subprocess.run([ttfautohint_bin, unhinted, hinted], check=True)

        font = TTFont(hinted)
        errors = check(font)
        if errors:
            sys.exit("build failed:\n  " + "\n  ".join(errors))
        shutil.copyfile(hinted, out)

    print("built %s (%s, weight class %d)" % (out, font["name"].getDebugName(4), WEIGHT_CLASS))
    print("thinned by %d units per side; %d block and Powerline glyphs unchanged; "
          "%d glyphs keep the Regular outline%s" % (
              OFFSET, unchanged, len(kept), (": " + " ".join(kept)) if kept else ""))


if __name__ == "__main__":
    main()
