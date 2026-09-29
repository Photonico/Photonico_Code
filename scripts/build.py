# Build the release TTF from 00_Regular.sfd
#
#   python3 scripts/build.py [output.ttf]
#
# Needs fontTools in this Python (pip install fonttools), plus the fontforge and
# ttfautohint commands. FONTFORGE / TTFAUTOHINT override where they are found.
#
# Steps:
#   1. FontForge generates the TTF. Version fields are all taken from the SFD
#      "Version" (e.g. 1.6_alpha -> head.fontRevision 1.6, name ID 3/5).
#   2. fontTools restores the SFD advance widths. FontForge writes every glyph
#      as 1200 wide once the font is monospaced, which would give combining
#      marks and U+200B a full cell.
#   3. ttfautohint adds TrueType hinting.
#   4. The result is checked before it is kept.

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SFD = os.path.join(ROOT, "00_Regular.sfd")
CELL = 1200
FONTFORGE_APP = "/Applications/FontForge.app/Contents/Resources/opt/local/bin/fontforge"

try:
    import fontforge
except ImportError:
    fontforge = None


def ff_generate(sfd, out_ttf, widths_json):
    """Runs inside FontForge."""
    f = fontforge.open(sfd)
    version = f.version
    number = re.match(r"\d+(\.\d+)?", version).group(0)
    f.sfntRevision = float(number)
    f.appendSFNTName("English (US)", "UniqueID", "%s; %s" % (version, f.fontname))
    f.appendSFNTName("English (US)", "Version", "Version %s" % version)
    with open(widths_json, "w", encoding="utf-8") as fp:
        json.dump({g.glyphname: g.width for g in f.glyphs()}, fp)
    f.generate(out_ttf)


def find_tool(env, name, fallback=None):
    path = os.environ.get(env) or shutil.which(name) or fallback
    if not path or not os.path.exists(path):
        sys.exit("cannot find %s (set %s)" % (name, env))
    return path


def main():
    from fontTools.ttLib import TTFont

    fontforge_bin = find_tool("FONTFORGE", "fontforge", FONTFORGE_APP)
    ttfautohint_bin = find_tool("TTFAUTOHINT", "ttfautohint")
    default_out = os.path.join(ROOT, "build", "PhotonicoCode-Regular.ttf")
    out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else default_out)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        raw = os.path.join(tmp, "raw.ttf")
        fixed = os.path.join(tmp, "fixed.ttf")
        hinted = os.path.join(tmp, "hinted.ttf")
        widths_json = os.path.join(tmp, "widths.json")

        # 1. FontForge
        subprocess.run([fontforge_bin, "-lang=py", "-script", os.path.abspath(__file__),
                        "--ff-generate", SFD, raw, widths_json], check=True)

        # 2. Advance widths and monospace flag
        with open(widths_json, encoding="utf-8") as fp:
            widths = json.load(fp)
        font = TTFont(raw)
        hmtx = font["hmtx"]
        for name in font.getGlyphOrder():
            if name in widths and hmtx[name][0] != widths[name]:
                hmtx[name] = (widths[name], hmtx[name][1])
        font["post"].isFixedPitch = 1
        font.save(fixed)

        # 3. Hinting
        subprocess.run([ttfautohint_bin, fixed, hinted], check=True)

        # 4. Checks
        font = TTFont(hinted)
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
        if errors:
            sys.exit("build failed:\n  " + "\n  ".join(errors))
        shutil.copyfile(hinted, out)

    names = font["name"]
    print("built %s (%s)" % (out, names.getDebugName(5)))


if __name__ == "__main__":
    if fontforge is not None and "--ff-generate" in sys.argv:
        i = sys.argv.index("--ff-generate")
        ff_generate(*sys.argv[i + 1:i + 4])
    else:
        main()
