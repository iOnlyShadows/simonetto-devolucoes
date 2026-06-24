# Faz o Simonetto-Servidor.exe iniciar sozinho ao ligar o PC principal.
# Rode no PC PRINCIPAL, como Administrador.
# Uso:  .\instalar-autostart.ps1              (procura o exe ao lado / em dist\)
#       .\instalar-autostart.ps1 -ExePath "C:\Simonetto\Simonetto-Servidor.exe"

param([string]$ExePath)

$ErrorActionPreference = "Stop"

if (-not $ExePath) {
    $candidatos = @(
        (Join-Path $PSScriptRoot "Simonetto-Servidor.exe"),
        (Join-Path $PSScriptRoot "dist\Simonetto-Servidor.exe")
    )
    $ExePath = $candidatos | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $ExePath -or -not (Test-Path $ExePath)) {
    Write-Error "Nao encontrei o Simonetto-Servidor.exe. Passe o caminho com -ExePath."
    exit 1
}

$nome = "SimonettoDevolucoes"
$acao = New-ScheduledTaskAction -Execute $ExePath -WorkingDirectory (Split-Path $ExePath)
$gatilho = New-ScheduledTaskTrigger -AtLogOn
$set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $nome -Action $acao -Trigger $gatilho -Settings $set `
    -Force -Description "Servidor de devolucoes Simonetto (rede local)" | Out-Null

Write-Host "Auto-start configurado: o servidor sobe sozinho ao iniciar a sessao do Windows." -ForegroundColor Green
Write-Host "Iniciar agora:  Start-ScheduledTask -TaskName $nome"
Write-Host "Remover depois: Unregister-ScheduledTask -TaskName $nome -Confirm:`$false"
