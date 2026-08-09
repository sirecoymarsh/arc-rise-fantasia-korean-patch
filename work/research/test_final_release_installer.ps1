[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PackageRoot,
    [Parameter(Mandatory=$true)][string]$SourceRvz,
    [Parameter(Mandatory=$true)][string]$FixtureRoot,
    [Parameter(Mandatory=$true)][string]$OutputReport
)
$ErrorActionPreference = 'Stop'
function Get-Full([string]$Path) { return [IO.Path]::GetFullPath($Path) }
function Get-Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
$PackageRoot = Get-Full $PackageRoot
$SourceRvz = Get-Full $SourceRvz
$FixtureRoot = Get-Full $FixtureRoot
$OutputReport = Get-Full $OutputReport
if (Test-Path -LiteralPath $FixtureRoot) {
    $resolved = Get-Full $FixtureRoot
    $workspace = Get-Full (Join-Path $PSScriptRoot '..\..')
    if (-not $resolved.StartsWith($workspace + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "안전하지 않은 fixture 경로: $resolved" }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $FixtureRoot | Out-Null
$target = Join-Path $FixtureRoot 'target with 한글'
$state = Join-Path $FixtureRoot 'state with 한글'
New-Item -ItemType Directory -Force -Path $target,$state | Out-Null
$install = Join-Path $PackageRoot 'Install-ARF-KO.ps1'
$verify = Join-Path $PackageRoot 'Verify-ARF-KO.ps1'
$restore = Join-Path $PackageRoot 'Restore-ARF-KO.ps1'
$manifest = Join-Path $PackageRoot 'MANIFEST.json'
if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) { throw "패키지 MANIFEST.json이 없습니다: $manifest" }
$checks = @()

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $install -SourceRvz $SourceRvz -TargetRoot $target -StateRoot $state
$checks += [pscustomobject]@{ name='pristine_install'; passed=($LASTEXITCODE -eq 0) }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $verify -StateRoot $state
$checks += [pscustomobject]@{ name='installed_hash_verification'; passed=($LASTEXITCODE -eq 0) }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $restore -StateRoot $state
$checks += [pscustomobject]@{ name='byte_exact_restore'; passed=($LASTEXITCODE -eq 0) }
$leftovers = @(Get-ChildItem -LiteralPath $target -Recurse -File -ErrorAction SilentlyContinue)
$checks += [pscustomobject]@{ name='restored_target_has_no_added_files'; passed=($leftovers.Count -eq 0); count=$leftovers.Count }

# Package tamper must fail before writing target/state.
$tampered = Join-Path $FixtureRoot 'tampered package'
Copy-Item -LiteralPath $PackageRoot -Destination $tampered -Recurse
$tamperedRoot = Join-Path $tampered (Split-Path -Leaf $PackageRoot)
if (-not (Test-Path -LiteralPath $tamperedRoot)) { $tamperedRoot = $tampered }
$tamperFile = Get-ChildItem -LiteralPath (Join-Path $tamperedRoot 'payload\riivolution_sd') -Recurse -File | Select-Object -First 1
[IO.File]::AppendAllText($tamperFile.FullName, 'tamper')
$tamperTarget = Join-Path $FixtureRoot 'tamper-target'
$tamperState = Join-Path $FixtureRoot 'tamper-state'
New-Item -ItemType Directory -Force -Path $tamperTarget,$tamperState | Out-Null
$tamperFailed = $false
try {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tamperedRoot 'Install-ARF-KO.ps1') -SourceRvz $SourceRvz -TargetRoot $tamperTarget -StateRoot $tamperState
    $tamperFailed = ($LASTEXITCODE -ne 0)
} catch { $tamperFailed = $true }
$tamperWrites = @(Get-ChildItem -LiteralPath $tamperTarget -Recurse -File -ErrorAction SilentlyContinue).Count
$checks += [pscustomobject]@{ name='tampered_payload_rejected_before_target_write'; passed=($tamperFailed -and $tamperWrites -eq 0); target_files=$tamperWrites }

$report = [ordered]@{
    schema='arf-ko-installer-fixture-v1'
    package_root=$PackageRoot
    package_manifest_sha256=(Get-Hash $manifest)
    package_manifest_size_bytes=(Get-Item -LiteralPath $manifest).Length
    source_rvz_sha256=(Get-Hash $SourceRvz)
    checks=@($checks)
    passed_count=@($checks | Where-Object {$_.passed}).Count
    failed_count=@($checks | Where-Object {-not $_.passed}).Count
    valid=(@($checks | Where-Object {-not $_.passed}).Count -eq 0)
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputReport) | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputReport -Encoding UTF8
if (-not $report.valid) { throw "설치기 fixture 실패: $($report.failed_count)건" }
$report | ConvertTo-Json -Depth 8
