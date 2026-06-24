# Inicia o Simonetto Devolucoes em modo SERVIDOR (rede local).
# Rode este script no PC PRINCIPAL (o que guarda os dados).
# Deixe a janela aberta enquanto o app estiver em uso.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$env:SIMONETTO_SERVER = "1"
if (-not $env:SIMONETTO_PORT) { $env:SIMONETTO_PORT = "8080" }

# (opcional) pasta de dados personalizada — descomente e ajuste se quiser:
# $env:SIMONETTO_DATA_DIR = "C:\SimonettoDados"

# Descobre o IP da rede local pra montar a URL de acesso do 2o PC
$ip = (Get-NetIPConfiguration |
    Where-Object { $_.IPv4DefaultGateway -ne $null -and $_.NetAdapter.Status -eq 'Up' } |
    Select-Object -First 1).IPv4Address.IPAddress

$porta = $env:SIMONETTO_PORT
Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Simonetto Devolucoes - Servidor da Rede Local" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Neste PC (principal):  http://localhost:$porta"
if ($ip) {
    Write-Host "  No OUTRO PC, acesse:   http://$($ip):$porta" -ForegroundColor Green
} else {
    Write-Host "  (Nao consegui detectar o IP. Rode 'ipconfig' e use o IPv4.)" -ForegroundColor Yellow
}
Write-Host "  Deixe esta janela ABERTA enquanto usar o app."
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

uv run python main.py
