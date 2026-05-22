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
