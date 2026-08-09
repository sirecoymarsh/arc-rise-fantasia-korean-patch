[CmdletBinding()]
param([string]$StateRoot = (Join-Path $env:LOCALAPPDATA 'ArcRiseFantasiaKO'))
$ErrorActionPreference = 'Stop'
function Get-Full([string]$Path) { return [IO.Path]::GetFullPath($Path) }
function Get-Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
$StateRoot = Get-Full $StateRoot
$statePath = Join-Path $StateRoot 'state.json'
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) { throw "설치 상태를 찾을 수 없습니다: $statePath" }
$state = Get-Content -LiteralPath $statePath -Encoding UTF8 -Raw | ConvertFrom-Json
if ($state.status -ne 'installed' -or $state.game_id -ne 'RPJJ99') { throw '알 수 없는 설치 상태입니다.' }
$targetRoot = Get-Full ([string]$state.target_root)
foreach ($record in @($state.records)) {
    $target = Get-Full (Join-Path $targetRoot ([string]$record.relative).Replace('/','\'))
    if (-not $target.StartsWith($targetRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "대상 경로 탈출: $($record.relative)" }
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "설치 파일 누락: $($record.relative)" }
    if ((Get-Hash $target) -ne ([string]$record.installed_sha256).ToUpperInvariant()) { throw "설치 후 파일이 변경되어 복원을 중단합니다: $($record.relative)" }
    if ($record.existed) {
        if (-not (Test-Path -LiteralPath $record.backup -PathType Leaf)) { throw "백업 누락: $($record.relative)" }
        if ((Get-Hash $record.backup) -ne ([string]$record.original_sha256).ToUpperInvariant()) { throw "백업 해시 불일치: $($record.relative)" }
    }
}
$restoreRecords = @($state.records)
[array]::Reverse($restoreRecords)
foreach ($record in $restoreRecords) {
    $target = Get-Full (Join-Path $targetRoot ([string]$record.relative).Replace('/','\'))
    if ($record.existed) {
        Copy-Item -LiteralPath $record.backup -Destination $target -Force
        if ((Get-Hash $target) -ne ([string]$record.original_sha256).ToUpperInvariant()) { throw "복원 확인 실패: $($record.relative)" }
    } else {
        Remove-Item -LiteralPath $target -Force
    }
}
$state.status = 'restored'
$state | Add-Member -NotePropertyName 'restored_utc' -NotePropertyValue ([DateTime]::UtcNow.ToString('o')) -Force
$state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding UTF8
Write-Host "복원 완료: $(@($state.records).Count)개 오버레이 파일"
