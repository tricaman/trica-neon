"""Compare two OTFs table by table, ignoring head timestamps and checksums.
usage: python -I compare.py <reference.otf> <generated.otf>"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

ref, gen = TTFont(sys.argv[1]), TTFont(sys.argv[2])
print("tables ref:", sorted(ref.keys()))
print("tables gen:", sorted(gen.keys()))

for tag in sorted(set(ref.keys()) | set(gen.keys())):
    if tag in ("GlyphOrder",):
        continue
    if tag not in ref or tag not in gen:
        print(f"{tag}: missing in one font"); continue
    a, b = ref[tag].compile(ref), gen[tag].compile(gen)
    if tag == "head":
        ha, hb = ref["head"], gen["head"]
        fields = [k for k in vars(ha) if k not in ("created", "modified", "checkSumAdjustment", "tableTag")]
        diff = [k for k in fields if getattr(ha, k) != getattr(hb, k)]
        print(f"head: {'identical (timestamps aside)' if not diff else 'differs in ' + str(diff)}")
        continue
    print(f"{tag}: {'identical' if a == b else 'DIFFERENT'}")

# outlines, glyph by glyph, as a second check independent from the CFF encoding
gsa, gsb = ref.getGlyphSet(), gen.getGlyphSet()
diff = []
for name in ref.getGlyphOrder():
    pa, pb = RecordingPen(), RecordingPen()
    gsa[name].draw(pa); gsb[name].draw(pb)
    if pa.value != pb.value or gsa[name].width != gsb[name].width:
        diff.append(name)
print("glyph order equal:", ref.getGlyphOrder() == gen.getGlyphOrder())
print("glyphs with different outlines or advance:", diff or "none")
print("glyphs:", len(ref.getGlyphOrder()), "codepoints:", len(ref.getBestCmap()))
