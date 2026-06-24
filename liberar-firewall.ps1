# Libera a porta do app no Firewall do Windows (somente rede PRIVADA).
# Rode UMA VEZ, no PC PRINCIPAL, como ADMINISTRADOR
# (clique direito > "Executar com o PowerShell" como admin).

$porta = if ($env:SIMONETTO_PORT) { $env:SIMONETTO_PORT } else { "8080" }
$nome = "Simonetto Devolucoes ($porta)"

# Remove regra antiga de mesmo nome (se existir) e recria
Get-NetFirewallRule -DisplayName $nome -ErrorAction SilentlyContinue | Remove-NetFirewallRule

New-NetFirewallRule -DisplayName $nome `
    -Direction Inbound -Action Allow -Protocol TCP `
    -LocalPort $porta -Profile Private | Out-Null

Write-Host "Regra de firewall criada: '$nome' (porta $porta, perfil Privado)." -ForegroundColor Green
Write-Host "Se o 2o PC ainda nao conectar, confirme que a rede da loja esta como 'Rede privada' no Windows."
