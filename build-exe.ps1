# Gera o executavel Simonetto-Servidor.exe (servidor de rede local).
# Rode no PC de desenvolvimento: .\build-exe.ps1
# O resultado fica em: dist\Simonetto-Servidor.exe

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "Instalando dependencias (incluindo PyInstaller)..." -ForegroundColor Cyan
uv sync

Write-Host "Empacotando o executavel..." -ForegroundColor Cyan
uv run pyinstaller --noconfirm --clean --onefile --console `
    --name "Simonetto-Servidor" `
    --collect-all nicegui `
    --add-data "app/ui/assets;app/ui/assets" `
    main.py

Write-Host ""
Write-Host "Pronto! Executavel em: dist\Simonetto-Servidor.exe" -ForegroundColor Green
Write-Host "Copie esse arquivo para o PC principal da loja."
