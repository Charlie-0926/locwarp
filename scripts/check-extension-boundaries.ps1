$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$forbidden = @(
    @{ Path = 'backend/services/geo_extras.py'; Pattern = 'def optimize_order_2opt' },
    @{ Path = 'frontend/src/services/api.ts'; Pattern = 'applyJumpSettings' },
    @{ Path = 'frontend/src/services/api.ts'; Pattern = 'routeOptimize' },
    @{ Path = 'backend/core/multi_stop.py'; Pattern = 'math\.sqrt\(random\.random\(\)\)' }
)

$failed = $false
foreach ($rule in $forbidden) {
    $path = Join-Path $repoRoot $rule.Path
    if (Select-String -LiteralPath $path -Pattern $rule.Pattern -Quiet) {
        Write-Error "Extension boundary regression: $($rule.Pattern) found in $($rule.Path)"
        $failed = $true
    }
}

$required = @(
    'backend/extensions/custom/jump_random_walk/policy.py',
    'backend/extensions/custom/route_optimizer/two_opt.py',
    'backend/extensions/custom/multi_device/coordinator.py',
    'frontend/src/extensions/custom/jumpRandomWalk/index.ts',
    'frontend/src/extensions/custom/routeOptimizer/index.ts',
    'frontend/src/extensions/custom/multiDevice/index.ts'
)
foreach ($relativePath in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $relativePath))) {
        Write-Error "Required extension module is missing: $relativePath"
        $failed = $true
    }
}

if ($failed) { exit 1 }
Write-Host 'Extension boundaries passed.' -ForegroundColor Green
