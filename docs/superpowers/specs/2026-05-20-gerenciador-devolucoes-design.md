# Gerenciador de Devoluções — Loja Simonetto

**Data:** 2026-05-20
**Status:** Design aprovado, aguardando plano de implementação
**Autor:** Matheus Simonetto + Claude

## 1. Contexto e Objetivo

A loja Simonetto trabalha com várias marcas, cada uma com seu próprio processo de devolução de produtos defeituosos. Hoje não há controle centralizado, o que faz com que casos "se percam" — fica difícil saber em qual etapa está cada devolução, se já foi abatida na nota / ressarcida, se o cliente está aguardando uma peça de volta, etc.

O objetivo deste app é prover um **gerenciador desktop simples, flexível e visual** para acompanhar cada devolução do início ao fim, com interface amigável e baixa fricção de uso.

### Premissas

- **Plataforma:** Desktop Windows, single-user (apenas o dono usa)
- **Volume:** baixo (< 20 devoluções/mês)
- **Offline-first:** funciona sem internet
- **Stack:** Python + NiceGUI + SQLite
- **Futuro:** possível migração para web hospedada (acesso pelo celular) — o design não deve impedir isso

### Não-objetivos (escopo fora)

- Integração com ERP / sistema de notas fiscais da loja
- Multi-usuário / autenticação
- Acesso pelo celular (versão 1)
- Geração automática de relatórios fiscais
- Empacotamento em `.exe` (fica para uma versão posterior — v1 roda via `uv run`)

## 2. Modelo Conceitual: os 3 Eixos

Em vez de tentar modelar o processo específico de cada marca (que muda com frequência e dá manutenção infinita), o app padroniza o controle em **3 eixos independentes**:

1. **Status do processo** (sequencial): em que etapa do tratamento está o caso
2. **Destino físico do produto** (independente): onde está fisicamente o produto
3. **Forma de ressarcimento** (informativo): como será / foi ressarcido

Os eixos são independentes — uma devolução pode estar `Ressarcido + Na loja + Abate na nota`, por exemplo (fábrica não veio buscar mas já abateu o valor).

Existe também uma flag adicional **"cliente aguardando retorno"**, usada principalmente para joias (cliente espera a peça consertada/substituta voltar).

## 3. Modelo de Dados

### Tabela `marcas`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | int (PK, auto) | |
| `nome` | text, único | ex: "Vizzano", "Olympikus" |
| `forma_ressarcimento_padrao` | enum, nullable | sugestão automática ao criar devolução |
| `observacoes` | text | ex: contato do representante |

### Tabela `devolucoes`

**Identificação:**
- `id` (int, PK, auto)
- `marca_id` (FK marcas, obrigatório)
- `criado_em`, `atualizado_em` (timestamps automáticos)

**Produto:**
- `produto_modelo` (text, obrigatório)
- `produto_referencia` (text, opcional)
- `quantidade` (int, default 1)
- `valor_custo` (decimal, opcional)
- `defeito_descricao` (text, opcional)
- `foto_principal_caminho` (text, opcional) — caminho relativo do thumbnail principal

**Datas:**
- `data_devolucao` (date, obrigatório)
- `data_compra_original` (date, opcional) — relevante para marcas com prazo (ex: Olympikus, 2 anos)

**Notas fiscais (ambas opcionais):**
- `nf_origem` (text)
- `nf_abatimento` (text)

**Cliente (opcional, relevante para joias):**
- `cliente_nome` (text)
- `cliente_contato` (text)
- `cliente_aguardando_retorno` (bool, default false)

**Status (os 3 eixos):**
- `status_processo` (enum) — ver §4
- `destino_fisico` (enum) — ver §4
- `forma_ressarcimento` (enum) — ver §4

**Texto livre:**
- `observacoes` (text)

**Soft delete (lixeira):**
- `excluido_em` (timestamp, nullable) — quando marcado, vai para a lixeira

### Tabela `anexos`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | int (PK, auto) | |
| `devolucao_id` | FK devolucoes | |
| `nome_original` | text | nome do arquivo original |
| `caminho_interno` | text | caminho relativo ao diretório de dados |
| `tipo` | text | pdf / imagem / outro |
| `tamanho_bytes` | int | |
| `criado_em` | timestamp | |

### Tabela `historico_status`

Registro de cada mudança nos eixos 1 e 2, para auditoria e linha do tempo.

| Campo | Tipo | Notas |
|---|---|---|
| `id` | int (PK, auto) | |
| `devolucao_id` | FK devolucoes | |
| `campo` | text | `status_processo` ou `destino_fisico` |
| `valor_anterior` | text | enum value anterior (pode ser null no caso de criação) |
| `valor_novo` | text | enum value novo |
| `observacao` | text, opcional | comentário livre na transição |
| `data` | timestamp | |

## 4. Enums e Cores

### Status do processo (Eixo 1)

| Status | Cor | Ícone | Significado |
|---|---|---|---|
| `defeito_identificado` | 🔴 Vermelho | ⚠️ | Chegou, ainda não foi tratado |
| `sinalizado` | 🟡 Amarelo | 📨 | Comunicado à marca, aguardando |
| `pendente_ressarcimento` | 🟠 Laranja | ⏳ | Aprovado, falta ressarcir |
| `ressarcido` | 🟢 Verde | ✅ | Encerrado |

Transições livres (pode pular ou voltar). Cada mudança gera entrada em `historico_status`.

### Destino físico (Eixo 2)

| Destino | Cor | Ícone |
|---|---|---|
| `na_loja` | ⚪ Cinza | 📦 |
| `recolhido` | 🔵 Azul | 🛠️ |
| `enviado` | 🟣 Roxo | 📤 |
| `descartado` | ⚫ Preto | 🗑️ |

Independente do Eixo 1.

### Forma de ressarcimento (Eixo 3, informativo)

`abate_nota` (💸) · `dinheiro` (💵) · `troca` (🔄) · `credito` (🎟️) · `outro` (❓ + campo livre)

Sem cor própria.

## 5. Telas e Fluxos

App de janela única, com **menu lateral fixo à esquerda** e área de conteúdo à direita.

Menu lateral: **📋 Devoluções** · **🏷️ Marcas** · **🗑️ Lixeira** · **⚙️ Configurações**

### Tela 1 — Lista de Devoluções (inicial)

- Tabela/lista com uma devolução por linha, ordenada por data de devolução (mais recente primeiro)
- Cada linha mostra: thumbnail, marca, modelo + ref, data, cliente (se houver, com ⏳ se aguardando retorno), e os **3 badges** (status, destino, forma de ressarcimento) lado a lado
- Filtros no topo: busca textual + dropdowns de marca/status/destino + checkbox "só aguardando retorno"
- Botão "+ Nova Devolução" abre o formulário (Tela 2)
- Clicar numa linha abre o detalhe (Tela 3)

### Tela 2 — Formulário (Nova / Editar) — **modal lateral**

Aparece como painel deslizante à direita, sobre a lista. Mesmo formulário para criar e editar.

Seções: Marca · Produto (incl. upload foto principal) · Datas · Notas fiscais · Cliente · Status (os 3 dropdowns) · Anexos extras · Observações.

Validação: marca e data de devolução são obrigatórios; todo o resto é opcional.

Ao escolher a marca, o app pré-seleciona a `forma_ressarcimento_padrao` cadastrada (sobrescrevível).

### Tela 3 — Detalhe da Devolução

- Cabeçalho com thumbnail grande, identificação, e os 3 badges atuais
- Botões "Editar" (abre Tela 2 em modo edição), "Mudar destino" (dropdown rápido)
- Mudanças de status sempre **manuais via dropdown** (não há botão de "avançar")
- Bloco de detalhes (valor, defeito, NFs, cliente)
- Bloco de anexos (abrir / baixar / remover, e adicionar)
- Bloco de observações
- **Linha do tempo** com entradas do `historico_status`
- Botão de excluir (envia para lixeira)

### Tela 4 — Marcas

CRUD simples: lista, adicionar, editar (nome, forma padrão, observações), excluir (apenas se não houver devoluções vinculadas).

### Tela 5 — Configurações

- Caminho da pasta de dados (read-only, informativo)
- Pasta de backup (editável)
- Frequência de backup (a v1 usa **"ao fechar o app"**, mas o seletor existe para futuras opções)
- Quantidade de backups a manter (default 30)
- Botão "Fazer backup agora"
- Lista dos últimos backups (com tamanho e data)

### Tela auxiliar — Lixeira

Lista das devoluções com `excluido_em != null` e menos de 30 dias. Cada uma pode ser **restaurada** ou **removida definitivamente**. Após 30 dias, expurgo automático ao abrir o app.

## 6. Armazenamento em Disco

Pasta única dentro de `AppData\Local`:

```
C:\Users\<usuario>\AppData\Local\SimonettoDevolucoes\
├── dados.db
├── anexos\
│   ├── 0001\
│   │   ├── thumb.jpg
│   │   ├── foto_defeito.jpg
│   │   └── nota_abatimento.pdf
│   └── 0002\...
├── backups\
│   └── 2026-05-20_backup.zip
└── config.json
```

- **Uma pasta por devolução** (nome = ID com zero-padding)
- **Thumbnail** da foto principal é gerado automaticamente (Pillow, ~200x200, JPEG)
- `config.json` guarda preferências (pasta de backup, frequência, retenção)

### Tipos de arquivo aceitos

PDF, JPG/JPEG, PNG, WEBP. Outros tipos são rejeitados com mensagem clara.

### Limite por arquivo

20 MB.

## 7. Backup

### Formato

Arquivo `.zip` único contendo:
- `dados.db`
- pasta `anexos/` completa
- `config.json`

Restauração = extrair o zip de volta sobre a pasta de dados.

### Quando roda (v1)

**Ao fechar o app**, automaticamente. A v1 implementa apenas esta opção, mas a estrutura suporta as outras (diário, semanal, manual) para versões futuras.

### Onde

Pasta default: `AppData\Local\SimonettoDevolucoes\backups\`
Configurável pelo usuário — quando a loja migrar pro Drive, basta apontar para a pasta sincronizada (ex: `OneDrive\Devoluções\Backups\`).

### Rotação

Mantém os **últimos 30** backups, apaga os mais antigos (configurável).

### Aviso de backup desatualizado

Se o último backup tem mais de 7 dias (ou nunca foi feito), aparece banner amarelo no topo da Tela 1 com botão "Fazer backup agora".

## 8. Lixeira (Soft Delete)

- Excluir uma devolução define `excluido_em = NOW()`
- Devolução sai da listagem principal e aparece em **🗑️ Lixeira**
- Permanece restaurável por **30 dias**
- Após 30 dias, expurgo automático (registro + arquivos do disco apagados) na próxima abertura do app
- Anexos só são removidos do disco no expurgo definitivo

## 9. Arquitetura do Código

Arquitetura em camadas: `ui → services → repositories → db`. A UI nunca acessa o banco diretamente.

```
simonetto_devolucoes/
├── pyproject.toml
├── README.md
├── main.py
├── app/
│   ├── config.py
│   ├── constants.py
│   ├── db.py
│   ├── models/         (marca, devolucao, anexo, historico)
│   ├── repositories/   (marcas_repo, devolucoes_repo, anexos_repo)
│   ├── services/       (devolucao_service, anexo_service, backup_service, lixeira_service)
│   └── ui/
│       ├── layout.py
│       ├── pages/      (lista, marcas, lixeira, configuracoes)
│       └── components/ (form_devolucao, detalhe, badge_status, upload_anexo)
├── tests/
└── scripts/
    └── seed_demo.py
```

### Responsabilidades

- **`models/`**: classes Python (SQLAlchemy) representando as tabelas
- **`repositories/`**: CRUD "burro" — SELECT/INSERT/UPDATE puros
- **`services/`**: regras de negócio (ex: ao mudar status, gravar histórico; ao salvar anexo, gerar thumbnail; ao excluir, soft delete; etc.)
- **`ui/`**: NiceGUI puro — formulários, listas, navegação. Chama services.

### Dependências principais

- `nicegui` — UI
- `sqlalchemy` — ORM
- `pillow` — thumbnails
- `pydantic` — validação de formulários
- `pytest` — testes

### Gerenciador de pacotes

`uv` (lockfile reprodutível, instalação rápida).

### Empacotamento (versão posterior)

Fora de escopo da v1. Estará previsto via `pyinstaller` quando o app estiver maduro, para gerar um `.exe` único.

## 10. Estratégia de Testes

- **Services** têm cobertura ampla (concentram as regras: histórico, thumbnail, backup, lixeira, expurgo)
- **Repositories** têm testes básicos (CRUD funciona)
- **UI** não tem testes automatizados (custo > benefício para um app desse porte e usuário único)
- Banco de teste: SQLite em memória (`sqlite:///:memory:`), isolado por teste

## 11. Decisões e Trade-offs Registrados

| Decisão | Alternativa considerada | Por que |
|---|---|---|
| 3 eixos independentes | Workflow por marca | Marca muda processo com o tempo; eixos cobrem 100% dos casos atuais sem manutenção |
| NiceGUI | PyQt, Flask+HTMX, Streamlit | UI moderna sem HTML; migração futura pra web é trivial |
| SQLite | Postgres local | Zero config, arquivo único = backup trivial |
| Lixeira 30 dias | Delete direto com confirmação | Volume baixo, risco de perda > custo de implementação |
| Backup ao fechar | Diário/semanal/manual | Volume baixo, simples e seguro; outras opções ficam no seletor para futuro |
| `uv` | `pip+venv`, `poetry` | Mais rápido e moderno; equivalente em funcionalidade |
| Sem `.exe` na v1 | Empacotar logo | Validar funcionamento primeiro; empacotar depois |
| Sem testes de UI | Cobertura ampla | Custo alto, ROI baixo em app single-user |

## 12. Próximos Passos

1. Criar plano de implementação detalhado (próximo documento, via skill `writing-plans`)
2. Implementar v1 seguindo TDD onde aplicável (services)
3. Popular com `seed_demo.py` para validar fluxos
4. Uso real por algumas semanas → coletar feedback → planejar v2 (empacotamento `.exe`, mais opções de backup, eventualmente web)
