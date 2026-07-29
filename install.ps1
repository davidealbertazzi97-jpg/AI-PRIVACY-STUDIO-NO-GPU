$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$UvVersion = "0.11.16"
$UvAsset = "uv-x86_64-pc-windows-msvc.zip"
$UvSha256 = "dd9d6d6554bfab265bfa98aa8e8a406c5c3a7b97582f93de1f4d48d9154a0395"

if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -ne "X64") {
    throw "Il profilo completo supporta Windows x86-64."
}

$UvDir = Join-Path $AppDir ".tools\uv"
$UvExe = Join-Path $UvDir "uv.exe"
if (-not (Test-Path $UvExe)) {
    $Temporary = Join-Path ([System.IO.Path]::GetTempPath()) (
        "privacy-studio-uv-" + [System.Guid]::NewGuid().ToString("N")
    )
    New-Item -ItemType Directory -Path $Temporary | Out-Null
    try {
        $Archive = Join-Path $Temporary $UvAsset
        $Url = "https://github.com/astral-sh/uv/releases/download/$UvVersion/$UvAsset"
        Write-Host "Scarico uv $UvVersion e verifico SHA-256..."
        Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Archive
        $Actual = (Get-FileHash -Algorithm SHA256 $Archive).Hash.ToLowerInvariant()
        if ($Actual -ne $UvSha256) {
            throw "Checksum uv non valido: $Actual"
        }
        $Expanded = Join-Path $Temporary "expanded"
        Expand-Archive -Path $Archive -DestinationPath $Expanded
        $DownloadedUv = Get-ChildItem -Path $Expanded -Filter "uv.exe" -Recurse |
            Select-Object -First 1
        if ($null -eq $DownloadedUv) {
            throw "uv.exe non trovato nell'archivio verificato."
        }
        New-Item -ItemType Directory -Force -Path $UvDir | Out-Null
        Copy-Item $DownloadedUv.FullName $UvExe
    }
    finally {
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $Temporary
    }
}

& $UvExe python install 3.12
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$env:PRIVACY_STUDIO_UV = $UvExe
& $UvExe run --isolated --no-project --python 3.12 `
    "$AppDir\scripts\bootstrap.py" @args
exit $LASTEXITCODE
