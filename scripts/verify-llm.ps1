$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Missing .venv — run: python -m venv .venv; pip install -r backend\requirements.txt"
    exit 1
}
& $python (Join-Path $PSScriptRoot "verify_llm.py")
exit $LASTEXITCODE
