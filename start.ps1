$ErrorActionPreference = "Stop"
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $AppDir ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Privacy Studio non è installato. Esegui prima .\install.ps1."
}
& $Python "$AppDir\scripts\start.py" @args
exit $LASTEXITCODE
