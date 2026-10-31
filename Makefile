# Build tasks for Trica Neon. `make build` makes every font from scratch, starting from the generator.
# PYTHON falls back to the python.org framework build when python3.13 is not on PATH.
PYTHON ?= $(shell command -v python3.13 || echo /Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13)
GENERATOR = $(wildcard sources/generator/*.py)
STYLES = Thin ExtraLight Light Regular Medium SemiBold
VERSION = $(shell $(PYTHON) -c 'import plistlib; i = plistlib.load(open("sources/TricaNeon-Regular.ufo/fontinfo.plist", "rb")); print("%d.%03d" % (i["versionMajor"], i["versionMinor"]))')

.PHONY: venv venv-test update sources check-sources build test proof specimen images npm release version clean

# venv holds the build tools, venv-test the QA tools: FontBakery's googlefonts
# profile needs protobuf<4, gftools needs protobuf>=6.33.
venv: venv/touchfile

venv-test: venv-test/touchfile

venv/touchfile: requirements.txt
	test -d venv || $(PYTHON) -m venv venv
	venv/bin/pip install -r requirements.txt
	touch venv/touchfile

venv-test/touchfile: requirements-test.txt
	test -d venv-test || $(PYTHON) -m venv venv-test
	venv-test/bin/pip install -r requirements-test.txt
	touch venv-test/touchfile

# Re-pin every dependency in requirements*.txt from requirements*.in.
update: venv venv-test
	venv/bin/pip install --upgrade pip-tools
	venv/bin/pip-compile --upgrade requirements.in
	venv/bin/pip-sync requirements.txt
	venv-test/bin/pip install --upgrade pip-tools
	venv-test/bin/pip-compile --upgrade requirements-test.in
	venv-test/bin/pip-sync requirements-test.txt
	touch venv/touchfile venv-test/touchfile

# Regenerate the UFO masters and the designspace from the generator.
sources: venv
	venv/bin/python sources/generator/make_sources.py

# Fail if the sources in the repository differ from what the generator produces.
check-sources: venv
	venv/bin/python sources/generator/make_sources.py --check

# Every font from scratch: the UFO sources from the generator, then gftools builder
# (sources/config.yaml) writes the variable font, static TTF and OTF and WOFF2 into fonts/.
build: build.stamp

build.stamp: venv/touchfile sources/config.yaml $(GENERATOR)
	venv/bin/python sources/generator/make_sources.py
	rm -rf fonts
	. venv/bin/activate && gftools builder sources/config.yaml
	touch build.stamp

# FontBakery (googlefonts profile) on the variable font, the one Google Fonts publishes,
# and on the static TTFs. Reports in out/fontbakery; fails if any check FAILs.
test: build.stamp venv-test/touchfile
	rm -rf out/fontbakery && mkdir -p out/fontbakery
	status=0; \
	venv-test/bin/fontbakery check-googlefonts -l WARN --succinct --full-lists \
		--html out/fontbakery/variable.html --ghmarkdown out/fontbakery/variable.md fonts/variable/*.ttf || status=1; \
	venv-test/bin/fontbakery check-googlefonts -l WARN --succinct --full-lists \
		--html out/fontbakery/static.html --ghmarkdown out/fontbakery/static.md fonts/ttf/*.ttf || status=1; \
	exit $$status

# Proofs in out/proof: an HTML page with every glyph and sample texts (diffenator3)
# and a PNG specimen of the six weights.
proof: build.stamp
	rm -rf out/proof && mkdir -p out/proof
	venv/bin/diff3proof fonts/variable/*.ttf --output out/proof
	venv/bin/python scripts/render_labeled.py out/proof/specimen.png 40 scripts/specimen.txt \
		$(foreach s,$(STYLES),"$(s)::fonts/ttf/TricaNeon-$(s).ttf")

# The specimen page in out/specimen, ready for GitHub Pages or any static host: the template in
# documentation/specimen with the characters of the font, and the variable web font.
specimen: build.stamp
	rm -rf out/specimen
	venv/bin/python scripts/specimen_page.py documentation/specimen/index.html \
		"fonts/variable/TricaNeon[wght].ttf" "fonts/webfonts/TricaNeon[wght].woff2" out/specimen

# The specimen images of the README in documentation/images.
images: build.stamp
	venv/bin/python scripts/specimen_images.py "fonts/variable/TricaNeon[wght].ttf" documentation/images

# The npm package in out/npm: the WOFF2 files with ready-made CSS. It is published by hand,
# with `npm publish ./out/npm`; a new package of the same fonts (a better README, say) takes
# the next revision: `make npm NPM_REVISION=1`.
NPM_REVISION ?= 0
npm: build.stamp
	rm -rf out/npm
	venv/bin/python scripts/npm_package.py fonts/webfonts OFL.txt $(VERSION) out/npm $(NPM_REVISION)

# The zip published with each GitHub release: fonts, license and README.
release: build.stamp
	rm -rf release && mkdir -p release/trica-neon-$(VERSION)
	cp -R fonts OFL.txt README.md release/trica-neon-$(VERSION)/
	cd release && zip -r -q trica-neon-$(VERSION).zip trica-neon-$(VERSION)
	@echo release/trica-neon-$(VERSION).zip

version:
	@echo $(VERSION)

clean:
	rm -rf venv venv-test fonts out release build.stamp
	find . -name "*.pyc" -delete
