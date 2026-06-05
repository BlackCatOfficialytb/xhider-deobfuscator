<#
.SYNOPSIS
  Build the XHider Deobfuscator executable with PyInstaller or Nuitka.

.USAGE
  .\build.ps1 pyinstaller   # -> dist\decbot.exe
  .\build.ps1 nuitka        # -> dist-nuitka\decbot.exe
  .\build.ps1 clean
#>
param(
    [ValidateSet('pyinstaller', 'nuitka', 'clean')]
    [string]$Target = 'pyinstaller'
)

$ErrorActionPreference = 'Stop'
$Py  = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$Pyi = Join-Path $PSScriptRoot '.venv\Scripts\pyinstaller.exe'

if (-not (Test-Path $Py)) {
    throw ".venv not found - create it first: python -m venv .venv; .venv\Scripts\pip install pyinstaller nuitka"
}

switch ($Target) {
    'pyinstaller' {
        & $Pyi --noconfirm main.spec
        Write-Host "`nBuilt: dist\decbot.exe"
    }
    'nuitka' {
        # All flags live in "# nuitka-project:" comments at the top of main.py.
        & $Py -m nuitka main.py
        Write-Host "`nBuilt: dist-nuitka\decbot.exe"
    }
    'clean' {
        'build', 'dist', 'dist-nuitka', 'main.build', 'main.dist', 'main.onefile-build' |
            ForEach-Object { if (Test-Path $_) { Remove-Item -Recurse -Force $_ } }
        Write-Host 'Cleaned build output.'
    }
}
