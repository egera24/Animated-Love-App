# Interactive: add Groq, Gemini, OpenRouter keys to .env (does not print keys back).
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$envFile = Join-Path $root ".env"

if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root ".env.example") $envFile
    Write-Host "Created .env from .env.example"
}

Write-Host ""
Write-Host "Get free API keys (paste when prompted; input is hidden):"
Write-Host "  Groq:       https://console.groq.com"
Write-Host "  Gemini:     https://aistudio.google.com/apikey"
Write-Host "  OpenRouter: https://openrouter.ai/keys"
Write-Host ""

function Read-Secret([string]$label) {
    $sec = Read-Host "$label (Enter to skip)" -AsSecureString
    if ($sec.Length -eq 0) { return $null }
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

$groq = Read-Secret "GROQ_API_KEY"
$gemini = Read-Secret "GEMINI_API_KEY"
$openrouter = Read-Secret "OPENROUTER_API_KEY"

if (-not $groq -and -not $gemini -and -not $openrouter) {
    Write-Host "No keys entered. Exiting without changes."
    exit 1
}

$content = Get-Content $envFile -Raw

function Set-EnvVar([string]$name, [string]$value) {
    global:content
    $escaped = $value -replace '\\', '\\\\'
    if ($content -match "(?m)^$name=.*$") {
        $content = $content -replace "(?m)^$name=.*$", "$name=$escaped"
    } else {
        $content = $content.TrimEnd() + "`n$name=$escaped`n"
    }
}

if ($groq) { Set-EnvVar "GROQ_API_KEY" $groq }
if ($gemini) { Set-EnvVar "GEMINI_API_KEY" $gemini }
if ($openrouter) { Set-EnvVar "OPENROUTER_API_KEY" $openrouter }

$defaults = @{
    "LLM_DAILY_CALL_LIMIT" = "50"
    "LLM_CHAT_DAILY_CALL_LIMIT" = "300"
    "ENABLE_SCHEDULER" = "true"
}
foreach ($k in $defaults.Keys) {
    if ($content -notmatch "(?m)^$k=") {
        $content = $content.TrimEnd() + "`n$k=$($defaults[$k])`n"
    }
}

if ($content -notmatch "(?m)^PREFETCH_SECRET=") {
    $prefetch = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
    $content = $content.TrimEnd() + "`nPREFETCH_SECRET=$prefetch`n"
    Write-Host "Generated PREFETCH_SECRET (saved to .env)"
}

Set-Content -Path $envFile -Value $content.TrimEnd() -NoNewline -Encoding utf8
Write-Host ""
Write-Host "Saved. Restart backend: .\scripts\start-backend.ps1"
Write-Host "Model fallback order: config\llm_models.yaml (see llm_models.example.yaml)"
Write-Host "Then: .\scripts\clear-bubble-cache.ps1"
Write-Host "Then: .\scripts\verify-llm.ps1"
