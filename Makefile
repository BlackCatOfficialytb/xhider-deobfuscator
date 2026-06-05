# Build rules for the XHider Deobfuscator (main.py)
# Requires the project venv at .venv (pyinstaller + nuitka already installed there).
# On Windows without GNU make, use build.ps1 instead (same targets).

PY      := .venv/Scripts/python.exe
PYI     := .venv/Scripts/pyinstaller.exe
NAME    := decbot
ENTRY   := main.py

.PHONY: all pyinstaller nuitka clean

all: pyinstaller

# --- PyInstaller (output: dist/decbot.exe) -----------------------------------
pyinstaller:
	$(PYI) --noconfirm main.spec

# --- Nuitka (output: dist-nuitka/decbot.exe) ----------------------------------
# All flags live in "# nuitka-project:" comments at the top of main.py.
nuitka:
	$(PY) -m nuitka $(ENTRY)

clean:
	-rm -rf build dist dist-nuitka main.build main.dist main.onefile-build
