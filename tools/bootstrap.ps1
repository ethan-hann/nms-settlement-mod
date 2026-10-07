# Fetches the pinned tools listed in tools.lock.json into gitignored folders.
# Safe to rerun: files that already match their pinned hash are left alone.
$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$lock = Get-Content -Raw (Join-Path $PSScriptRoot 'tools.lock.json') | ConvertFrom-Json

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw 'uv is required (https://docs.astral.sh/uv/). Install it, then rerun this script.'
}

# Python venv with pinned packages.
$venv = Join-Path $repo $lock.python.venv
$python = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $python)) {
    uv venv --python $lock.python.version $venv
    if ($LASTEXITCODE -ne 0) { throw 'uv venv failed' }
}
$specs = $lock.python.packages.PSObject.Properties | ForEach-Object { "$($_.Name)==$($_.Value)" }
uv pip install --python $python @specs
if ($LASTEXITCODE -ne 0) { throw 'uv pip install failed' }

# MBINCompiler release files, verified against pinned hashes.
$mbinDir = Join-Path $repo $lock.mbincompiler.dir
New-Item -ItemType Directory -Force $mbinDir | Out-Null
foreach ($entry in $lock.mbincompiler.files.PSObject.Properties) {
    $target = Join-Path $mbinDir $entry.Name
    $want = $entry.Value.sha256
    if ((Test-Path $target) -and ((Get-FileHash -Algorithm SHA256 $target).Hash -eq $want)) {
        continue
    }
    $tmp = "$target.download"
    Invoke-WebRequest -Uri $entry.Value.url -OutFile $tmp -UseBasicParsing
    $got = (Get-FileHash -Algorithm SHA256 $tmp).Hash
    if ($got -ne $want) {
        Remove-Item $tmp
        throw "Hash mismatch for $($entry.Name): expected $want, got $got"
    }
    Move-Item -Force $tmp $target
}

Write-Host "Bootstrap complete: MBINCompiler $($lock.mbincompiler.version), Python packages: $($specs -join ', ')"
