<#
.SYNOPSIS
    Lists every file in "Music Albums" (including subfolders) into one text file.

.DESCRIPTION
    Writes music_file_list.txt next to this script. Each line is the file's path
    relative to "Music Albums", e.g.
        Yeat\2093\Yeat - Breathe (Instrumental).mp3
    Send that file back to check which albums are missing tracks.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\list_music_files.ps1
#>
param(
    [string]$Root = (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Music Albums'),
    [string]$OutFile = (Join-Path $PSScriptRoot 'music_file_list.txt')
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\', '/')

$lines = Get-ChildItem -LiteralPath $Root -File -Recurse |
    Where-Object { $_.FullName -ne $OutFile -and $_.Extension -notin '.ps1', '.csv' } |
    ForEach-Object { $_.FullName.Substring($Root.Length + 1) } |
    Sort-Object

[IO.File]::WriteAllLines($OutFile, [string[]]$lines, (New-Object Text.UTF8Encoding $false))

Get-ChildItem -LiteralPath $Root -Directory | ForEach-Object {
    $n = @(Get-ChildItem -LiteralPath $_.FullName -File -Recurse).Count
    Write-Host ("{0,5}  {1}" -f $n, $_.Name)
}
Write-Host ''
Write-Host "Listed $(@($lines).Count) files to $OutFile" -ForegroundColor Green
