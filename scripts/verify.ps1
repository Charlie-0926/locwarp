param(
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Invoke-Checked {
    param([string]$Label, [scriptblock]$Command)
    Write-Host "`n== $Label ==" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

Push-Location $repoRoot
try {
    Invoke-Checked 'Backend Pyright' { npx.cmd --yes pyright backend }
    Invoke-Checked 'Electron syntax' { node --check frontend/electron/main.js }

    Push-Location (Join-Path $repoRoot 'frontend')
    try {
        Invoke-Checked 'Frontend TypeScript' { npx.cmd tsc --noEmit }
        if (-not $SkipBuild) {
            Invoke-Checked 'Frontend production build' { npm.cmd run build }
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    Pop-Location
}

Write-Host "`nAll verification checks passed." -ForegroundColor Green
