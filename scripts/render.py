"""Render text lines in one or more fonts to a PNG.
usage: python -I render.py <out.png> <px> <lines.txt> <font> [<font> ...]"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

out, px, lines_file, fonts = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4:]
lines = [l.rstrip("\n") for l in open(lines_file, encoding="utf-8") if l.strip()]
label_font = ImageFont.load_default(size=14)
pad, gap = 24, int(px * 0.35)
blocks = []
for path in fonts:
    font = ImageFont.truetype(path, px)
    widths = [font.getlength(l) for l in lines]
    blocks.append((path, font, widths))
W = int(max(max(w) for _, _, w in blocks)) + 2 * pad
line_h = int(px * 1.25)
H = sum(22 + len(lines) * line_h + gap for _ in blocks) + pad
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
y = pad // 2
for path, font, _ in blocks:
    d.text((pad, y), os.path.basename(path), fill=(150, 150, 150), font=label_font)
    y += 22
    for l in lines:
        d.text((pad, y), l, fill="black", font=font)
        y += line_h
    y += gap
img.save(out)
print("saved", out, img.size)
