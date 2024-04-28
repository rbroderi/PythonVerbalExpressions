set ignore-comments
PACKAGE_SLUG := "src/verbex"
export PYTHON_VERSION := if env("CI","false") != "false" { `python --version|cut -d" " -f2` } else { `cat .python-version` }
PYTHON := if env("USE_SYSTEM_PYTHON", "false") != "false" { "python" } else { ".venv/bin/python" }
PYTHON_ENV := if env("USE_SYSTEM_PYTHON", "false") != "false" { "" } else { "sh .venv/bin/activate &&" }
NEWLINE:="$'\n'"
# print list of commands
help:
    @just --list --unsorted
# install into the venv
install:
    @# $(PYTHON_PYENV)
    {{if env("CI","false") != "false" { "" } else { "pyenv install --skip-existing $PYTHON_VERSION "} }}
    @# $(PYTHON_VENV)
    {{ if env("USE_SYSTEM_PYTHON", "false") != "false" { "" } else { "python -m venv .venv" } }}
    @# pip
    {{PYTHON}} -m pip install -e .[dev,optional,docs]

# Install pre-commit
pre-commit_install:
    pre-commit install

# Setup sphynx autodoc
setup_autodoc:
    sphinx-apidoc -f -o docs/source {{PACKAGE_SLUG}}

# copy as template
copy_as_template DEST:
    rsync -r --exclude .mypy_cache --exclude .pytest_cache --exclude .ruff_cache --exclude .tox --exclude .venv --exclude *.egg* --exclude .git ./ {{DEST}}
    cd {{DEST}} && git init . && git commit --allow-empty -m 'Make initial root commit'

# profiling
profile:
    python -m cProfile -s time -o timing.prof tests/timing.py --profile
    snakeviz timing.prof

#
# Formatting
#
# Run all linting and fixes
fixes: validate_pyproject ruff_fixes ruff_format_fixes pylint dapperdata_fixes tomlsort_fixes docs pytest

_fixes_no_ruff: validate_pyproject dapperdata_fixes tomlsort_fixes docs pytest update_dependencies_quiet

# Validate pyproject.toml format
validate_pyproject:
    {{PYTHON}} -m validate_pyproject pyproject.toml

# Run pylint
pylint:
   {{PYTHON}} -m pylint {{PACKAGE_SLUG}}

# Run Ruff and fix
ruff_fixes:
    {{PYTHON}} -m ruff check . --fix

alias black_check := ruff_format_fixes
#Run Ruff format fixes
ruff_format_fixes:
    {{PYTHON}} -m ruff format .

# Run dapperdata fixes
dapperdata_fixes:
    {{PYTHON}} -m dapperdata.cli pretty . --no-dry-run

# Run Tomlsort fixes
tomlsort_fixes:
    {{PYTHON_ENV}} toml-sort `find . -not -path "./.venv/*" -not -path "./.tox/*" -name "*.toml"` -i

# Generate Docs
docs:
    make -C ./docs clean html

#
# Testing
#
# Run all tests
tests: install pytest ruff_check ruff_format_check mypy dapperdata_check tomlsort_check

# Run Pytest
pytest:
    {{PYTHON}} -m pytest --cov=./{{PACKAGE_SLUG}} --cov-report=term-missing tests

# Run Pytest verbose
pytestvv:
    {{PYTHON}} -m pytest -vv --cov=./{{PACKAGE_SLUG}} --cov-report=term-missing tests

# Run pytest show strings
pytest_loud:
    {{PYTHON}} -m pytest -vv -rA --cov=./{{PACKAGE_SLUG}} --cov-report=term-missing tests

# Run ruff in check mode
ruff_check:
    {{PYTHON}} -m ruff check

# Run ruff format in check mode
ruff_format_check:
    {{PYTHON}} -m ruff format . --check

# Run mypy check
mypy:
    {{PYTHON}} -m mypy {{PACKAGE_SLUG}}

# Run dapperdata check
dapperdata_check:
    {{PYTHON}} -m dapperdata.cli pretty .

# Run tomlsort_check
tomlsort_check:
    {{PYTHON_ENV}} toml-sort `find . -not -path "./.venv/*" -not -path "./.tox/*" -name "*.toml"` --check

#
# Dependencies
#

# Rebuild dependencies
rebuild_dependencies:
    {{PYTHON}} -m uv pip compile --output-file=requirements.txt pyproject.toml
    {{PYTHON}} -m uv pip compile --output-file=requirements-dev.txt --extra=dev pyproject.toml
    {{PYTHON}} -m uv pip compile --output-file=requirements-optional.txt --extra=optional pyproject.toml

# Update dependencies
update_dependencies:
    {{PYTHON}} -m uv pip compile --upgrade --output-file=requirements.txt pyproject.toml
    {{PYTHON}} -m uv pip compile --upgrade --output-file=requirements-dev.txt --extra=dev pyproject.toml
    {{PYTHON}} -m uv pip compile --upgrade --output-file=requirements-optional.txt --extra=optional pyproject.toml

update_dependencies_quiet:
    {{PYTHON}} -m uv pip compile --upgrade --output-file=requirements.txt pyproject.toml > /dev/null
    {{PYTHON}} -m uv pip compile --upgrade --output-file=requirements-dev.txt --extra=dev pyproject.toml > /dev/null
    {{PYTHON}} -m uv pip compile --upgrade --output-file=requirements-optional.txt --extra=optional pyproject.toml > /dev/null

#
# Packaging
#

# Build package
build: install
    {{PYTHON}} -m build

# Create Git tag for release
create_tag tag notes="":
    git tag -a v{{tag}} -m "Release {{tag}} "{{NEWLINE}}" {{notes}})"
