"""Assemble the npm package, in the style of Fontsource: the WOFF2 files and ready-made CSS.
index.css loads the variable font (every weight from one file); 100.css to 600.css load one
static weight each and static.css all of them.
usage: python -I npm_package.py <webfonts folder> <OFL.txt> <font version> <output folder> [package revision]"""
import json, os, shutil, sys

webfonts, license_file, font_version, out = sys.argv[1:5]
revision = int(sys.argv[5]) if len(sys.argv) > 5 else 0
NAME, FAMILY = "trica-neon", "Trica Neon"
WEIGHTS = [("Thin", 100), ("ExtraLight", 200), ("Light", 300), ("Regular", 400), ("Medium", 500), ("SemiBold", 600)]
major, minor = font_version.split(".")
version = f"{int(major)}.{int(minor)}.{revision}"        # font version 1.000 -> package version 1.0.0; a new package
                                                         # of the same fonts takes the next revision (1.0.1)
IMAGE = f"https://raw.githubusercontent.com/tricaman/trica-neon/{font_version}/documentation/images/specimen.png"


def face(file, weight):
    return (f"@font-face {{\n  font-family: \"{FAMILY}\";\n  font-style: normal;\n  font-display: swap;\n"
            f"  font-weight: {weight};\n  src: url(\"./files/{file}\") format(\"woff2\");\n}}\n")


os.makedirs(os.path.join(out, "files"))
shutil.copy(os.path.join(webfonts, "TricaNeon[wght].woff2"), os.path.join(out, "files", f"{NAME}-wght-normal.woff2"))
variable = face(f"{NAME}-wght-normal.woff2", "100 600")
statics = []
for style, wght in WEIGHTS:
    file = f"{NAME}-{wght}-normal.woff2"
    shutil.copy(os.path.join(webfonts, f"TricaNeon-{style}.woff2"), os.path.join(out, "files", file))
    statics.append(face(file, wght))
    open(os.path.join(out, f"{wght}.css"), "w").write(statics[-1])
for name, css in [("index.css", variable), ("variable.css", variable), ("static.css", "\n".join(statics))]:
    open(os.path.join(out, name), "w").write(css)
shutil.copy(license_file, os.path.join(out, "LICENSE"))

package = {
    "name": NAME,
    "version": version,
    "description": f"{FAMILY}, a geometric display typeface drawn with a single stroke: web fonts with ready-made CSS.",
    "keywords": ["font", "typeface", "display", "geometric", "webfont", "woff2", "variable font", "css", NAME],
    "homepage": "https://tricaman.github.io/trica-neon/",
    "repository": {"type": "git", "url": "git+https://github.com/tricaman/trica-neon.git"},
    "bugs": {"url": "https://github.com/tricaman/trica-neon/issues"},
    "license": "OFL-1.1",
    "author": "Marius Trica (https://mariustrica.com)",
    "main": "index.css",
    "style": "index.css",
    "files": ["*.css", "files", "LICENSE", "README.md"],
}
json.dump(package, open(os.path.join(out, "package.json"), "w"), indent=2)
open(os.path.join(out, "package.json"), "a").write("\n")
open(os.path.join(out, "README.md"), "w").write(f"""# {FAMILY}

![{FAMILY} in its six weights, from Thin to SemiBold]({IMAGE})

{FAMILY} is a geometric display typeface drawn with a single, even stroke, like a line of neon tube. It is made
for headlines, titles and logos, for posters, signs and interfaces, and it feels at home in short texts such as
captions, labels and menus.

[Specimen](https://tricaman.github.io/trica-neon/) · [Source on GitHub](https://github.com/tricaman/trica-neon) ·
[Desktop fonts (TTF, OTF)](https://github.com/tricaman/trica-neon/releases/latest)

- Six weights, from Thin (100) to SemiBold (600), and a variable font with every weight in between
- The Google Fonts Latin Core character set, with kerning and mark positioning
- Fractions, superiors, ordinals and tabular figures
- WOFF2 files with ready-made CSS, free under the SIL Open Font License 1.1

## Install

```sh
npm install {NAME}
```

## Use

Import the CSS once, in your main JavaScript or CSS file:

```js
import "{NAME}";            // the variable font: every weight from one file
```

or only the static weights you need:

```js
import "{NAME}/400.css";
import "{NAME}/600.css";
```

Then use the family, with any weight from 100 to 600:

```css
h1 {{
  font-family: "{FAMILY}", sans-serif;
  font-weight: 600;
}}
```

Without a bundler, link the CSS from a CDN that serves npm packages:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/{NAME}@{int(major)}/index.css">
```

## Files

| File | Loads |
| --- | --- |
| `index.css`, `variable.css` | the variable font, weights 100 to 600 |
| `static.css` | the six static weights |
| `100.css` … `600.css` | one static weight each |

## License

{FAMILY} is designed by [Marius Trica](https://mariustrica.com) and licensed under the SIL Open Font License,
Version 1.1 (see `LICENSE`).
""")
print(f"wrote the npm package {NAME}@{version} to {out}")
