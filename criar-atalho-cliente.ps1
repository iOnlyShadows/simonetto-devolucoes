# Cria, na Area de Trabalho, um atalho que abre o app em modo "app"
# (janela limpa, sem barra de navegador — cara de programa nativo).
# Rode no 2o PC (cliente).
# Uso:  .\criar-atalho-cliente.ps1 -Endereco "http://192.168.0.10:8080"

param([string]$Endereco)

$ErrorActionPreference = "Stop"

if (-not $Endereco) {
    $Endereco = Read-Host "Endereco do servidor (ex.: http://192.168.0.10:8080)"
}

# Procura Chrome ou Edge
$browsers = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
)
$browser = $browsers | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $browser) {
    Write-Error "Nao encontrei Chrome nem Edge. Instale um deles ou crie um atalho manual para $Endereco."
    exit 1
}

$desktop = [Environment]::GetFolderPath("Desktop")
$lnk = Join-Path $desktop "Simonetto Devolucoes.lnk"

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnk)
$sc.TargetPath = $browser
$sc.Arguments = "--app=$Endereco"
$sc.IconLocation = "$browser,0"
$sc.Description = "Gerenciador de Devolucoes - Simonetto"
$sc.Save()

Write-Host "Atalho criado na Area de Trabalho: 'Simonetto Devolucoes'." -ForegroundColor Green
Write-Host "Ele abre $Endereco em janela de app (sem barra do navegador)."
