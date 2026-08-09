[CmdletBinding()]
param([string]$StateRoot = (Join-Path $env:LOCALAPPDATA 'ArcRiseFantasiaKO'))
$ErrorActionPreference = 'Stop'
function Get-Full([string]$Path) { return [IO.Path]::GetFullPath($Path) }
function Get-Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
$statePath = Join-Path (Get-Full $StateRoot) 'state.json'
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) { throw "설치 상태를 찾을 수 없습니다: $statePath" }
$state = Get-Content -LiteralPath $statePath -Encoding UTF8 -Raw | ConvertFrom-Json
if ($state.status -ne 'installed') { throw "현재 설치 상태가 아닙니다: $($state.status)" }
$targetRoot = Get-Full ([string]$state.target_root)
$errors = @()
foreach ($record in @($state.records)) {
    $target = Get-Full (Join-Path $targetRoot ([string]$record.relative).Replace('/','\'))
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { $errors += "누락: $($record.relative)"; continue }
    if ((Get-Hash $target) -ne ([string]$record.installed_sha256).ToUpperInvariant()) { $errors += "해시 불일치: $($record.relative)" }
}
if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_ }; throw "무결성 검사 실패: $($errors.Count)건" }
Write-Host "무결성 검사 통과: $(@($state.records).Count)개 파일"
