[CmdletBinding()]
param(
    [string]$TargetRoot,
    [switch]$NonInteractive,
    [switch]$SkipDolphinCheck
)

$ErrorActionPreference = 'Stop'
$ExpectedGameId = 'RPJJ99'
$PackageRoot = [IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$PayloadRoot = Join-Path $PackageRoot 'payload\riivolution_sd'
$ManifestPath = Join-Path $PackageRoot 'MANIFEST.json'
$PatchFolderName = 'arc_rise_fantasia_ko_full'
$PatchXmlName = 'arc_rise_fantasia_ko_full.xml'

function Get-Full([string]$Path) {
    return [IO.Path]::GetFullPath($Path)
}

function Get-Hash([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Read-Utf8Json([string]$Path) {
    return (Get-Content -LiteralPath $Path -Encoding UTF8 -Raw | ConvertFrom-Json)
}

function Test-ChildPath([string]$Child, [string]$Parent) {
    $childFull = Get-Full $Child
    $parentFull = (Get-Full $Parent).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    return $childFull.StartsWith($parentFull, [StringComparison]::OrdinalIgnoreCase)
}

function Show-Notice([string]$Text, [string]$Title, [string]$Icon = 'Information') {
    if ($NonInteractive) {
        Write-Host $Text
        return
    }
    Add-Type -AssemblyName System.Windows.Forms
    $messageIcon = [System.Enum]::Parse([System.Windows.Forms.MessageBoxIcon], $Icon)
    [void][System.Windows.Forms.MessageBox]::Show(
        $Text,
        $Title,
        [System.Windows.Forms.MessageBoxButtons]::OK,
        $messageIcon
    )
}

function Normalize-LoadRoot([string]$SelectedPath) {
    $full = Get-Full $SelectedPath
    if ([IO.Path]::GetFileName($full.TrimEnd('\')) -ieq 'Load') {
        return $full.TrimEnd('\')
    }
    return Get-Full (Join-Path $full 'Load')
}

function Find-DolphinLoadRoot {
    $candidateRoots = New-Object System.Collections.Generic.List[string]
    try {
        foreach ($process in @(Get-Process -Name Dolphin -ErrorAction SilentlyContinue)) {
            if ($process.Path) {
                $candidateRoots.Add((Join-Path (Split-Path -Parent $process.Path) 'User'))
            }
        }
    } catch { }
    if ($env:APPDATA) {
        $candidateRoots.Add((Join-Path $env:APPDATA 'Dolphin Emulator'))
    }
    $documents = [Environment]::GetFolderPath('MyDocuments')
    if ($documents) {
        $candidateRoots.Add((Join-Path $documents 'Dolphin Emulator'))
    }
    if ($env:LOCALAPPDATA) {
        $candidateRoots.Add((Join-Path $env:LOCALAPPDATA 'Dolphin Emulator'))
    }

    $seen = @{}
    foreach ($root in $candidateRoots) {
        $full = Get-Full $root
        if ($seen.ContainsKey($full)) { continue }
        $seen[$full] = $true
        if (-not (Test-Path -LiteralPath $full -PathType Container)) { continue }
        $recognized = (
            (Test-Path -LiteralPath (Join-Path $full 'Config\Dolphin.ini') -PathType Leaf) -or
            (Test-Path -LiteralPath (Join-Path $full 'Wii') -PathType Container) -or
            (Test-Path -LiteralPath (Join-Path $full 'Load') -PathType Container)
        )
        if ($recognized) {
            return Normalize-LoadRoot $full
        }
    }
    return $null
}

function Select-DolphinLoadRoot {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Dolphin 사용자 폴더를 선택하세요.`n(Dolphin에서 '파일 → 사용자 폴더 열기'로 확인할 수 있습니다.)"
    $dialog.ShowNewFolderButton = $true
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        throw '설치가 취소되었습니다.'
    }
    return Normalize-LoadRoot $dialog.SelectedPath
}

function Verify-Package {
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw 'MANIFEST.json이 없습니다. ZIP을 완전히 압축 해제한 뒤 다시 실행하세요.'
    }
    if (-not (Test-Path -LiteralPath $PayloadRoot -PathType Container)) {
        throw '패치 데이터가 없습니다. ZIP을 완전히 압축 해제한 뒤 다시 실행하세요.'
    }
    $manifest = Read-Utf8Json $ManifestPath
    if ($manifest.game_id -ne $ExpectedGameId) {
        throw '다른 게임용 패키지입니다.'
    }
    if (
        $manifest.translation_engine_policy -ne 'Codex internal models only' -or
        $manifest.external_translation_models_or_apis_used -ne $false
    ) {
        throw '번역 출처 정보가 일치하지 않습니다.'
    }
    $payloadEntries = @($manifest.files | Where-Object { $_.role -eq 'riivolution_overlay' })
    if ($payloadEntries.Count -ne [int]$manifest.overlay_file_count) {
        throw '패치 파일 수가 매니페스트와 다릅니다.'
    }
    foreach ($entry in $payloadEntries) {
        $path = [string]$entry.path
        if (-not $path.StartsWith('payload/riivolution_sd/', [StringComparison]::Ordinal)) {
            throw "잘못된 패치 경로: $path"
        }
        $candidate = Get-Full (Join-Path $PackageRoot $path.Replace('/', '\'))
        if (-not (Test-ChildPath $candidate $PackageRoot)) {
            throw "패키지 경로가 패키지 밖을 가리킵니다: $path"
        }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            throw "패치 파일이 없습니다: $path"
        }
        if ((Get-Hash $candidate) -ne ([string]$entry.sha256).ToUpperInvariant()) {
            throw "패치 파일이 손상되었습니다: $path"
        }
    }
    return @($payloadEntries)
}

function Install-Overlay([object[]]$Entries, [string]$LoadRoot) {
    $load = Get-Full $LoadRoot
    New-Item -ItemType Directory -Force -Path $load | Out-Null
    $transactionId = [Guid]::NewGuid().ToString('N')
    $incomingRoot = Join-Path $load ('.arfko-incoming-' + $transactionId)
    $oldPatch = Join-Path $load ('.arfko-old-' + $transactionId)
    $riivolutionRoot = Join-Path $load 'riivolution'
    $oldXml = Join-Path $riivolutionRoot ('.arfko-old-' + $transactionId + '.xml')
    $destinationPatch = Join-Path $load $PatchFolderName
    $destinationXml = Join-Path $riivolutionRoot $PatchXmlName
    $patchMovedAside = $false
    $newPatchInstalled = $false
    $xmlMovedAside = $false
    $newXmlInstalled = $false

    try {
        New-Item -ItemType Directory -Force -Path $incomingRoot | Out-Null
        foreach ($entry in $Entries) {
            $relative = ([string]$entry.path).Substring('payload/riivolution_sd/'.Length)
            $source = Get-Full (Join-Path $PayloadRoot $relative.Replace('/', '\'))
            $incoming = Get-Full (Join-Path $incomingRoot $relative.Replace('/', '\'))
            if (-not (Test-ChildPath $incoming $incomingRoot)) {
                throw "설치 경로가 임시 폴더 밖을 가리킵니다: $relative"
            }
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $incoming) | Out-Null
            Copy-Item -LiteralPath $source -Destination $incoming -Force
            if ((Get-Hash $incoming) -ne ([string]$entry.sha256).ToUpperInvariant()) {
                throw "복사 확인에 실패했습니다: $relative"
            }
        }

        $incomingPatch = Join-Path $incomingRoot $PatchFolderName
        $incomingXml = Join-Path (Join-Path $incomingRoot 'riivolution') $PatchXmlName
        if (-not (Test-Path -LiteralPath $incomingPatch -PathType Container)) {
            throw '설치할 한국어 패치 폴더가 없습니다.'
        }
        if (-not (Test-Path -LiteralPath $incomingXml -PathType Leaf)) {
            throw '설치할 Riivolution XML이 없습니다.'
        }
        New-Item -ItemType Directory -Force -Path $riivolutionRoot | Out-Null

        if (Test-Path -LiteralPath $destinationPatch) {
            Move-Item -LiteralPath $destinationPatch -Destination $oldPatch
            $patchMovedAside = $true
        }
        Move-Item -LiteralPath $incomingPatch -Destination $destinationPatch
        $newPatchInstalled = $true

        if (Test-Path -LiteralPath $destinationXml -PathType Leaf) {
            Move-Item -LiteralPath $destinationXml -Destination $oldXml
            $xmlMovedAside = $true
        }
        Move-Item -LiteralPath $incomingXml -Destination $destinationXml
        $newXmlInstalled = $true

        foreach ($entry in $Entries) {
            $relative = ([string]$entry.path).Substring('payload/riivolution_sd/'.Length)
            $installed = Get-Full (Join-Path $load $relative.Replace('/', '\'))
            if (-not (Test-ChildPath $installed $load)) {
                throw "설치 확인 경로가 Load 폴더 밖을 가리킵니다: $relative"
            }
            if (-not (Test-Path -LiteralPath $installed -PathType Leaf)) {
                throw "설치된 파일이 없습니다: $relative"
            }
            if ((Get-Hash $installed) -ne ([string]$entry.sha256).ToUpperInvariant()) {
                throw "설치된 파일의 확인에 실패했습니다: $relative"
            }
        }

        if ($patchMovedAside -and (Test-Path -LiteralPath $oldPatch)) {
            Remove-Item -LiteralPath $oldPatch -Recurse -Force
            $patchMovedAside = $false
        }
        if ($xmlMovedAside -and (Test-Path -LiteralPath $oldXml)) {
            Remove-Item -LiteralPath $oldXml -Force
            $xmlMovedAside = $false
        }
    } catch {
        if ($newXmlInstalled -and (Test-Path -LiteralPath $destinationXml)) {
            Remove-Item -LiteralPath $destinationXml -Force
        }
        if ($xmlMovedAside -and (Test-Path -LiteralPath $oldXml)) {
            Move-Item -LiteralPath $oldXml -Destination $destinationXml -Force
        }
        if ($newPatchInstalled -and (Test-Path -LiteralPath $destinationPatch)) {
            Remove-Item -LiteralPath $destinationPatch -Recurse -Force
        }
        if ($patchMovedAside -and (Test-Path -LiteralPath $oldPatch)) {
            Move-Item -LiteralPath $oldPatch -Destination $destinationPatch
        }
        throw
    } finally {
        if (Test-Path -LiteralPath $incomingRoot) {
            Remove-Item -LiteralPath $incomingRoot -Recurse -Force
        }
    }
}

try {
    if (-not $SkipDolphinCheck -and @(Get-Process -Name Dolphin -ErrorAction SilentlyContinue).Count -gt 0) {
        throw 'Dolphin을 완전히 종료한 뒤 설치하기를 다시 실행하세요.'
    }
    $entries = Verify-Package
    if ($TargetRoot) {
        $loadRoot = Normalize-LoadRoot $TargetRoot
    } else {
        $loadRoot = Find-DolphinLoadRoot
        if (-not $loadRoot) {
            if ($NonInteractive) {
                throw 'Dolphin 사용자 폴더를 자동으로 찾지 못했습니다.'
            }
            $loadRoot = Select-DolphinLoadRoot
        }
    }
    Install-Overlay -Entries $entries -LoadRoot $loadRoot
    Show-Notice (
        "한국어 패치 설치가 완료되었습니다.`n`n" +
        "Dolphin에서 게임을 우클릭하고`n" +
        "'Riivolution 패치로 시작'을 선택한 뒤`n" +
        "한국어 패치를 켜고 실행하세요.`n`n" +
        "설치 위치: $loadRoot"
    ) '아크 라이즈 판타지아 한국어 패치'
    exit 0
} catch {
    Show-Notice ("설치하지 못했습니다.`n`n" + $_.Exception.Message) '한국어 패치 설치 오류' 'Error'
    Write-Error $_
    exit 1
}
