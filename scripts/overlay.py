"""Overlay the same text set in two fonts: black where both draw, red where only the
first does, blue where only the second does. For before/after proofs of shape changes.
usage: python -I overlay.py <out.png> <px> <lines.txt> <first font> <second font> [<label>]"""
import sys
from PIL import Image, ImageChops, ImageDraw, ImageFont

out, px, lines_file, fa, fb = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
label = sys.argv[6] if len(sys.argv) > 6 else ""
lines = [l.rstrip("\n") for l in open(lines_file, encoding="utf-8") if l.strip()]
A, B = ImageFont.truetype(fa, px), ImageFont.truetype(fb, px)
pad, line_h, top = 24, int(px * 1.3), 34 if label else 12
W = int(max(max(A.getlength(l), B.getlength(l)) for l in lines)) + 2 * pad
H = top + len(lines) * line_h + pad


def mask(font):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for i, l in enumerate(lines):
        d.text((pad, top + i * line_h), l, fill=255, font=font)
    return m


ma, mb = mask(A), mask(B)
img = Image.merge("RGB", (ImageChops.invert(mb), ImageChops.invert(ImageChops.lighter(ma, mb)), ImageChops.invert(ma)))
if label:
    ImageDraw.Draw(img).text((pad, 10), label, fill=(110, 110, 110), font=ImageFont.load_default(size=16))
img.save(out)
print("saved", out, img.size)
