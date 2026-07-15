param(
    [string]$CustomBranch = 'custom/main',
    [string]$UpstreamRef = 'upstream/main',
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $repoRoot
try {
    $currentBranch = git branch --show-current
    if ($currentBranch -ne $CustomBranch) {
        throw "Run this script from $CustomBranch (current: $currentBranch)."
    }
    if (git status --porcelain) {
        throw 'Working tree is not clean. Commit or stash changes before syncing.'
    }
    git remote get-url upstream 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Missing upstream remote.' }

    git fetch upstream --tags --prune
    if ($LASTEXITCODE -ne 0) { throw 'Unable to fetch upstream.' }

    # main is a read-only local mirror of the official branch.
    git branch --force main $UpstreamRef
    if ($LASTEXITCODE -ne 0) { throw 'Unable to update the local main mirror.' }

    $tag = git describe --tags --abbrev=0 $UpstreamRef 2>$null
    if (-not $tag) { $tag = (git rev-parse --short $UpstreamRef) }
    $safeTag = $tag -replace '[^A-Za-z0-9._-]', '-'
    $syncBranch = "sync/upstream-$safeTag"
    if (git show-ref --verify --quiet "refs/heads/$syncBranch") {
        $syncBranch = "$syncBranch-$(Get-Date -Format yyyyMMdd-HHmmss)"
    }

    git switch --create $syncBranch
    if ($LASTEXITCODE -ne 0) { throw "Unable to create $syncBranch." }

    git merge --no-ff --no-edit $UpstreamRef
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nMerge conflicts remain on $syncBranch." -ForegroundColor Yellow
        git diff --name-only --diff-filter=U
        Write-Host 'Resolve them, run scripts/verify.ps1, commit, then fast-forward custom/main.'
        exit 1
    }

    & (Join-Path $PSScriptRoot 'verify.ps1') -SkipBuild:$SkipBuild
    if ($LASTEXITCODE -ne 0) { throw 'Verification failed.' }

    Write-Host "`nSync branch is ready: $syncBranch" -ForegroundColor Green
    Write-Host "Review it, then run:"
    Write-Host "  git switch $CustomBranch"
    Write-Host "  git merge --ff-only $syncBranch"
}
finally {
    Pop-Location
}
