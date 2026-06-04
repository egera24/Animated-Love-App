Set-Location $PSScriptRoot\..
.\.venv\Scripts\Activate.ps1
Set-Location backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
