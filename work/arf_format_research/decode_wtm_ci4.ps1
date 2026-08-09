param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Drawing

function Read-U16BE([byte[]]$Bytes, [int]$Offset) {
    return ([int]$Bytes[$Offset] -shl 8) -bor [int]$Bytes[$Offset + 1]
}

function Expand-Bits([int]$Value, [int]$Bits) {
    $maximum = (1 -shl $Bits) - 1
    return [int][Math]::Round(($Value * 255.0) / $maximum)
}

function Decode-Rgb5A3([int]$Value) {
    if (($Value -band 0x8000) -ne 0) {
        $a = 255
        $r = Expand-Bits (($Value -shr 10) -band 0x1F) 5
        $g = Expand-Bits (($Value -shr 5) -band 0x1F) 5
        $b = Expand-Bits ($Value -band 0x1F) 5
    }
    else {
        $a = Expand-Bits (($Value -shr 12) -band 0x7) 3
        $r = Expand-Bits (($Value -shr 8) -band 0xF) 4
        $g = Expand-Bits (($Value -shr 4) -band 0xF) 4
        $b = Expand-Bits ($Value -band 0xF) 4
    }

    return [System.Drawing.Color]::FromArgb($a, $r, $g, $b)
}

$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
$bytes = [System.IO.File]::ReadAllBytes($resolvedInput)

if ($bytes.Length -lt 0x40 -or [Text.Encoding]::ASCII.GetString($bytes, 0, 4) -ne 'WTMD') {
    throw "Not a WTMD file: $resolvedInput"
}

$width = Read-U16BE $bytes 0x08
$height = Read-U16BE $bytes 0x0A
$format = $bytes[0x0C]
$dataOffset = (([int]$bytes[0x10] -shl 24) -bor ([int]$bytes[0x11] -shl 16) -bor ([int]$bytes[0x12] -shl 8) -bor [int]$bytes[0x13])

if ($format -ne 8) {
    throw "Only GX_TF_CI4 (format 8) is implemented; file reports format $format"
}
if (($width % 8) -ne 0 -or ($height % 8) -ne 0) {
    throw "CI4 dimensions must be multiples of 8; got ${width}x${height}"
}

$palette = New-Object 'System.Drawing.Color[]' 16
for ($i = 0; $i -lt 16; $i++) {
    $palette[$i] = Decode-Rgb5A3 (Read-U16BE $bytes (0x20 + 2 * $i))
}

$expectedDataLength = [int]($width * $height / 2)
if ($dataOffset + $expectedDataLength -gt $bytes.Length) {
    throw "Truncated CI4 payload: need $expectedDataLength bytes from 0x$($dataOffset.ToString('X'))"
}

$bitmap = New-Object System.Drawing.Bitmap($width, $height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
try {
    $cursor = $dataOffset
    for ($tileY = 0; $tileY -lt $height; $tileY += 8) {
        for ($tileX = 0; $tileX -lt $width; $tileX += 8) {
            for ($row = 0; $row -lt 8; $row++) {
                for ($pair = 0; $pair -lt 4; $pair++) {
                    $packed = $bytes[$cursor++]
                    $bitmap.SetPixel($tileX + 2 * $pair, $tileY + $row, $palette[($packed -shr 4) -band 0xF])
                    $bitmap.SetPixel($tileX + 2 * $pair + 1, $tileY + $row, $palette[$packed -band 0xF])
                }
            }
        }
    }

    $fullOutput = [System.IO.Path]::GetFullPath($OutputPath)
    $outputDirectory = [System.IO.Path]::GetDirectoryName($fullOutput)
    [System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
    $bitmap.Save($fullOutput, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output $fullOutput
}
finally {
    $bitmap.Dispose()
}
