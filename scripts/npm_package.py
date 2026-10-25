"""Assemble the npm package, in the style of Fontsource: the WOFF2 files and ready-made CSS.
index.css loads the variable font (every weight from one file); 100.css to 600.css load one
static weight each and static.css all of them.
usage: python -I npm_package.py <webfonts folder> <OFL.txt> <font version> <output folder>"""
import json, os, shutil, sys

webfonts, license_file, font_version, out = sys.argv[1:5]
NAME, FAMILY = "trica-neon", "Trica Neon"
WEIGHTS = [("Thin", 100), ("ExtraLight", 200), ("Light", 300), ("Regular", 400), ("Medium", 500), ("SemiBold", 600)]
major, minor = font_version.split(".")
version = f"{int(major)}.{int(minor)}.0"                 # font version 1.000 -> package version 1.0.0


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
    "description": f"{FAMILY}, a geometric typeface drawn with a single stroke: web fonts with ready-made CSS.",
    "keywords": ["font", "typeface", "webfont", "woff2", "variable font", "css", NAME],
    "homepage": "https://tricaman.github.io/trica-neon/",
    "repository": {"type": "git", "url": "git+https://github.com/tricaman/trica-neon.git"},
    "license": "OFL-1.1",
    "author": "Marius Trica (https://mariustrica.com)",
    "main": "index.css",
    "style": "index.css",
    "files": ["*.css", "files", "LICENSE", "README.md"],
}
json.dump(package, open(os.path.join(out, "package.json"), "w"), indent=2)
open(os.path.join(out, "package.json"), "a").write("\n")
open(os.path.join(out, "README.md"), "w").write(f"""# {FAMILY}

Web fonts of [{FAMILY}](https://github.com/tricaman/trica-neon), a geometric typeface drawn with a single
stroke, in six weights from Thin (100) to SemiBold (600), with ready-made CSS.

```sh
npm install {NAME}
```

Import the CSS once, for example in your main JavaScript or CSS file:

```js
import "{NAME}";            // the variable font: every weight from one file
// or single static weights
import "{NAME}/400.css";
import "{NAME}/600.css";
```

Then use the family:

```css
body {{
  font-family: "{FAMILY}", sans-serif;
}}
```

{FAMILY} is licensed under the SIL Open Font License, Version 1.1 (see LICENSE).
""")
print(f"wrote the npm package {NAME}@{version} to {out}")
