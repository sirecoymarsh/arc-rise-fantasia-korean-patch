[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SourceRvz,
    [Parameter(Mandatory=$true)][string]$TargetRoot,
    [string]$StateRoot = (Join-Path $env:LOCALAPPDATA 'ArcRiseFantasiaKO')
)
$ErrorActionPreference = 'Stop'
$ExpectedSource = '4671E3E74EB664E441FA927FF6BE9FC06B7D4860782BC4CECCF7DBBB4108AAC5'
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PayloadRoot = Join-Path $PackageRoot 'payload\riivolution_sd'
$ManifestPath = Join-Path $PackageRoot 'MANIFEST.json'

function Get-Full([string]$Path) { return [IO.Path]::GetFullPath($Path) }
function Get-Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Read-Utf8Json([string]$Path) { return (Get-Content -LiteralPath $Path -Encoding UTF8 -Raw | ConvertFrom-Json) }

$SourceRvz = Get-Full $SourceRvz
$TargetRoot = Get-Full $TargetRoot
$StateRoot = Get-Full $StateRoot
$PackageRoot = Get-Full $PackageRoot
if (-not (Test-Path -LiteralPath $SourceRvz -PathType Leaf)) { throw "원본 RVZ를 찾을 수 없습니다: $SourceRvz" }
if ((Get-Hash $SourceRvz) -ne $ExpectedSource) { throw '지원하지 않는 원본 RVZ 해시입니다.' }
$manifest = Read-Utf8Json $ManifestPath
if ($manifest.game_id -ne 'RPJJ99' -or $manifest.source_rvz_sha256 -ne $ExpectedSource) { throw '패키지 매니페스트가 대상 원본과 일치하지 않습니다.' }
if ($manifest.translation_engine_policy -ne 'Codex internal models only' -or $manifest.external_translation_models_or_apis_used -ne $false) { throw '번역 출처 정책이 일치하지 않습니다.' }

$payloadEntries = @($manifest.files | Where-Object { $_.role -eq 'riivolution_overlay' })
if ($payloadEntries.Count -ne [int]$manifest.overlay_file_count) { throw '오버레이 파일 수가 매니페스트와 다릅니다.' }
foreach ($entry in $manifest.files) {
    $candidate = Get-Full (Join-Path $PackageRoot ([string]$entry.path).Replace('/','\'))
    if (-not $candidate.StartsWith($PackageRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "패키지 경로 탈출: $($entry.path)" }
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { throw "패키지 파일 누락: $($entry.path)" }
    if ((Get-Hash $candidate) -ne ([string]$entry.sha256).ToUpperInvariant()) { throw "패키지 해시 불일치: $($entry.path)" }
}

New-Item -ItemType Directory -Force -Path $TargetRoot,$StateRoot | Out-Null
$backupRoot = Join-Path $StateRoot ('backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$journalPath = Join-Path $StateRoot 'in_progress.json'
$statePath = Join-Path $StateRoot 'state.json'
if (Test-Path -LiteralPath $statePath) { throw "이미 설치 상태가 존재합니다. 먼저 복원하십시오: $statePath" }
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
$records = @()
foreach ($entry in $payloadEntries) {
    $relative = ([string]$entry.path).Substring('payload/riivolution_sd/'.Length)
    $source = Get-Full (Join-Path $PayloadRoot $relative.Replace('/','\'))
    $target = Get-Full (Join-Path $TargetRoot $relative.Replace('/','\'))
    if (-not $target.StartsWith($TargetRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "대상 경로 탈출: $relative" }
    $record = [ordered]@{ relative=$relative; installed_sha256=([string]$entry.sha256).ToUpperInvariant(); existed=$false; original_sha256=$null; backup=$null }
    if (Test-Path -LiteralPath $target -PathType Leaf) {
        $record.existed = $true
        $record.original_sha256 = Get-Hash $target
        $backup = Get-Full (Join-Path $backupRoot $relative.Replace('/','\'))
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backup) | Out-Null
        Copy-Item -LiteralPath $target -Destination $backup -Force
        if ((Get-Hash $backup) -ne $record.original_sha256) { throw "백업 확인 실패: $relative" }
        $record.backup = $backup
    }
    $records += [pscustomobject]$record
}
$journal = [ordered]@{ schema='arf-ko-install-journal-v1'; status='in_progress'; target_root=$TargetRoot; backup_root=$backupRoot; records=@($records) }
$journal | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $journalPath -Encoding UTF8

$installed = @()
try {
    foreach ($record in $records) {
        $source = Get-Full (Join-Path $PayloadRoot $record.relative.Replace('/','\'))
        $target = Get-Full (Join-Path $TargetRoot $record.relative.Replace('/','\'))
        $parent = Split-Path -Parent $target
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        $incoming = Join-Path $parent ('.arfko-incoming-' + [Guid]::NewGuid().ToString('N'))
        Copy-Item -LiteralPath $source -Destination $incoming -Force
        if ((Get-Hash $incoming) -ne $record.installed_sha256) { throw "수신 파일 해시 실패: $($record.relative)" }
        Move-Item -LiteralPath $incoming -Destination $target -Force
        if ((Get-Hash $target) -ne $record.installed_sha256) { throw "설치 파일 해시 실패: $($record.relative)" }
        $installed += $record
    }
} catch {
    $rollbackRecords = @($installed)
    [array]::Reverse($rollbackRecords)
    foreach ($record in $rollbackRecords) {
        $target = Get-Full (Join-Path $TargetRoot $record.relative.Replace('/','\'))
        if ($record.existed) { Copy-Item -LiteralPath $record.backup -Destination $target -Force }
        elseif (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Force }
    }
    throw
}
$state = [ordered]@{ schema='arf-ko-install-state-v1'; status='installed'; game_id='RPJJ99'; source_rvz=$SourceRvz; source_sha256=$ExpectedSource; target_root=$TargetRoot; backup_root=$backupRoot; package_manifest_sha256=(Get-Hash $ManifestPath); records=@($records) }
$state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding UTF8
Remove-Item -LiteralPath $journalPath -Force
Write-Host "설치 완료: $($records.Count)개 오버레이 파일"
