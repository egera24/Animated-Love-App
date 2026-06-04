$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root ".venv\Scripts\python.exe"
& $python (Join-Path $PSScriptRoot "clear_bubble_cache.py")
