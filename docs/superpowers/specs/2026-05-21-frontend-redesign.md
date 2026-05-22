# Front-end Redesign — Loja Simonetto

**Data:** 2026-05-21
**Status:** Design aprovado, aguardando plano de implementação
**Autor:** Matheus Simonetto + Claude

## 1. Contexto

O app está funcional mas com aparência de protótipo (Quasar padrão em tons azul/cinza, baixa polidez visual). Precisa de redesenho com identidade visual moderna, sóbria e tecnológica. Decisão: **direção A — Vercel / Linear**, dark-first, accent branco.

### Premissas

- Continua single-user desktop, mesmo backend, mesma stack (NiceGUI + SQLite)
- Sem mudanças de modelo de dados nem de regras de negócio
- Mantém todas as funcionalidades existentes — só muda apresentação e algumas interações
- Mantém o fluxo de navegação geral, mas refina cada superfície

### Não-objetivos

- Não muda banco, models, services
- Não adiciona tema claro nesta versão (dark-only)
- Não muda navegação principal (continua sidebar à esquerda)
- Não muda fluxo de criação/edição (continua via painel lateral direito)

## 2. Sistema visual

### Paleta

| Token | Hex | Uso |
|---|---|---|
| `bg-base` | `#0a0a0a` | fundo de superfícies principais |
| `bg-elevated` | `#0d0d0d` | cards levemente acima |
| `bg-hover` | `#161616` | hover sobre items clicáveis |
| `bg-active` | `#1a1a1a` | item ativo (menu, aba) |
| `border-subtle` | `#1f1f1f` | divisores e bordas de cards |
| `border-faint` | `#161616` | divisores entre rows |
| `text-primary` | `#fafafa` | títulos, texto principal |
| `text-secondary` | `#999999` | labels, meta |
| `text-muted` | `#666666` | data, hints |
| `accent` | `#fafafa` | botão primário (branco com texto preto) |
| `danger` | `#ef4444` | botão de excluir / erros |
| `waiting` | `#fbbf24` | flag "aguardando retorno" (mantém amarelo) |

### Cores semânticas (mantidas dos 3 eixos)

Status do processo:
- `red` `#f87171` — Defeito identificado
- `yellow` `#fbbf24` — Sinalizado
- `orange` `#fb923c` — Pendente ressarcimento
- `green` `#4ade80` — Ressarcido

Destino físico:
- `slate` `#94a3b8` — Na loja
- `blue` `#60a5fa` — Recolhido
- `purple` `#c084fc` — Enviado
- `zinc` `#52525b` — Descartado

Em badges no estilo dark, cor da letra = cor semântica, borda = mesma cor com 30% alpha, fundo = transparente. Bolinha (dot) à esquerda também na cor semântica.

### Tipografia

- Fonte principal: **Inter** (web font local — baixar uma vez, servir local)
- Fonte mono (datas, refs, NF): **JetBrains Mono** (web font local)
- Tamanhos: 22px (h1) · 16px (h2) · 13px (corpo) · 11px (caption/label uppercase) · 10px (mono small)

### Espaçamento e bordas

- Grid base de **4px** (todos os spacings são múltiplos: 4, 8, 12, 16, 20, 24, 32)
- Border-radius padrão: **6px** (inputs, botões), **10px** (cards grandes)
- Sombras: ausentes (estilo Vercel é flat — usa borda fina em vez de sombra)

## 3. Layout principal (app shell)

### Sidebar retrátil

**Dois estados, alternáveis por:**
- Botão `◂` / `▸` no canto superior da sidebar
- Atalho de teclado **Ctrl+B**

**Estado expandido** (largura 200px, default):
- Cabeçalho com nome "Simonetto" + sub "Devoluções" + botão de toggle
- Links: ícone + texto, padding 7px 10px, hover bg-hover, ativo bg-active + texto branco

**Estado recolhido** (largura 48px):
- Topo: logo "S" em quadrado branco-gradiente 36x36 (substitui o cabeçalho)
- Botão de toggle abaixo do logo
- Links: só ícone, 36x36, tooltip aparece à direita ao hover

**Persistência:** o estado fica salvo em `config.json` (campo `sidebar_collapsed: bool`). Reabre como fechou.

**Transição:** animação CSS 150ms ease-out na largura.

### Área de conteúdo

- Padding interno 24px
- Não tem header global (cada página renderiza seu próprio título)

## 4. Página: Lista de Devoluções

Layout em rows, não cards. Estilo "Linear inbox".

### Cabeçalho da página

- Título "Devoluções" em h1
- Linha de filtros logo abaixo, separada por borda inferior:
  - Input de busca (largura 220px, placeholder "Buscar...")
  - Selects: Marca · Status · Destino (largura compacta, label oculto, value visível)
  - Checkbox "Só aguardando retorno"
  - Botão **+ Nova Devolução** (alinhado à direita, branco com texto preto)

### Banner de backup desatualizado

Quando aplicável, banner sutil acima dos filtros: fundo amber/8% alpha, borda amber/30% alpha, texto amber-300. Mensagem + botão "Fazer backup agora".

### Row de devolução

Grid: `[thumb 56px] [conteúdo principal flex] [pill status] [pill destino] [pill forma]`

- **Thumb**: 56x56, border-radius 6px, mostra `thumb_url_de(primeira_imagem)` ou placeholder `📷` em gradient cinza
- **Conteúdo principal**:
  - Linha 1: `{marca} · {modelo}` + (se houver) `· ref {referencia}` — text-primary 14px medium
  - Linha 2: `Devolvido em {data}` + (se cliente) `· {cliente_nome}` + (se aguardando) `⏳ aguardando` em amber — text-secondary 12px
- **3 pills semânticas** (cor + dot)

Hover na row: bg muda pra `#0f0f0f`. Cursor pointer.

Click na row → abre painel de detalhe (§5).

### Empty state

Quando filtros não retornam nada: ícone 📭 grande cinza + "Nenhuma devolução com esses filtros" + botão "Limpar filtros".

Quando não há nenhuma devolução no banco: ícone 📋 grande + "Você ainda não tem devoluções" + botão "+ Nova Devolução".

## 5. Painel de Detalhe (lateral direito)

Abre por cima da lista, fixo à direita, largura **560px**. Lista atrás fica visível com opacity 35% e pointer-events none.

Animação: slide-in 200ms ease-out + fade do backdrop.

Fecha com: botão ✕, tecla ESC, ou click fora.

### Header sticky

- À esquerda: label uppercase 11px com nome da marca + título 15px com modelo
- À direita: botão `⋯` (menu de mais opções — placeholder pra futuro) e botão `✕` (fechar)
- Borda inferior fina

### Body (scroll vertical)

**Hero** (top):
- Imagem principal 120x120 (clicável → abre lightbox)
- À direita: data de devolução · ref em mono · linha de 3 pills

**Pills clicáveis (nova UX)**:
Cada uma das 3 pills (status, destino, forma) tem um indicador `▾` à direita. Click abre dropdown com as outras opções. Selecionar muda direto, sem precisar abrir "Editar". Geração de histórico automática (mesma regra do `devolucao_service`).

**Seção: Detalhes** (definition list)
- Quantidade · Valor (R$ formatado) · Cliente · Contato · NF origem · NF abatimento · Data da compra original
- Layout: `dt` 120px cinza, `dd` flex texto principal
- NFs em mono pequeno
- Link "editar" no header da seção → abre o form

**Seção: Imagens (N)**
- Grid de cards 4 colunas (gap 8px, aspect-ratio 1)
- Cada card: imagem + (se principal) badge `★ PRINCIPAL` no canto superior esquerdo + 4 mini-botões no canto inferior direito: `◀ ▶ ★ 🗑`
- Borda branca destaca o card principal
- Último item do grid: upload-zone dashed clicável "+ adicionar"

**Seção: Documentos (N)**
- Lista de items (ícone PDF + nome + link "abrir" + link "remover")
- Upload-zone dashed abaixo: "📎 arraste um PDF ou clique pra anexar"

**Seção: Observações**
- Box bg `bg-elevated`, padding 10x12, mostra texto com `white-space: pre-wrap`
- Link "editar" no header da seção

**Seção: Histórico**
- Timeline vertical com linha guia (1px `border-subtle`) à esquerda
- Cada item: pontinho colorido (semântica do status), data/hora em mono 10px cinza, descrição "Status → X" ou "Destino → Y" com valor em bold

### Footer sticky

- À esquerda: botão `🗑 Mover pra lixeira` (texto vermelho, borda vermelho/30%)
- À direita: botão primário `✎ Editar` (branco, texto preto)

## 6. Painel de Form (Nova/Editar)

**Mesma posição e dimensões do painel de detalhe** (560px direito). O usuário não percebe troca de "tipo de modal" — só percebe que o conteúdo virou um formulário.

### Header

Igual ao do detalhe, mas título é "Nova devolução" ou "Editar devolução".

### Body

Seções com mesma divisão visual do detalhe, mas com inputs. Espaçamento generoso entre seções (24px).

- **Marca *** (select) — auto-sugere `forma_ressarcimento_padrao` quando muda
- **Produto**
  - Modelo *
  - Referência
  - Quantidade · Valor custo (R$) — em duas colunas
  - Defeito
  - Upload de imagens (multi, drag-and-drop)
- **Datas**
  - Data devolução *
  - Data da compra original
- **Notas Fiscais (opcional)**
  - NF origem · NF abatimento
- **Cliente (opcional)**
  - Nome · Contato
  - Checkbox "Cliente aguardando retorno"
- **Status** — 3 selects (status, destino, forma)
- **Observações** — textarea

Inputs:
- bg `bg-base`, borda `border-subtle`, padding 6x10, font 13px
- Focus: borda `text-primary` (branco), sem outline
- Placeholder: `text-muted`
- Labels: 11px uppercase letter-spacing 1.2px `text-secondary`

### Footer

- Botão "Cancelar" (transparente, sem borda)
- Botão primário "Salvar" (branco)

## 7. Páginas secundárias (mesmo padrão)

### Marcas

- Título "Marcas" + botão "+ Nova marca" no header da página
- Lista de rows simples: `nome` + label "Padrão: {forma}" + observações em cinza + ícones de editar/excluir à direita
- Modal de criar/editar = pequeno dialog centralizado (não painel lateral — formulário simples)

### Lixeira

- Título "Lixeira" + sub "Auto-expurgo em 30 dias"
- Mesmas rows da lista, mas com botões "Restaurar" e "Apagar agora" à direita
- Empty state quando vazia

### Configurações

- Título "Configurações"
- Seções: Dados (paths read-only) · Backup (form com inputs) · Backup manual (botão + lista dos últimos)
- Layout de form vertical com max-width 600px

## 8. Componentes globais

### Toasts (notificações)

- Posição: bottom-right
- Card 360px, padding 12x16, borda colorida à esquerda (4px)
- Variantes: success (verde), error (vermelho), warning (amber), info (azul)
- Auto-dismiss 4s, hover pausa

### Dialogs de confirmação

- Dialog centralizado pequeno (~400px)
- Mesmo estilo dos cards: bg-elevated, borda fina
- Pergunta + 2 botões (Cancelar / Confirmar)

### Lightbox de imagem

Click em imagem do detalhe abre lightbox fullscreen com:
- Backdrop preto 90%
- Imagem centralizada com largura/altura máxima da viewport
- Navegação (se múltiplas imagens): setas `← →` nos lados, contador "2 / 5" no topo
- Fecha com ESC ou click no backdrop

## 9. Mudanças técnicas necessárias

### CSS global

Como NiceGUI usa Quasar por baixo, várias classes Quasar precisam ser sobrescritas. Vou adicionar um `app.css` carregado via `ui.add_head_html()` no `main.py` ou via `app.add_static_files`.

Estratégia: definir variáveis CSS no `:root` e usar nelas em todos os overrides.

### Componentes a refatorar

- `app/ui/layout.py` — sidebar retrátil com estado persistido em `config.json`
- `app/ui/pages/lista.py` — novo layout de rows + filtros redesenhados
- `app/ui/components/detalhe_devolucao.py` — painel direito + badges clicáveis + nova estrutura de seções
- `app/ui/components/form_devolucao.py` — painel direito redesenhado, inputs com novo estilo
- `app/ui/components/badge_status.py` — pills com dot + variante "clicável" (com `▾`)
- `app/ui/pages/marcas.py`, `lixeira.py`, `configuracoes.py` — adaptar pro novo visual

### Novos componentes

- `app/ui/components/pill_dropdown.py` — badge clicável que vira dropdown
- `app/ui/components/lightbox.py` — modal fullscreen pra imagens

### Novos campos em Config

- `sidebar_collapsed: bool` (default False) — estado da sidebar

### Mudanças em backend (mínimas)

- Nenhuma mudança em models, repos, services existentes
- `config.py` ganha o campo `sidebar_collapsed`
- Nenhuma migração de DB necessária

## 10. Decisões e Trade-offs

| Decisão | Alternativa | Por que |
|---|---|---|
| Dark-only nesta versão | Light + dark com toggle | Foco. Tema claro vira v3 se realmente precisar |
| Accent branco | Ciano / indigo / verde | Mais sóbrio, menos data, casa com Vercel |
| Sidebar retrátil | Sidebar fixa só / top-tabs / só ícones | Híbrido cobre os 2 modos de uso (focado vs explorando) |
| Painel direito pra detalhe e form | Full-page navigation | Mantém contexto da lista, padrão moderno (Linear) |
| Badges clicáveis pra mudar status | Sempre via "Editar" | Reduz fricção pra ação mais comum |
| Sem sombras (flat) | Sombras suaves | Vercel é flat. Sombras em dark ficam estranhas |
| Inter + JetBrains Mono local | Google Fonts CDN | Offline-first, sem internet em runtime |

## 11. Critérios de sucesso

- Visual coerente com Vercel/Linear/GitHub dark (tipografia, espaçamento, paleta)
- Lista mais escaneável que a versão atual (1 row por devolução, badges semânticos óbvios)
- Mudança de status em < 2 clicks (badge clicável)
- Sidebar não atrapalha em telas pequenas (modo recolhido)
- Tudo continua funcionando offline (fontes locais, sem CDN)
- 32+ testes existentes continuam passando (sem mudanças em backend)

## 12. Próximos passos

1. Criar plano de implementação detalhado (via `writing-plans`)
2. Executar em fases: sistema visual base → lista → detalhe → form → páginas secundárias → polimento
3. Validar com o usuário a cada fase
