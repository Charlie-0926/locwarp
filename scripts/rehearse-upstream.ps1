param(
    [string]$CustomBranch = 'custom/main',
    [string]$UpstreamRef = 'upstream/main',
    [switch]$SkipFetch
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $repoRoot
try {
    if (-not (git rev-parse --is-inside-work-tree 2>$null)) {
        throw 'This directory is not a Git repository.'
    }
    if (-not $SkipFetch) {
        git fetch upstream --tags --prune
        if ($LASTEXITCODE -ne 0) { throw 'Unable to fetch upstream.' }
    }

    git rev-parse --verify $CustomBranch 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Missing branch: $CustomBranch" }
    git rev-parse --verify $UpstreamRef 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Missing ref: $UpstreamRef" }

    $output = git merge-tree --write-tree $CustomBranch $UpstreamRef 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Upstream rehearsal found merge conflicts:' -ForegroundColor Yellow
        $output | ForEach-Object { Write-Host $_ }
        exit 1
    }

    $customSha = git rev-parse --short $CustomBranch
    $upstreamSha = git rev-parse --short $UpstreamRef
    Write-Host "Rehearsal passed: $CustomBranch ($customSha) + $UpstreamRef ($upstreamSha)" -ForegroundColor Green
}
finally {
    Pop-Location
}
