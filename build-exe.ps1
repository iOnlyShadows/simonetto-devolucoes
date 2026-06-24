# Gera os 2 executaveis do Simonetto Devolucoes.
# Rode no PC de desenvolvimento: .\build-exe.ps1
# Resultado em dist\:
#   - Simonetto-Servidor.exe  (servidor de rede; vai SO no PC principal)
#   - Simonetto-Cliente.exe   (janela nativa; vai nos 2 PCs)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "Instalando dependencias (incluindo PyInstaller)..." -ForegroundColor Cyan
uv sync

Write-Host "Empacotando o SERVIDOR..." -ForegroundColor Cyan
uv run pyinstaller --noconfirm --clean --onefile --console `
    --name "Simonetto-Servidor" `
    --collect-all nicegui `
    --add-data "app/ui/assets;app/ui/assets" `
    main.py

Write-Host "Empacotando o CLIENTE (janela nativa)..." -ForegroundColor Cyan
uv run pyinstaller --noconfirm --clean --onefile --windowed `
    --name "Simonetto-Cliente" `
    --collect-all webview `
    client.py

Write-Host "Montando o instalador do cliente (.zip)..." -ForegroundColor Cyan
$stage = Join-Path $env:TEMP "sim_instalador"
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Path $stage | Out-Null
Copy-Item "dist\Simonetto-Cliente.exe" "$stage\Simonetto-Cliente.exe"
Copy-Item "instalar-cliente.bat" "$stage\Instalar.bat"
$zip = "dist\Simonetto-Cliente-Instalador.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path "$stage\*" -DestinationPath $zip
Remove-Item -Recurse -Force $stage

Write-Host ""
Write-Host "Pronto! Em dist\:" -ForegroundColor Green
Write-Host "  Simonetto-Servidor.exe              -> PC principal"
Write-Host "  Simonetto-Cliente.exe               -> PC principal (janela)"
Write-Host "  Simonetto-Cliente-Instalador.zip    -> envie para o 2o PC"
