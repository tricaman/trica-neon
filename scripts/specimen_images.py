"""Render the specimen images in documentation/images from the variable font.
HarfBuzz places the glyphs (with the kerning), Pillow draws them.
usage: python -I specimen_images.py <variable font> <output folder>"""
import os, sys
import uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont

FONT, OUT = sys.argv[1], sys.argv[2]
W, MARGIN = 2400, 140                       # twice the size they are shown at
BG, FG, MUTED = (14, 15, 18), (245, 243, 238), (139, 144, 153)
WEIGHTS = [("Thin", 100), ("ExtraLight", 200), ("Light", 300), ("Regular", 400), ("Medium", 500), ("SemiBold", 600)]
LANGUAGES = [
    ("Italian", "Perché la volpe, col suo balzo, ha già raggiunto il mio quieto Fido?"),
    ("French", "Voix ambiguë d’un cœur qui au zéphyr préfère les jattes de kiwis."),
    ("German", "Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich."),
    ("Polish", "Pchnąć w tę łódź jeża lub ośm skrzyń fig."),
    ("Czech", "Příliš žluťoučký kůň úpěl ďábelské ódy."),
    ("Hungarian", "Árvíztűrő tükörfúrógép."),
    ("Romanian", "Muzicologă în bej vând whisky și tequila, preț fix."),
    ("Turkish", "Pijamalı hasta yağız şoföre çabucak güvendi."),
    ("Spanish", "El pingüino Wenceslao hizo kilómetros bajo exhaustiva lluvia y frío, añoraba a su querido cachorro."),
    ("Danish", "Høj bly gom vandt fræk sexquiz på wc."),
]
DESCRIPTION = ("Trica Neon is drawn with a single, even stroke, like a line of neon tube. The design grows "
               "from one module: a pill as wide as the capital height and half as tall, with fully round "
               "ends. Every curve is half or a quarter of that pill, outer corners are rounded and inner "
               "joints stay sharp.")

face = hb.Face(hb.Blob.from_file_path(FONT))
UPM, CMAP = face.upem, set(face.unicodes)
_fonts = {}


def font(size, wght):
    if (size, wght) not in _fonts:
        pil = ImageFont.truetype(FONT, size)
        pil.set_variation_by_axes([wght])
        hbf = hb.Font(face)
        hbf.set_variations({"wght": wght})
        _fonts[size, wght] = pil, hbf
    return _fonts[size, wght]


def shape(text, size, wght):
    """[(character, x, y offset)] in pixels, and the width of the line."""
    hbf = font(size, wght)[1]
    buf = hb.Buffer()
    buf.add_codepoints([ord(c) for c in text])
    buf.guess_segment_properties()
    hb.shape(hbf, buf, {})
    k, x, out = size / UPM, 0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((text[info.cluster], x + pos.x_offset * k, pos.y_offset * k))
        x += pos.x_advance * k
    return out, x


def draw(d, x, baseline, text, size, wght, color=FG):
    glyphs, width = shape(text, size, wght)
    pil = font(size, wght)[0]
    for ch, gx, gy in glyphs:
        if not ch.isspace():
            d.text((x + gx, baseline - gy), ch, font=pil, fill=color, anchor="ls")
    return width


def wrap(text, size, wght, width):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = f"{cur} {word}".strip()
        if cur and shape(trial, size, wght)[1] > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def canvas(height):
    img = Image.new("RGB", (W, height), BG)
    return img, ImageDraw.Draw(img)


def save(img, name):
    path = os.path.join(OUT, name)
    img.save(path, optimize=True)
    print("saved", path, img.size)


def specimen():
    img, d = canvas(1200)
    draw(d, MARGIN, 540, "Trica Neon", 300, 600)
    size = 64
    while sum(shape(n, size, w)[1] for n, w in WEIGHTS) + 50 * (len(WEIGHTS) - 1) > W - 2 * MARGIN:
        size -= 2
    x = MARGIN
    for name, wght in WEIGHTS:
        x += draw(d, x, 790, name, size, wght) + 50
    draw(d, MARGIN, 930, "A geometric typeface drawn with a single stroke.", 44, 300, MUTED)
    draw(d, MARGIN, 1080, "Six weights and a variable font · SIL Open Font License", 32, 400, MUTED)
    save(img, "specimen.png")


def alphabet():
    lines = [("ABCDEFGHIJKLM", 130), ("NOPQRSTUVWXYZ", 130), ("abcdefghijklm", 130), ("nopqrstuvwxyz", 130),
             ("0123456789", 130), ("ÀÁÂÄÅÇÉÈÍÑÓÖØŠÚÜŽ àáâäåçéèíñóöøšúüž", 62),
             (".,:;!?¡¿'\"‘’“”«»‹›()[]{}/\\|-–— &@#%‰$€£¥¢₹§¶©®™°", 62)]
    lines = [("".join(c for c in text if c == " " or ord(c) in CMAP), size) for text, size in lines]
    gap = 40                                # before the first line of small characters
    img, d = canvas(MARGIN * 2 + gap + sum(int(s * 1.3) for _, s in lines))
    y = MARGIN
    for i, (text, size) in enumerate(lines):
        y += int(size * 1.3) + (gap if i and size < lines[i - 1][1] else 0)
        draw(d, MARGIN, y - int(size * 0.3), text, size, 400)
    save(img, "alphabet.png")


def sentence():
    big = wrap("Sphinx of black quartz, judge my vow.", 150, 400, W - 2 * MARGIN)
    body = wrap(DESCRIPTION, 40, 300, W - 2 * MARGIN)
    img, d = canvas(MARGIN * 2 + len(big) * 195 + 60 + len(body) * 52)
    y = MARGIN
    for line in big:
        y += 195
        draw(d, MARGIN, y - 45, line, 150, 400)
    y += 60
    for line in body:
        y += 52
        draw(d, MARGIN, y - 12, line, 40, 300, MUTED)
    save(img, "sentence.png")


def languages():
    label_w, size = 380, 50
    rows = [(name, wrap(text, size, 400, W - 2 * MARGIN - label_w)) for name, text in LANGUAGES]
    line_h, gap = int(size * 1.3), 28
    img, d = canvas(MARGIN * 2 + sum(len(lines) * line_h + gap for _, lines in rows) - gap)
    y = MARGIN
    for name, lines in rows:
        draw(d, MARGIN, y + line_h - 18, name, 34, 400, MUTED)
        for line in lines:
            y += line_h
            draw(d, MARGIN + label_w, y - 15, line, size, 400)
        y += gap
    save(img, "languages.png")


os.makedirs(OUT, exist_ok=True)
specimen()
alphabet()
sentence()
languages()
