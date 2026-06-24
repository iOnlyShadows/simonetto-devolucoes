# Cria, na Area de Trabalho, um atalho que abre o Simonetto-Cliente.exe
# (janela NATIVA, sem navegador) ja apontando para o servidor.
# Rode no PC onde quer o icone (principal e/ou 2o PC).
# Uso:
#   .\criar-atalho-cliente.ps1 -Endereco "http://192.168.1.12:8080"
#   (no proprio PC principal pode usar -Endereco "http://localhost:8080")

param([string]$Endereco, [string]$ExePath)

$ErrorActionPreference = "Stop"

if (-not $Endereco) {
    $Endereco = Read-Host "Endereco do servidor (ex.: http://192.168.1.12:8080)"
}

if (-not $ExePath) {
    $cand = @(
        (Join-Path $PSScriptRoot "Simonetto-Cliente.exe"),
        (Join-Path $PSScriptRoot "dist\Simonetto-Cliente.exe")
    )
    $ExePath = $cand | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $ExePath -or -not (Test-Path $ExePath)) {
    Write-Error "Nao encontrei o Simonetto-Cliente.exe. Passe o caminho com -ExePath."
    exit 1
}

$desktop = [Environment]::GetFolderPath("Desktop")
$lnk = Join-Path $desktop "Simonetto Devolucoes.lnk"

$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($lnk)
$sc.TargetPath = $ExePath
$sc.Arguments = $Endereco
$sc.WorkingDirectory = (Split-Path $ExePath)
$sc.IconLocation = "$ExePath,0"
$sc.Description = "Gerenciador de Devolucoes - Simonetto"
$sc.Save()

Write-Host "Atalho 'Simonetto Devolucoes' criado na Area de Trabalho." -ForegroundColor Green
Write-Host "Ele abre a janela nativa apontando para $Endereco"
