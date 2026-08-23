[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PackageRoot,
    [Parameter(Mandatory=$true)][string]$FixtureRoot,
    [Parameter(Mandatory=$true)][string]$OutputReport
)
$ErrorActionPreference = 'Stop'
function Get-Full([string]$Path) { return [IO.Path]::GetFullPath($Path) }
function Get-Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
$PackageRoot = Get-Full $PackageRoot
$FixtureRoot = Get-Full $FixtureRoot
$OutputReport = Get-Full $OutputReport
if (Test-Path -LiteralPath $FixtureRoot) {
    $resolved = Get-Full $FixtureRoot
    $workspace = Get-Full (Join-Path $PSScriptRoot '..\..')
    if (-not $resolved.StartsWith($workspace + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "안전하지 않은 fixture 경로: $resolved"
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $FixtureRoot | Out-Null
$dolphinUser = Join-Path $FixtureRoot 'Dolphin 사용자 폴더'
$load = Join-Path $dolphinUser 'Load'
New-Item -ItemType Directory -Force -Path $load | Out-Null
$install = Join-Path $PackageRoot 'Install-ARF-KO.ps1'
$manifestPath = Join-Path $PackageRoot 'MANIFEST.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$overlayEntries = @($manifest.files | Where-Object {$_.role -eq 'riivolution_overlay'})
$checks = @()

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $install -TargetRoot $dolphinUser -NonInteractive -SkipDolphinCheck
$checks += [pscustomobject]@{ name='one_click_noninteractive_install'; passed=($LASTEXITCODE -eq 0) }
$missing = @()
$mismatched = @()
foreach ($entry in $overlayEntries) {
    $relative = ([string]$entry.path).Substring('payload/riivolution_sd/'.Length)
    $target = Join-Path $load $relative.Replace('/','\')
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { $missing += $relative; continue }
    if ((Get-Hash $target) -ne ([string]$entry.sha256).ToUpperInvariant()) { $mismatched += $relative }
}
$checks += [pscustomobject]@{
    name='installed_payload_matches_manifest'
    passed=($missing.Count -eq 0 -and $mismatched.Count -eq 0)
    missing_count=$missing.Count
    mismatched_count=$mismatched.Count
}

# 업데이트 시 우리 패치 폴더의 오래된 파일은 제거하고 다른 Riivolution 파일은 보존해야 한다.
$stale = Join-Path $load 'arc_rise_fantasia_ko_full\stale-file.bin'
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $stale) | Out-Null
[IO.File]::WriteAllBytes($stale, [byte[]](1,2,3,4))
$otherXml = Join-Path $load 'riivolution\other_patch.xml'
[IO.File]::WriteAllText($otherXml, '<wiidisc />')
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $install -TargetRoot $load -NonInteractive -SkipDolphinCheck
$checks += [pscustomobject]@{
    name='repeat_install_replaces_only_own_patch'
    passed=($LASTEXITCODE -eq 0 -and -not (Test-Path -LiteralPath $stale) -and (Test-Path -LiteralPath $otherXml -PathType Leaf))
}

# 변조된 패키지는 Load 폴더에 쓰기 전에 거부해야 한다.
$tampered = Join-Path $FixtureRoot 'tampered package'
Copy-Item -LiteralPath $PackageRoot -Destination $tampered -Recurse
$tamperedRoot = Join-Path $tampered (Split-Path -Leaf $PackageRoot)
if (-not (Test-Path -LiteralPath $tamperedRoot)) { $tamperedRoot = $tampered }
$tamperFile = Get-ChildItem -LiteralPath (Join-Path $tamperedRoot 'payload\riivolution_sd') -Recurse -File | Select-Object -First 1
[IO.File]::AppendAllText($tamperFile.FullName, 'tamper')
$tamperUser = Join-Path $FixtureRoot 'tamper Dolphin user'
New-Item -ItemType Directory -Force -Path $tamperUser | Out-Null
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tamperedRoot 'Install-ARF-KO.ps1') -TargetRoot $tamperUser -NonInteractive -SkipDolphinCheck
$tamperWrites = @(Get-ChildItem -LiteralPath (Join-Path $tamperUser 'Load') -Recurse -File -ErrorAction SilentlyContinue).Count
$checks += [pscustomobject]@{
    name='tampered_payload_rejected_before_target_write'
    passed=($LASTEXITCODE -ne 0 -and $tamperWrites -eq 0)
    target_files=$tamperWrites
}

$report = [ordered]@{
    schema='arf-ko-one-click-installer-fixture-v1'
    package_root=$PackageRoot
    package_manifest_sha256=(Get-Hash $manifestPath)
    package_manifest_size_bytes=(Get-Item -LiteralPath $manifestPath).Length
    overlay_file_count=$overlayEntries.Count
    checks=@($checks)
    passed_count=@($checks | Where-Object {$_.passed}).Count
    failed_count=@($checks | Where-Object {-not $_.passed}).Count
    valid=(@($checks | Where-Object {-not $_.passed}).Count -eq 0)
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputReport) | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputReport -Encoding UTF8
if (-not $report.valid) { throw "원클릭 설치기 fixture 실패: $($report.failed_count)건" }
$report | ConvertTo-Json -Depth 8
