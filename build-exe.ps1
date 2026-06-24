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

Write-Host ""
Write-Host "Pronto! Em dist\:" -ForegroundColor Green
Write-Host "  Simonetto-Servidor.exe  -> copie para o PC principal"
Write-Host "  Simonetto-Cliente.exe   -> copie para os 2 PCs"
