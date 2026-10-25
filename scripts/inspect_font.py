"""Print names, vertical metrics and the glyphs that fall outside them.
usage: python -I inspect_font.py <font.otf>"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

f = TTFont(sys.argv[1])
print("name:")
for rec in f["name"].names:
    if rec.platformID == 3:
        print(f"  {rec.nameID:>2}: {rec.toUnicode()}")
os2, hhea, head = f["OS/2"], f["hhea"], f["head"]
print(f"OS/2 v{os2.version}: weight {os2.usWeightClass}, fsType {os2.fsType}, fsSelection {os2.fsSelection:#06x}, "
      f"vendor {os2.achVendID!r}")
print(f"  typo {os2.sTypoAscender}/{os2.sTypoDescender}/{os2.sTypoLineGap}, win {os2.usWinAscent}/{os2.usWinDescent}, "
      f"capHeight {os2.sCapHeight}, xHeight {os2.sxHeight}")
print(f"hhea {hhea.ascent}/{hhea.descent}/{hhea.lineGap}; head bbox y {head.yMin}..{head.yMax}, x {head.xMin}..{head.xMax}; "
      f"version {head.fontRevision}")

gs = f.getGlyphSet()
cmap = {v: k for k, v in f.getBestCmap().items()}
over, under, empty = [], [], []
for name in f.getGlyphOrder():
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    if not bp.bounds:
        empty.append(name)
        continue
    xmin, ymin, xmax, ymax = bp.bounds
    label = f"{name}({chr(cmap[name])})" if name in cmap else name
    if ymax > os2.usWinAscent:
        over.append((ymax, label))
    if -ymin > os2.usWinDescent:
        under.append((ymin, label))
print("above winAscent:", sorted(over, reverse=True)[:12], f"({len(over)} total)")
print("below winDescent:", sorted(under)[:12], f"({len(under)} total)")
print("empty glyphs:", empty)
