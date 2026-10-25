"""Build the specimen page: fill in the character list, the version and a hash of the web font in
the template (the hash changes the font URL whenever the font changes, so browsers do not keep an
old copy), and copy the variable web font next to the page.
usage: python -I specimen_page.py <template.html> <variable font> <variable woff2> <output folder>"""
import hashlib, html, os, shutil, sys, unicodedata
from fontTools.ttLib import TTFont

template, font_path, woff2, out = sys.argv[1:5]
font = TTFont(font_path)
version = font["name"].getDebugName(5).split(";")[0].replace("Version ", "")
chars = []
for cp in sorted(font.getBestCmap()):
    ch = chr(cp)
    if unicodedata.category(ch) in ("Zs", "Cc", "Cf"):           # spaces and invisible characters
        continue
    shown = "◌" + ch if unicodedata.combining(ch) else ch    # marks on a dotted circle
    name = unicodedata.name(ch, "").title()
    chars.append(f'          <li><button type="button" title="U+{cp:04X} {name}">{html.escape(shown)}</button></li>')
page = open(template, encoding="utf-8").read()
fonthash = hashlib.sha256(open(woff2, "rb").read()).hexdigest()[:12]
page = page.replace("{{glyphs}}", "\n".join(chars)).replace("{{count}}", str(len(chars))).replace("{{version}}", version)
page = page.replace("{{fonthash}}", fonthash)
os.makedirs(os.path.join(out, "fonts"), exist_ok=True)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
shutil.copy(woff2, os.path.join(out, "fonts", "TricaNeon-Variable.woff2"))
print(f"wrote {os.path.join(out, 'index.html')} ({len(chars)} characters, version {version})")
