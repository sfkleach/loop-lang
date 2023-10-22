################################################################################
### Standard Makefile intro
################################################################################

# Important check
MAKEFLAGS+=--warn-undefined-variables

# Causes the commands in a recipe to be issued in the same shell (beware cd commands not executed in a subshell!)
.ONESHELL:
SHELL:=/bin/bash

# When using ONESHELL, we want to exit on error (-e) and error if a command fails in a pipe (-o pipefail)
# When overriding .SHELLFLAGS one must always add a tailing `-c` as this is the default setting of Make.
.SHELLFLAGS:=-e -o pipefail -c

# Invoke the all target when no target is explicitly specified.
.DEFAULT_GOAL:=help

# Delete targets if their recipe exits with a non-zero exit code.
.DELETE_ON_ERROR:


################################################################################
### Main Contents
################################################################################

.PHONY: help
help:
	# Valid targets are:
	#	clean           - removes artefacts
	#	test 			- runs the unit tests
	#	build	 		- build looplang.pyz

# Changes to the way poetry is implemented appears to require an explicit
# look-up for the poetry command to run inside this makefile.
POETRY=$(shell command -v poetry)

.PHONY: clean
clean:
	rm -rf _build

.PHONY: build
build:
	mkdir -p _build/
	(cd src; tar cf - looplang) | (cd _build; tar xf -)
	$(POETRY) export > _build/requirements.txt
	$(POETRY) run python -m pip install -r _build/requirements.txt --target _build/looplang
	$(POETRY) run python -m zipapp -p "/usr/bin/env python" _build/looplang -o _build/looplang.pyz

.PHONY: test
test:
	$(POETRY) run mypy src/looplang/__main__.py --check-untyped-defs
	$(POETRY) run pytest tests
