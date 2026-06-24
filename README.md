# Simonetto Devoluções

Gerenciador desktop de devoluções de produtos da Loja Simonetto.

## Requisitos

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

## Instalação

```bash
uv sync
```

## Rodar

```bash
uv run python main.py
```

A primeira execução cria a pasta de dados em `%LOCALAPPDATA%\SimonettoDevolucoes\`.

## Rodar com dados de exemplo (dev)

PowerShell:
```powershell
$env:SIMONETTO_DATA_DIR = ".\.dev_data"
uv run python scripts/seed_demo.py
uv run python main.py
```

Bash:
```bash
SIMONETTO_DATA_DIR=./.dev_data uv run python scripts/seed_demo.py
SIMONETTO_DATA_DIR=./.dev_data uv run python main.py
```

## Deploy em rede local (2 PCs)

Modelo: **um** PC é o **principal** — roda o servidor e guarda o banco. O **2º PC
não instala nada**, só abre o endereço no navegador. Os dados ficam só no principal.

### 1. Gerar o executável (no PC de desenvolvimento)

```powershell
.\build-exe.ps1
```

Gera `dist\Simonetto-Servidor.exe` (servidor de rede, não precisa de Python/uv no
PC da loja). Copie esse `.exe` para o **PC principal**.

### 2. No PC principal

1. Liberar a porta no firewall (uma vez, como **Administrador**):
   ```powershell
   .\liberar-firewall.ps1
   ```
2. Rodar o `Simonetto-Servidor.exe` (duplo clique). Abre um console mostrando o
   endereço de acesso, ex.: `http://192.168.0.10:8080`. Deixe aberto durante o uso.
3. (Opcional) iniciar sozinho ao ligar o PC:
   ```powershell
   .\instalar-autostart.ps1 -ExePath "C:\caminho\Simonetto-Servidor.exe"
   ```

### 3. No 2º PC

Criar um atalho em modo "app" (janela limpa, cara de programa nativo):

```powershell
.\criar-atalho-cliente.ps1 -Endereco "http://192.168.0.10:8080"
```

Ou simplesmente abrir esse endereço no navegador.

### Alternativa: rodar do código (sem gerar `.exe`)

No PC principal, com `uv` instalado: `.\iniciar-servidor.ps1` (mostra o endereço e
deixa um terminal aberto).

### Detalhes

- O banco (SQLite) roda em modo **WAL** + `busy_timeout`, suportando os 2 acessos
  simultâneos com segurança.
- Pela rede, só a pasta de **anexos** é exposta via HTTP — o banco e os backups
  **não** ficam acessíveis.
- Requisitos: os 2 PCs na mesma rede e a rede marcada como **Privada** no Windows.
- Variáveis de ambiente: `SIMONETTO_SERVER=1` (liga o modo servidor; o `.exe` já
  vem nesse modo), `SIMONETTO_PORT` (padrão `8080`), `SIMONETTO_DATA_DIR` (pasta
  de dados).

## Testes

```bash
uv run pytest -v
uv run pytest --cov=app/services --cov=app/repositories
```

## Estrutura

- `app/models/` — modelos SQLAlchemy
- `app/repositories/` — acesso ao banco (CRUD puro)
- `app/services/` — regras de negócio
- `app/ui/` — interface NiceGUI
- `docs/superpowers/specs/` — spec do produto
- `docs/superpowers/plans/` — plano de implementação

## Backup

- Automático ao fechar o app
- Configurável em **Configurações → Backup**
- Para apontar pro OneDrive: salvar a pasta de backup como
  `C:\Users\<você>\OneDrive\Devoluções\Backups`

## Restaurar de backup

1. Fechar o app
2. Extrair o `.zip` desejado sobre `%LOCALAPPDATA%\SimonettoDevolucoes\`
3. Reabrir o app

## Próximas melhorias (backlog)

- **Front-end pass**: melhorar a interface — layout mais polido, tipografia,
  espaçamentos, hierarquia visual, transições, possivelmente dark mode.
  Hoje está funcional mas tem cara de protótipo. Considerar usar componentes
  Quasar mais elaborados ou adotar um sistema de design coeso.
- Empacotamento em `.exe` (PyInstaller) para clicar e abrir sem terminal
- Atalho na área de trabalho apontando para o `.exe`
- Opções adicionais de frequência de backup (diário, semanal)
- Exportação CSV das devoluções
- Acesso pelo celular (rodar como serviço local + ngrok, ou migrar pra hospedagem)
