# Trica Neon

Trica Neon is a geometric typeface drawn with a single stroke width. Wide letters fit a square module, outer corners are rounded and inner joints stay sharp.

The project is a work in progress: version 1.000 is not released yet.

## Build

A Python generator in `sources/generator/` draws every glyph from centerline skeletons and writes the UFO sources: one master per weight, from Thin to SemiBold, and `sources/TricaNeon.designspace`. The UFOs are generated files: change the generator, not the UFOs. [gftools builder](https://github.com/googlefonts/gftools) then compiles them as set in `sources/config.yaml`. With Python 3.13 installed:

```sh
make build           # every font from scratch, starting from the generator
make sources         # only regenerate the UFO masters and the designspace
make check-sources   # fail if the UFOs in the repository differ from the generator
make test            # FontBakery with the Google Fonts profile; reports in out/fontbakery
make proof           # HTML proof and PNG specimen in out/proof
make release         # zip of the fonts, the license and this README
```

`make build` writes the variable font to `fonts/variable`, the static fonts to `fonts/ttf` and `fonts/otf` and the WOFF2 web fonts to `fonts/webfonts`. GitHub Actions builds and checks the fonts on every push; a tag such as `v1.000` also publishes a GitHub release with the zip.

## License

Trica Neon is licensed under the SIL Open Font License, Version 1.1. The license is in [OFL.txt](OFL.txt) and is also available with a FAQ at https://openfontlicense.org.
