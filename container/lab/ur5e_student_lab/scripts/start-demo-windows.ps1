param([string]$WebotsHome = (Join-Path $env:USERPROFILE '.local\Webots-R2023b'))
$ErrorActionPreference = 'Stop'
$env:WEBOTS_HOME = $WebotsHome
$packageRoot = Split-Path $PSScriptRoot -Parent
$world = Join-Path $packageRoot 'webots\worlds\ur5e_demo.wbt'
$exe = Join-Path $WebotsHome 'msys64\mingw64\bin\webots.exe'
if (-not (Test-Path -LiteralPath $exe)) { throw 'Webots R2023b not found. Specify -WebotsHome with an ASCII installation path.' }
Start-Process -FilePath $exe -ArgumentList @('--mode=realtime', '--port=1240', ('"' + $world + '"')) -WorkingDirectory $packageRoot
