# Build tasks for Trica Neon. `make build` makes every font from scratch, starting from the generator.
# PYTHON falls back to the python.org framework build when python3.13 is not on PATH.
PYTHON ?= $(shell command -v python3.13 || echo /Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13)
GENERATOR = $(wildcard sources/generator/*.py)
VERSION = $(shell $(PYTHON) -c 'import plistlib; i = plistlib.load(open("sources/TricaNeon-Regular.ufo/fontinfo.plist", "rb")); print("%d.%03d" % (i["versionMajor"], i["versionMinor"]))')

.PHONY: venv update sources check-sources build release version clean

venv: venv/touchfile

venv/touchfile: requirements.txt
	test -d venv || $(PYTHON) -m venv venv
	venv/bin/pip install -r requirements.txt
	touch venv/touchfile

# Re-pin every dependency in requirements.txt from requirements.in.
update: venv
	venv/bin/pip install --upgrade pip-tools
	venv/bin/pip-compile --upgrade requirements.in
	venv/bin/pip-sync requirements.txt
	touch venv/touchfile

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

# The zip published with each GitHub release: fonts, license and README.
release: build.stamp
	rm -rf release && mkdir -p release/trica-neon-$(VERSION)
	cp -R fonts OFL.txt README.md release/trica-neon-$(VERSION)/
	cd release && zip -r -q trica-neon-$(VERSION).zip trica-neon-$(VERSION)
	@echo release/trica-neon-$(VERSION).zip

version:
	@echo $(VERSION)

clean:
	rm -rf venv fonts release build.stamp
	find . -name "*.pyc" -delete
