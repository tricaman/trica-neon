"""Like render.py, with a custom label per font.
usage: python -I render_labeled.py <out.png> <px> <lines.txt> <label::font> [...]"""
import sys
from PIL import Image, ImageDraw, ImageFont
out, px, lines_file, items = sys.argv[1], int(sys.argv[2]), sys.argv[3], [a.split("::") for a in sys.argv[4:]]
lines = [l.rstrip("\n") for l in open(lines_file, encoding="utf-8") if l.strip()]
lab = ImageFont.load_default(size=15)
fonts = [(label, ImageFont.truetype(path, px)) for label, path in items]
pad, line_h = 24, int(px * 1.25)
W = int(max(f.getlength(l) for _, f in fonts for l in lines)) + 2 * pad
H = pad + len(fonts) * (24 + len(lines) * line_h + 10)
img = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(img); y = pad // 2
for label, f in fonts:
    d.text((pad, y), label, fill=(120, 120, 120), font=lab); y += 24
    for l in lines:
        d.text((pad, y), l, fill="black", font=f); y += line_h
    y += 10
img.save(out); print("saved", out, img.size)
