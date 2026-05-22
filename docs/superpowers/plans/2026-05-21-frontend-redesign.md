# Front-end Redesign — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aplicar redesign visual estilo Vercel/Linear dark com sidebar retrátil, painéis laterais redesenhados, badges clicáveis e nova hierarquia visual — sem mudanças de backend.

**Architecture:** CSS global com variáveis (carregado via `ui.add_head_html`), refatoração das UI pages/components existentes, novos componentes (`pill_dropdown`), persistência de preferência da sidebar em `config.json`.

**Tech Stack:** NiceGUI 3.x, Quasar (substrato), CSS custom (override de Quasar), Inter (font system stack).

**Spec de referência (fonte da verdade visual):** `docs/superpowers/specs/2026-05-21-frontend-redesign.md`

---

## Mapa de arquivos

```
app/
├── config.py                              # MODIFY: adicionar sidebar_collapsed
├── ui/
│   ├── assets/
│   │   └── app.css                        # CREATE: tema global + variáveis
│   ├── layout.py                          # REWRITE: sidebar retrátil
│   ├── pages/
│   │   ├── lista.py                       # REWRITE: rows + filtros redesenhados
│   │   ├── marcas.py                      # REWRITE: novo visual
│   │   ├── lixeira.py                     # REWRITE: novo visual
│   │   └── configuracoes.py               # REWRITE: novo visual
│   └── components/
│       ├── badge_status.py                # REWRITE: pílulas com dot
│       ├── pill_dropdown.py               # CREATE: pílula clicável → dropdown
│       ├── form_devolucao.py              # REWRITE: painel novo
│       └── detalhe_devolucao.py           # REWRITE: painel novo
└── main.py                                # MODIFY: carregar app.css + servir /assets
tests/
└── test_config.py                         # MODIFY: cobrir sidebar_collapsed
```

---

## FASE A — Fundação visual

### Task 1: Tema CSS global + variáveis + carga no main.py

**Files:**
- Create: `app/ui/assets/app.css`
- Modify: `main.py` (adicionar `app.add_static_files('/assets', app/ui/assets)` + `ui.add_head_html`)

- [ ] **Step 1: Criar `app/ui/assets/app.css` com variáveis e tema base**

```css
:root {
  /* superfícies */
  --bg-base: #0a0a0a;
  --bg-elevated: #0d0d0d;
  --bg-hover: #161616;
  --bg-active: #1a1a1a;
  --border-subtle: #1f1f1f;
  --border-faint: #161616;
  /* texto */
  --text-primary: #fafafa;
  --text-secondary: #999999;
  --text-muted: #666666;
  /* accent */
  --accent: #fafafa;
  --accent-fg: #000000;
  --danger: #ef4444;
  --waiting: #fbbf24;
  /* status processo */
  --status-red: #f87171;
  --status-yellow: #fbbf24;
  --status-orange: #fb923c;
  --status-green: #4ade80;
  /* destino físico */
  --dest-slate: #94a3b8;
  --dest-blue: #60a5fa;
  --dest-purple: #c084fc;
  --dest-zinc: #52525b;
  /* tipografia */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', 'Cascadia Code', Menlo, monospace;
  /* radius */
  --r-sm: 4px;
  --r-md: 6px;
  --r-lg: 10px;
}

/* ===== reset Quasar/NiceGUI para tema dark ===== */
html, body, .q-page, .q-page-container, .nicegui-content {
  background: var(--bg-base) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-sans) !important;
}
.q-drawer, .q-header { background: var(--bg-base) !important; box-shadow: none !important; }
.q-card { background: var(--bg-elevated) !important; border: 1px solid var(--border-subtle) !important; box-shadow: none !important; border-radius: var(--r-lg) !important; }
.q-separator { background: var(--border-subtle) !important; }

/* inputs */
.q-field__control { background: var(--bg-base) !important; border-radius: var(--r-md) !important; }
.q-field--outlined .q-field__control:before { border-color: var(--border-subtle) !important; }
.q-field__native, .q-field__input { color: var(--text-primary) !important; }
.q-field__label { color: var(--text-secondary) !important; }

/* botões */
.q-btn { font-family: var(--font-sans) !important; text-transform: none !important; letter-spacing: 0 !important; font-weight: 500 !important; }
.q-btn.bg-primary { background: var(--accent) !important; color: var(--accent-fg) !important; }

/* ===== utilitários custom ===== */
.app-page-title { font-size: 22px; font-weight: 600; color: var(--text-primary); }
.app-section-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1.2px; color: var(--text-secondary); font-weight: 600; }
.app-mono { font-family: var(--font-mono); }
.app-divider { height: 1px; background: var(--border-subtle); margin: 16px 0; }

/* pílula */
.app-pill {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px; padding: 3px 9px; border-radius: 20px;
  border: 1px solid; font-weight: 500; line-height: 1;
}
.app-pill .dot { width: 6px; height: 6px; border-radius: 50%; }
.app-pill.clickable { cursor: pointer; transition: filter .15s; }
.app-pill.clickable:hover { filter: brightness(1.3); }
.app-pill.clickable::after { content: '▾'; font-size: 9px; opacity: .6; margin-left: 2px; }

/* row de devolução */
.app-row {
  display: grid; grid-template-columns: 56px 1fr auto auto auto;
  gap: 16px; padding: 14px 8px; border-bottom: 1px solid var(--border-faint);
  align-items: center; cursor: pointer; transition: background .15s;
}
.app-row:hover { background: #0f0f0f; }
.app-row:last-child { border-bottom: none; }

/* sidebar */
.app-sidebar-link {
  display: flex; align-items: center; gap: 10px; padding: 7px 10px;
  border-radius: var(--r-md); color: var(--text-secondary);
  font-size: 13px; cursor: pointer; transition: background .15s, color .15s;
  text-decoration: none;
}
.app-sidebar-link:hover { background: var(--bg-hover); color: var(--text-primary); }
.app-sidebar-link.active { background: var(--bg-active); color: var(--text-primary); }
.app-sidebar-icon-only { width: 36px; height: 36px; justify-content: center; padding: 0; }

/* upload zones */
.app-upload-zone {
  border: 1px dashed var(--border-subtle); border-radius: var(--r-md);
  padding: 14px; text-align: center; color: var(--text-secondary);
  font-size: 12px; cursor: pointer; transition: border-color .15s, color .15s;
}
.app-upload-zone:hover { border-color: var(--text-secondary); color: var(--text-primary); }

/* timeline */
.app-timeline { position: relative; padding-left: 16px; }
.app-timeline::before { content: ''; position: absolute; left: 5px; top: 4px; bottom: 4px; width: 1px; background: var(--border-subtle); }
.app-timeline-item { position: relative; padding-bottom: 12px; }
.app-timeline-item::before { content: ''; position: absolute; left: -14px; top: 5px; width: 8px; height: 8px; border-radius: 50%; background: var(--bg-base); border: 2px solid var(--text-muted); }
.app-timeline-item .time { color: var(--text-muted); font-size: 10px; font-family: var(--font-mono); }
.app-timeline-item .text { color: var(--text-primary); font-size: 12px; margin-top: 2px; }

/* scrollbar dark */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: #3a3a3a; }
```

- [ ] **Step 2: Modificar `main.py` para servir /assets e carregar app.css**

Adicionar logo após `app.add_static_files("/dados", ...)`:

```python
from pathlib import Path
ASSETS_DIR = Path(__file__).parent / "app" / "ui" / "assets"
app.add_static_files("/assets", str(ASSETS_DIR))
ui.add_head_html('<link rel="stylesheet" href="/assets/app.css">')
```

- [ ] **Step 3: Sanity check — app sobe e carrega o CSS**

```bash
uv run python -c "from pathlib import Path; assert (Path('app/ui/assets/app.css')).exists(); print('ok')"
uv run pytest tests/ -q
```
Expected: `ok` + 38 testes passando

- [ ] **Step 4: Commit**

```bash
git add app/ui/assets/app.css main.py
git commit -m "feat(ui): tema CSS global com variaveis e overrides do Quasar"
```

---

### Task 2: Config — campo `sidebar_collapsed`

**Files:**
- Modify: `app/config.py`
- Modify: `tests/test_config.py`

- [ ] **Step 1: Atualizar teste em `tests/test_config.py` (adicionar caso novo)**

Adicionar ao final do arquivo:

```python
def test_config_persists_sidebar_state(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMONETTO_DATA_DIR", str(tmp_path))
    cfg = Config.load()
    assert cfg.sidebar_collapsed is False  # default
    cfg.sidebar_collapsed = True
    cfg.save()
    reloaded = Config.load()
    assert reloaded.sidebar_collapsed is True
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_config.py::test_config_persists_sidebar_state -v
```
Expected: FAIL (`AttributeError: 'Config' object has no attribute 'sidebar_collapsed'`)

- [ ] **Step 3: Adicionar campo em `app/config.py`**

Adicionar a `Config` dataclass:
```python
sidebar_collapsed: bool = False
```

Atualizar `load()` defaults:
```python
defaults = {
    "backup_folder": str(data_dir / "backups"),
    "backup_retention": 30,
    "backup_frequency": "on_close",
    "sidebar_collapsed": False,
}
```

E na construção do retorno:
```python
return cls(
    data_dir=data_dir,
    backup_folder=Path(defaults["backup_folder"]),
    backup_retention=defaults["backup_retention"],
    backup_frequency=defaults["backup_frequency"],
    sidebar_collapsed=defaults["sidebar_collapsed"],
)
```

Atualizar `save()`:
```python
payload = {
    "backup_folder": str(self.backup_folder),
    "backup_retention": self.backup_retention,
    "backup_frequency": self.backup_frequency,
    "sidebar_collapsed": self.sidebar_collapsed,
}
```

- [ ] **Step 4: Rodar todos**

```bash
uv run pytest tests/ -q
```
Expected: 39 passed (38 + 1 novo)

- [ ] **Step 5: Commit**

```bash
git add app/config.py tests/test_config.py
git commit -m "feat(config): persiste sidebar_collapsed entre sessoes"
```

---

### Task 3: Sidebar retrátil

**Files:**
- Rewrite: `app/ui/layout.py`

- [ ] **Step 1: Substituir conteúdo de `app/ui/layout.py`**

```python
from nicegui import app, ui

from app.config import Config

PAGINAS = [
    ("/", "Devoluções", "list_alt", "📋"),
    ("/marcas", "Marcas", "label", "🏷️"),
    ("/lixeira", "Lixeira", "delete", "🗑️"),
    ("/configuracoes", "Configurações", "settings", "⚙️"),
]


def montar_layout(titulo_pagina: str) -> ui.column:
    """Monta sidebar retrátil + container de conteúdo."""
    cfg = Config.load()
    state = {"collapsed": cfg.sidebar_collapsed}

    drawer = ui.left_drawer(value=True, fixed=True, bordered=False) \
        .props("width=200 mini-to-overlay=false") \
        .style("background: var(--bg-base); border-right: 1px solid var(--border-subtle); padding: 14px 8px;")

    def aplicar_estado():
        """Aplica largura e oculta/mostra labels via JS conforme state['collapsed']."""
        largura = 48 if state["collapsed"] else 200
        drawer.props(f"width={largura}")
        ui.run_javascript(
            f"document.querySelectorAll('.sidebar-label').forEach(el => "
            f"el.style.display = '{('none' if state['collapsed'] else 'inline')}');"
            f"document.querySelectorAll('.app-sidebar-link').forEach(el => "
            f"el.classList.toggle('app-sidebar-icon-only', {str(state['collapsed']).lower()}));"
        )

    def toggle():
        state["collapsed"] = not state["collapsed"]
        c = Config.load()
        c.sidebar_collapsed = state["collapsed"]
        c.save()
        aplicar_estado()

    with drawer:
        with ui.row().classes("items-center justify-between w-full").style("padding: 4px 6px 16px;"):
            with ui.column().classes("gap-0 sidebar-label"):
                ui.label("Simonetto").style("font-size: 12px; color: var(--text-primary); font-weight: 600;")
                ui.label("Devoluções").style("font-size: 10px; color: var(--text-muted);")
            ui.button(on_click=toggle, icon="chevron_left") \
                .props("flat dense round size=sm").style("color: var(--text-secondary);")

        for rota, label, _icone, emoji in PAGINAS:
            with ui.link(target=rota).classes("app-sidebar-link"):
                ui.label(emoji).style("font-size: 14px;")
                ui.label(label).classes("sidebar-label")

    # Header minimal: só o titulo da pagina
    with ui.header(elevated=False).style("background: var(--bg-base); border-bottom: 1px solid var(--border-subtle); padding: 12px 24px;"):
        ui.label(titulo_pagina).classes("app-page-title")

    # Atalho Ctrl+B
    ui.keyboard(on_key=lambda e: (e.key.name == "b" and e.modifiers.ctrl and toggle()))

    # Aplica estado inicial após DOM montar
    ui.timer(0.1, aplicar_estado, once=True)

    container = ui.column().classes("w-full").style("padding: 24px;")
    return container
```

- [ ] **Step 2: Smoke test**

```bash
uv run python -c "from app.ui.layout import montar_layout; print('ok')"
uv run pytest tests/ -q
```
Expected: `ok` + 39 passed

- [ ] **Step 3: Manual test — abrir o app, conferir que sidebar abre/recolhe**

```bash
uv run python main.py
```
Verificar: clique no botão ◂/▸ alterna a sidebar; Ctrl+B também; ao reabrir, mantém o último estado.

- [ ] **Step 4: Commit**

```bash
git add app/ui/layout.py
git commit -m "feat(ui): sidebar retratil com toggle, Ctrl+B e persistencia"
```

---

## FASE B — Componentes reutilizáveis

### Task 4: Badge/Pill — refatorar `badge_status.py` para novo estilo

**Files:**
- Rewrite: `app/ui/components/badge_status.py`

- [ ] **Step 1: Substituir conteúdo do arquivo**

```python
"""Pílulas semânticas dos 3 eixos (status, destino, forma de ressarcimento).

Cada função renderiza uma pílula estática (apenas exibição).
Para pílulas clicáveis com dropdown, ver pill_dropdown.py.
"""
from nicegui import ui

from app.constants import (
    DESTINO_FISICO_LABELS, DestinoFisico,
    FORMA_RESSARCIMENTO_LABELS, FormaRessarcimento,
    STATUS_PROCESSO_LABELS, StatusProcesso,
)

# Mapeamento de cores Quasar (usadas no plano antigo) para as CSS vars do novo tema
_COR_PARA_VAR = {
    "red": "var(--status-red)",
    "yellow": "var(--status-yellow)",
    "orange": "var(--status-orange)",
    "green": "var(--status-green)",
    "grey": "var(--dest-slate)",
    "blue": "var(--dest-blue)",
    "purple": "var(--dest-purple)",
    "black": "var(--dest-zinc)",
}


def _pill(label: str, cor_quasar: str, icone: str) -> ui.html:
    cor = _COR_PARA_VAR.get(cor_quasar, "var(--text-secondary)")
    return ui.html(
        f'<span class="app-pill" '
        f'style="color: {cor}; border-color: color-mix(in srgb, {cor} 30%, transparent);">'
        f'<span class="dot" style="background: {cor};"></span>'
        f'{icone} {label}'
        f'</span>'
    )


def badge_status_processo(status: StatusProcesso) -> ui.html:
    label, cor, icone = STATUS_PROCESSO_LABELS[status]
    return _pill(label, cor, icone)


def badge_destino(destino: DestinoFisico) -> ui.html:
    label, cor, icone = DESTINO_FISICO_LABELS[destino]
    return _pill(label, cor, icone)


def badge_forma(forma: FormaRessarcimento | None) -> ui.html | None:
    if forma is None:
        return None
    label, icone = FORMA_RESSARCIMENTO_LABELS[forma]
    return ui.html(
        f'<span class="app-pill" '
        f'style="color: var(--text-secondary); border-color: var(--border-subtle);">'
        f'{icone} {label}'
        f'</span>'
    )
```

- [ ] **Step 2: Sanity check**

```bash
uv run python -c "from app.ui.components import badge_status; print('ok')"
uv run pytest tests/ -q
```
Expected: `ok` + 39 passed

- [ ] **Step 3: Commit**

```bash
git add app/ui/components/badge_status.py
git commit -m "feat(ui): pilulas semanticas com dot + cores via CSS vars"
```

---

### Task 5: Componente `pill_dropdown` — pílula clicável que abre dropdown

**Files:**
- Create: `app/ui/components/pill_dropdown.py`

- [ ] **Step 1: Criar `app/ui/components/pill_dropdown.py`**

```python
"""Pílulas clicáveis que abrem dropdown para mudar status/destino/forma direto
do detalhe da devolução, sem precisar abrir o formulário de edição.
"""
from typing import Callable, Optional
from nicegui import ui

from app.constants import (
    DESTINO_FISICO_LABELS, DestinoFisico,
    FORMA_RESSARCIMENTO_LABELS, FormaRessarcimento,
    STATUS_PROCESSO_LABELS, StatusProcesso,
)
from app.ui.components.badge_status import _COR_PARA_VAR


def _pill_button(label: str, cor_quasar: str, icone: str,
                  on_click: Callable[[], None]) -> ui.element:
    cor = _COR_PARA_VAR.get(cor_quasar, "var(--text-secondary)")
    el = ui.html(
        f'<span class="app-pill clickable" '
        f'style="color: {cor}; border-color: color-mix(in srgb, {cor} 30%, transparent);">'
        f'<span class="dot" style="background: {cor};"></span>'
        f'{icone} {label}'
        f'</span>'
    ).on("click", lambda _: on_click())
    return el


def pill_dropdown_status(atual: StatusProcesso,
                          on_change: Callable[[StatusProcesso], None]) -> None:
    label, cor, icone = STATUS_PROCESSO_LABELS[atual]
    with ui.element("div").style("display: inline-block; position: relative;"):
        def abrir():
            with ui.menu() as menu:
                for s in StatusProcesso:
                    if s == atual:
                        continue
                    s_label, _, s_icone = STATUS_PROCESSO_LABELS[s]
                    ui.menu_item(f"{s_icone} {s_label}",
                                 lambda s=s: (on_change(s), menu.close()))
            menu.open()
        _pill_button(label, cor, icone, abrir)


def pill_dropdown_destino(atual: DestinoFisico,
                           on_change: Callable[[DestinoFisico], None]) -> None:
    label, cor, icone = DESTINO_FISICO_LABELS[atual]
    with ui.element("div").style("display: inline-block; position: relative;"):
        def abrir():
            with ui.menu() as menu:
                for d in DestinoFisico:
                    if d == atual:
                        continue
                    d_label, _, d_icone = DESTINO_FISICO_LABELS[d]
                    ui.menu_item(f"{d_icone} {d_label}",
                                 lambda d=d: (on_change(d), menu.close()))
            menu.open()
        _pill_button(label, cor, icone, abrir)


def pill_dropdown_forma(atual: Optional[FormaRessarcimento],
                         on_change: Callable[[Optional[FormaRessarcimento]], None]) -> None:
    if atual is None:
        label, icone = ("Sem forma", "❓")
    else:
        label, icone = FORMA_RESSARCIMENTO_LABELS[atual]
    cor = "var(--text-secondary)"

    with ui.element("div").style("display: inline-block; position: relative;"):
        def abrir():
            with ui.menu() as menu:
                for f in FormaRessarcimento:
                    if f == atual:
                        continue
                    f_label, f_icone = FORMA_RESSARCIMENTO_LABELS[f]
                    ui.menu_item(f"{f_icone} {f_label}",
                                 lambda f=f: (on_change(f), menu.close()))
            menu.open()
        el = ui.html(
            f'<span class="app-pill clickable" '
            f'style="color: {cor}; border-color: var(--border-subtle);">'
            f'{icone} {label}'
            f'</span>'
        ).on("click", lambda _: abrir())
```

- [ ] **Step 2: Sanity check**

```bash
uv run python -c "from app.ui.components import pill_dropdown; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add app/ui/components/pill_dropdown.py
git commit -m "feat(ui): pilulas clicaveis com dropdown para mudar status/destino/forma"
```

---

## FASE C — Lista de devoluções redesenhada

### Task 6: Página `lista.py` no novo visual

**Files:**
- Rewrite: `app/ui/pages/lista.py`

- [ ] **Step 1: Substituir conteúdo do arquivo**

```python
from datetime import date

from nicegui import ui

from app.constants import (
    BANNER_BACKUP_ALERTA_DIAS,
    DestinoFisico, DESTINO_FISICO_LABELS,
    StatusProcesso, STATUS_PROCESSO_LABELS,
)
from app.db import session_scope
from app.repositories import devolucoes_repo, marcas_repo
from app.services import anexo_service, backup_service
from app.ui.components.badge_status import (
    badge_destino, badge_forma, badge_status_processo,
)


def render():
    from app.ui.layout import montar_layout
    from app.ui.components.form_devolucao import abrir_form_devolucao
    from app.ui.components.detalhe_devolucao import abrir_detalhe

    montar_layout("Devoluções")

    filtros = {"busca": "", "marca_id": None, "status": None,
               "destino": None, "aguardando": False}

    container = ui.column().classes("w-full").style("max-width: 1100px;")

    def render_banner_backup():
        info = backup_service.ultimo_backup()
        precisa = False
        msg = ""
        if info is None:
            precisa = True
            msg = "⚠️ Nenhum backup foi feito ainda."
        else:
            dias = (date.today() - info.criado_em.date()).days
            if dias >= BANNER_BACKUP_ALERTA_DIAS:
                precisa = True
                msg = f"⚠️ Último backup há {dias} dias."
        if precisa:
            with ui.row().style(
                "background: rgba(251, 191, 36, .08); "
                "border: 1px solid rgba(251, 191, 36, .25); "
                "border-radius: var(--r-md); padding: 8px 12px; "
                "margin-bottom: 16px; width: 100%; align-items: center;"
            ):
                ui.label(msg).style("color: var(--waiting); font-size: 13px; flex: 1;")
                ui.button("Fazer backup agora",
                          on_click=lambda: (backup_service.criar_backup(),
                                            ui.notify("Backup criado", type="positive"))) \
                    .props("size=sm flat").style("color: var(--waiting);")

    def render_filtros():
        with ui.row().classes("items-center gap-2 w-full") \
                .style("padding-bottom: 12px; border-bottom: 1px solid var(--border-subtle); margin-bottom: 12px;"):
            ui.input(placeholder="Buscar...",
                     on_change=lambda e: filtros.update(busca=e.value) or render_lista()) \
                .props("outlined dense").style("width: 220px;")

            with session_scope() as s:
                marcas = [(m.id, m.nome) for m in marcas_repo.listar(s)]
            opcoes_marca = {None: "Todas marcas"} | {mid: nome for mid, nome in marcas}
            ui.select(opcoes_marca, value=None,
                      on_change=lambda e: filtros.update(marca_id=e.value) or render_lista()) \
                .props("outlined dense").style("width: 160px;")

            opcoes_status = {None: "Status"} | {
                s.value: STATUS_PROCESSO_LABELS[s][0] for s in StatusProcesso
            }
            ui.select(opcoes_status, value=None,
                      on_change=lambda e: filtros.update(
                          status=StatusProcesso(e.value) if e.value else None) or render_lista()) \
                .props("outlined dense").style("width: 180px;")

            opcoes_dest = {None: "Destino"} | {
                d.value: DESTINO_FISICO_LABELS[d][0] for d in DestinoFisico
            }
            ui.select(opcoes_dest, value=None,
                      on_change=lambda e: filtros.update(
                          destino=DestinoFisico(e.value) if e.value else None) or render_lista()) \
                .props("outlined dense").style("width: 160px;")

            ui.checkbox("⏳ aguardando",
                        on_change=lambda e: filtros.update(aguardando=e.value) or render_lista()) \
                .style("color: var(--text-secondary);")

            ui.space()
            ui.button("+ Nova Devolução",
                      on_click=lambda: abrir_form_devolucao(on_save=recarregar)) \
                .props("unelevated").classes("bg-primary")

    lista_container = ui.column().classes("w-full gap-0")

    def render_lista():
        lista_container.clear()
        with session_scope() as s:
            devs = devolucoes_repo.listar_ativas(
                s,
                marca_id=filtros["marca_id"], status=filtros["status"],
                destino=filtros["destino"],
                aguardando_retorno=True if filtros["aguardando"] else None,
                busca=filtros["busca"] or None,
            )
            dados = []
            for d in devs:
                primeira_imagem = next(
                    (a for a in sorted(d.anexos, key=lambda x: (x.ordem, x.criado_em))
                     if a.tipo == "imagem"),
                    None
                )
                thumb = anexo_service.thumb_url_de(primeira_imagem) if primeira_imagem else None
                dados.append({
                    "id": d.id, "marca": d.marca.nome,
                    "modelo": d.produto_modelo, "ref": d.produto_referencia,
                    "data": d.data_devolucao.strftime("%d/%m/%Y"),
                    "cliente": d.cliente_nome, "aguardando": d.cliente_aguardando_retorno,
                    "status": d.status_processo, "destino": d.destino_fisico,
                    "forma": d.forma_ressarcimento, "thumb": thumb,
                })

        with lista_container:
            if not dados:
                # empty state
                with ui.column().classes("items-center w-full") \
                        .style("padding: 60px 20px; color: var(--text-muted);"):
                    ui.label("📭").style("font-size: 48px; margin-bottom: 12px;")
                    if any([filtros["busca"], filtros["marca_id"], filtros["status"],
                            filtros["destino"], filtros["aguardando"]]):
                        ui.label("Nenhuma devolução com esses filtros.") \
                            .style("color: var(--text-secondary);")
                    else:
                        ui.label("Você ainda não tem devoluções.") \
                            .style("color: var(--text-secondary);")
                        ui.button("+ Nova Devolução",
                                  on_click=lambda: abrir_form_devolucao(on_save=recarregar)) \
                            .props("unelevated").classes("bg-primary").style("margin-top: 12px;")
                return

            for d in dados:
                with ui.element("div").classes("app-row") \
                        .on("click", lambda _, i=d["id"]: abrir_detalhe(i, on_save=recarregar)):
                    # thumb
                    if d["thumb"]:
                        ui.image(d["thumb"]).style(
                            "width: 56px; height: 56px; border-radius: 6px; "
                            "object-fit: cover; flex-shrink: 0;"
                        )
                    else:
                        ui.html(
                            '<div style="width:56px; height:56px; border-radius:6px; '
                            'background: linear-gradient(135deg, #1a1a1a, #2a2a2a); '
                            'display:flex; align-items:center; justify-content:center; '
                            'color:#4a4a4a; font-size:24px;">📷</div>'
                        )
                    # main
                    with ui.column().classes("gap-1").style("min-width: 0;"):
                        ref_part = f" · ref {d['ref']}" if d['ref'] else ""
                        ui.label(f"{d['marca']} · {d['modelo']}{ref_part}").style(
                            "color: var(--text-primary); font-size: 14px; font-weight: 500;"
                        )
                        meta = f"Devolvido em {d['data']}"
                        if d['cliente']:
                            meta += f"   ·   Cliente: {d['cliente']}"
                            if d['aguardando']:
                                meta += "  ⏳"
                        ui.label(meta).style("color: var(--text-secondary); font-size: 12px;")
                    badge_status_processo(d["status"])
                    badge_destino(d["destino"])
                    forma_el = badge_forma(d["forma"])
                    # forma já renderiza inline; nada a fazer aqui

    def recarregar():
        render_lista()

    with container:
        render_banner_backup()
        render_filtros()
    container.move()  # placeholder to ensure order
    render_lista()
```

- [ ] **Step 2: Smoke test**

```bash
uv run python -c "from app.ui.pages import lista; print('ok')"
uv run pytest tests/ -q
```
Expected: `ok` + 39 passed

- [ ] **Step 3: Visual test manual**

```bash
uv run python main.py
```
Conferir: lista carrega no novo estilo, filtros funcionam, banner aparece se aplicável, empty state aparece quando filtra algo inexistente.

- [ ] **Step 4: Commit**

```bash
git add app/ui/pages/lista.py
git commit -m "feat(ui): lista de devolucoes redesenhada (rows + filtros + empty state)"
```

---

## FASE D — Detalhe e Form redesenhados

### Task 7: Painel de Detalhe redesenhado

**Files:**
- Rewrite: `app/ui/components/detalhe_devolucao.py`

- [ ] **Step 1: Substituir conteúdo do arquivo**

```python
import webbrowser
from pathlib import Path
from typing import Callable, Optional

from nicegui import ui

from app.config import Config
from app.constants import (
    DESTINO_FISICO_LABELS, DestinoFisico,
    FORMA_RESSARCIMENTO_LABELS, FormaRessarcimento,
    STATUS_PROCESSO_LABELS, StatusProcesso,
)
from app.db import session_scope
from app.repositories import historico_repo
from app.services import anexo_service, devolucao_service, lixeira_service
from app.ui.components.pill_dropdown import (
    pill_dropdown_destino, pill_dropdown_forma, pill_dropdown_status,
)


def abrir_detalhe(devolucao_id: int,
                   on_save: Optional[Callable[[], None]] = None) -> None:
    from app.ui.components.form_devolucao import abrir_form_devolucao

    with session_scope() as s:
        d = devolucao_service.buscar(s, devolucao_id)
        if d is None:
            ui.notify("Devolução não encontrada", type="negative")
            return
        anexos_ordenados = sorted(d.anexos, key=lambda x: (x.ordem, x.criado_em))
        imagens = [(a.id, a.nome_original, anexo_service.thumb_url_de(a))
                   for a in anexos_ordenados if a.tipo == "imagem"]
        documentos = [(a.id, a.nome_original, a.caminho_interno, a.tipo)
                      for a in anexos_ordenados if a.tipo != "imagem"]
        dados = dict(
            id=d.id, marca=d.marca.nome, modelo=d.produto_modelo,
            referencia=d.produto_referencia, quantidade=d.quantidade,
            valor=float(d.valor_custo) if d.valor_custo else None,
            defeito=d.defeito_descricao, data_dev=d.data_devolucao,
            data_compra=d.data_compra_original,
            nf_origem=d.nf_origem, nf_abat=d.nf_abatimento,
            cliente_nome=d.cliente_nome, cliente_contato=d.cliente_contato,
            aguardando=d.cliente_aguardando_retorno,
            status=d.status_processo, destino=d.destino_fisico,
            forma=d.forma_ressarcimento, observacoes=d.observacoes,
            imagens=imagens, documentos=documentos,
        )
        historico = [(h.campo, h.valor_anterior, h.valor_novo, h.data, h.observacao)
                     for h in historico_repo.listar_por_devolucao(s, devolucao_id)]

    cfg = Config.load()

    def _recarregar():
        if on_save:
            on_save()
        dlg.close()
        abrir_detalhe(devolucao_id, on_save=on_save)

    def _mudar_status(novo: StatusProcesso):
        with session_scope() as s:
            devolucao_service.mudar_status_processo(s, devolucao_id, novo=novo)
        ui.notify("Status atualizado")
        _recarregar()

    def _mudar_destino(novo: DestinoFisico):
        with session_scope() as s:
            devolucao_service.mudar_destino_fisico(s, devolucao_id, novo=novo)
        ui.notify("Destino atualizado")
        _recarregar()

    def _mudar_forma(nova: Optional[FormaRessarcimento]):
        with session_scope() as s:
            devolucao_service.atualizar(s, devolucao_id, forma_ressarcimento=nova)
        ui.notify("Forma atualizada")
        _recarregar()

    dlg = ui.dialog().props("position=right persistent=false")
    with dlg, ui.card().style(
        "width: 560px; height: 100vh; max-height: 100vh; padding: 0; "
        "border-radius: 0; background: var(--bg-base); border-left: 1px solid var(--border-subtle); "
        "display: flex; flex-direction: column;"
    ):
        # Header sticky
        with ui.row().style(
            "padding: 16px 20px; border-bottom: 1px solid var(--border-faint); "
            "align-items: center; justify-content: space-between; flex-shrink: 0;"
        ):
            with ui.column().classes("gap-0"):
                ui.label(dados["marca"].upper()).style(
                    "color: var(--text-muted); font-size: 11px; letter-spacing: 1px;"
                )
                ui.label(dados["modelo"]).style(
                    "color: var(--text-primary); font-size: 15px; font-weight: 600;"
                )
            ui.button(icon="close", on_click=dlg.close) \
                .props("flat round dense").style("color: var(--text-secondary);")

        # Body scroll
        with ui.column().classes("w-full").style(
            "flex: 1; overflow-y: auto; padding: 20px; gap: 0;"
        ):
            # Hero
            with ui.row().classes("gap-4 items-start w-full") \
                    .style("margin-bottom: 20px;"):
                if dados["imagens"]:
                    _, _, principal_url = dados["imagens"][0]
                    if principal_url:
                        ui.image(principal_url).style(
                            "width: 120px; height: 120px; border-radius: 8px; "
                            "object-fit: cover; flex-shrink: 0;"
                        )
                with ui.column().classes("gap-2"):
                    ui.label(f"Devolvido em {dados['data_dev'].strftime('%d/%m/%Y')}") \
                        .style("color: var(--text-secondary); font-size: 12px;")
                    if dados["referencia"]:
                        ui.label(f"ref {dados['referencia']}") \
                            .classes("app-mono").style("color: var(--text-muted); font-size: 11px;")
                    with ui.row().classes("gap-2 items-center"):
                        pill_dropdown_status(dados["status"], _mudar_status)
                        pill_dropdown_destino(dados["destino"], _mudar_destino)
                        pill_dropdown_forma(dados["forma"], _mudar_forma)

            ui.html(
                '<div style="background: rgba(96,165,250,.08); '
                'border: 1px solid rgba(96,165,250,.2); color: #93c5fd; '
                'font-size: 11px; padding: 6px 10px; border-radius: 6px; margin-bottom: 20px;">'
                '💡 Clique nos badges acima pra mudar de status sem entrar em "Editar"</div>'
            )

            # Detalhes
            ui.label("DETALHES").classes("app-section-label") \
                .style("margin-bottom: 10px;")
            _detalhe_grid(dados)
            ui.html('<div class="app-divider"></div>')

            # Galeria
            _galeria(dados, devolucao_id, _recarregar)
            ui.html('<div class="app-divider"></div>')

            # Documentos
            _documentos(dados, devolucao_id, cfg, _recarregar)
            ui.html('<div class="app-divider"></div>')

            # Observações
            if dados["observacoes"]:
                ui.label("OBSERVAÇÕES").classes("app-section-label") \
                    .style("margin-bottom: 10px;")
                ui.html(
                    f'<div style="background: var(--bg-elevated); border: 1px solid var(--border-faint); '
                    f'border-radius: 6px; padding: 10px 12px; color: var(--text-primary); '
                    f'font-size: 13px; line-height: 1.5; white-space: pre-wrap;">'
                    f'{dados["observacoes"]}</div>'
                )
                ui.html('<div class="app-divider"></div>')

            # Histórico
            ui.label("HISTÓRICO").classes("app-section-label") \
                .style("margin-bottom: 10px;")
            _historico(historico)

        # Footer sticky
        with ui.row().style(
            "padding: 14px 20px; border-top: 1px solid var(--border-faint); "
            "justify-content: space-between; flex-shrink: 0;"
        ):
            def _excluir():
                with ui.dialog() as confirm, ui.card().style("background: var(--bg-elevated);"):
                    ui.label("Mover para a lixeira?").style("color: var(--text-primary);")
                    ui.label("Você terá 30 dias para restaurar.") \
                        .style("color: var(--text-muted); font-size: 12px;")
                    with ui.row().classes("justify-end gap-2"):
                        ui.button("Cancelar", on_click=confirm.close).props("flat")
                        def fazer():
                            with session_scope() as s:
                                lixeira_service.enviar_para_lixeira(s, devolucao_id)
                            ui.notify("Movida para a lixeira")
                            confirm.close()
                            dlg.close()
                            if on_save: on_save()
                        ui.button("Mover", on_click=fazer) \
                            .style("background: var(--danger); color: white;")
                confirm.open()

            ui.button("🗑 Mover pra lixeira", on_click=_excluir) \
                .props("flat").style("color: var(--danger);")
            ui.button("✎ Editar",
                      on_click=lambda: (dlg.close(),
                                         abrir_form_devolucao(devolucao_id, on_save=on_save))) \
                .props("unelevated").classes("bg-primary")

    dlg.open()


def _detalhe_grid(dados):
    pares = [
        ("Quantidade", str(dados["quantidade"])),
        ("Valor", f"R$ {dados['valor']:.2f}" if dados["valor"] else "—"),
        ("Defeito", dados["defeito"] or "—"),
        ("NF origem", dados["nf_origem"] or "—"),
        ("NF abatimento", dados["nf_abat"] or "—"),
        ("Data compra", dados["data_compra"].strftime("%d/%m/%Y") if dados["data_compra"] else "—"),
    ]
    if dados["cliente_nome"]:
        nome = dados["cliente_nome"]
        if dados["aguardando"]:
            nome += '  <span style="color: var(--waiting); font-size: 11px;">⏳ aguardando</span>'
        pares.append(("Cliente", nome))
        if dados["cliente_contato"]:
            pares.append(("Contato", dados["cliente_contato"]))
    html = '<dl style="display: grid; grid-template-columns: 120px 1fr; row-gap: 8px; column-gap: 12px; margin-bottom: 20px;">'
    for label, valor in pares:
        html += f'<dt style="color: var(--text-secondary); font-size: 12px;">{label}</dt>'
        html += f'<dd style="color: var(--text-primary); font-size: 13px;">{valor}</dd>'
    html += '</dl>'
    ui.html(html)


def _galeria(dados, devolucao_id, on_change):
    ui.label(f"IMAGENS ({len(dados['imagens'])})").classes("app-section-label") \
        .style("margin-bottom: 10px;")

    async def upload_imagem(e):
        from tempfile import mkdtemp
        nome = e.file.name or "imagem.jpg"
        tmp = Path(mkdtemp()) / nome
        await e.file.save(tmp)
        try:
            with session_scope() as s:
                anexo_service.salvar_anexo(s, devolucao_id, tmp)
            ui.notify("Imagem adicionada")
            on_change()
        except ValueError as err:
            ui.notify(str(err), type="negative")

    if dados["imagens"]:
        with ui.row().classes("gap-2").style("flex-wrap: wrap; margin-bottom: 10px;"):
            for idx, (aid, nome, url) in enumerate(dados["imagens"]):
                is_first = idx == 0
                _card_imagem(aid, nome, url, is_first, devolucao_id, on_change)
    else:
        ui.label("Nenhuma imagem ainda.") \
            .style("color: var(--text-muted); font-size: 12px; margin-bottom: 10px;")

    ui.upload(label="+ Adicionar imagem", on_upload=upload_imagem,
              auto_upload=True, multiple=True) \
        .props('accept=".jpg,.jpeg,.png,.webp" flat').classes("w-full app-upload-zone")


def _card_imagem(aid, nome, url, is_first, devolucao_id, on_change):
    border = "border: 2px solid var(--accent);" if is_first else "border: 1px solid var(--border-subtle);"
    with ui.element("div").style(
        f"position: relative; width: 110px; height: 110px; {border} "
        f"border-radius: 6px; overflow: hidden;"
    ):
        if url:
            ui.image(url).style("width: 100%; height: 100%; object-fit: cover;")
        if is_first:
            ui.html(
                '<div style="position: absolute; top: 4px; left: 4px; '
                'background: var(--accent); color: var(--accent-fg); '
                'font-size: 9px; padding: 2px 6px; border-radius: 8px; '
                'font-weight: 700;">★ PRINCIPAL</div>'
            )
        # Botões hover
        with ui.row().style(
            "position: absolute; bottom: 4px; right: 4px; gap: 2px;"
        ):
            def _up(aid=aid):
                with session_scope() as s:
                    anexo_service.mover_para_cima(s, aid)
                on_change()
            def _down(aid=aid):
                with session_scope() as s:
                    anexo_service.mover_para_baixo(s, aid)
                on_change()
            def _principal(aid=aid):
                with session_scope() as s:
                    anexo_service.definir_como_principal(s, aid)
                on_change()
            def _del(aid=aid):
                with session_scope() as s:
                    anexo_service.remover_anexo(s, aid)
                ui.notify("Imagem removida")
                on_change()
            for icon, fn in [("◀", _up), ("▶", _down), ("★", _principal), ("🗑", _del)]:
                ui.button(icon, on_click=fn).props("dense flat size=xs").style(
                    "min-width: 22px; height: 22px; padding: 0; "
                    "background: rgba(0,0,0,.7); color: white; border-radius: 4px;"
                )


def _documentos(dados, devolucao_id, cfg, on_change):
    ui.label(f"DOCUMENTOS ({len(dados['documentos'])})") \
        .classes("app-section-label").style("margin-bottom: 10px;")

    async def upload_doc(e):
        from tempfile import mkdtemp
        nome = e.file.name or "doc.pdf"
        tmp = Path(mkdtemp()) / nome
        await e.file.save(tmp)
        try:
            with session_scope() as s:
                anexo_service.salvar_anexo(s, devolucao_id, tmp)
            ui.notify("Documento adicionado")
            on_change()
        except ValueError as err:
            ui.notify(str(err), type="negative")

    if dados["documentos"]:
        for aid, nome, caminho, _tipo in dados["documentos"]:
            with ui.row().classes("items-center gap-2 w-full") \
                    .style("background: var(--bg-elevated); border: 1px solid var(--border-faint); "
                           "border-radius: 6px; padding: 8px 10px; margin-bottom: 6px;"):
                ui.label("📄")
                ui.label(nome).style("color: var(--text-primary); font-size: 12px; flex: 1;")
                ui.button("abrir",
                          on_click=lambda _, c=caminho: webbrowser.open(
                              (cfg.data_dir / c).as_uri())) \
                    .props("flat dense").style("font-size: 11px;")
                def _remove(aid=aid):
                    with session_scope() as s:
                        anexo_service.remover_anexo(s, aid)
                    ui.notify("Removido")
                    on_change()
                ui.button("remover", on_click=_remove) \
                    .props("flat dense").style("color: var(--danger); font-size: 11px;")

    ui.upload(label="📎 Adicionar PDF", on_upload=upload_doc, auto_upload=True) \
        .props('accept=".pdf" flat').classes("w-full app-upload-zone")


def _historico(historico):
    html = '<div class="app-timeline">'
    for campo, anterior, novo, data, obs in historico:
        data_str = data.strftime("%d/%m/%Y %H:%M")
        if campo == "status_processo":
            label_novo = STATUS_PROCESSO_LABELS[StatusProcesso(novo)][0]
            texto = f"Status → <b>{label_novo}</b>"
        else:
            label_novo = DESTINO_FISICO_LABELS[DestinoFisico(novo)][0]
            texto = f"Destino → <b>{label_novo}</b>"
        if obs:
            texto += f' <span style="color: var(--text-muted);">({obs})</span>'
        html += f'<div class="app-timeline-item"><div class="time">{data_str}</div><div class="text">{texto}</div></div>'
    html += '</div>'
    ui.html(html)
```

- [ ] **Step 2: Smoke test**

```bash
uv run python -c "from app.ui.components import detalhe_devolucao; print('ok')"
uv run pytest tests/ -q
```
Expected: `ok` + 39 passed

- [ ] **Step 3: Commit**

```bash
git add app/ui/components/detalhe_devolucao.py
git commit -m "feat(ui): painel de detalhe redesenhado com pilulas clicaveis e nova hierarquia"
```

---

### Task 8: Painel de Form redesenhado

**Files:**
- Rewrite: `app/ui/components/form_devolucao.py`

- [ ] **Step 1: Substituir conteúdo do arquivo**

Importações iguais ao atual. Mudanças focadas no visual do painel:
- Container: mesmo posicionamento `position=right` mas dimensões e classes alinhadas com detalhe
- Header sticky com label uppercase + título
- Body scrollável com seções separadas por `app-divider` e label uppercase
- Inputs com props `outlined dense` (Quasar overrides já aplicados via app.css)
- Footer sticky com Cancelar + Salvar

```python
from datetime import date
from pathlib import Path
from typing import Callable, Optional

from nicegui import events, ui

from app.constants import (DestinoFisico, DESTINO_FISICO_LABELS,
                            FormaRessarcimento, FORMA_RESSARCIMENTO_LABELS,
                            StatusProcesso, STATUS_PROCESSO_LABELS)
from app.db import session_scope
from app.repositories import marcas_repo
from app.services import anexo_service, devolucao_service


def abrir_form_devolucao(devolucao_id: Optional[int] = None,
                          on_save: Optional[Callable[[], None]] = None) -> None:
    with session_scope() as s:
        d = devolucao_service.buscar(s, devolucao_id) if devolucao_id else None
        marcas = [(m.id, m.nome, m.forma_ressarcimento_padrao) for m in marcas_repo.listar(s)]

    if not marcas:
        ui.notify("Cadastre ao menos uma marca antes de criar devolução.", type="warning")
        return

    valores = {
        "marca_id": d.marca_id if d else marcas[0][0],
        "produto_modelo": d.produto_modelo if d else "",
        "produto_referencia": (d.produto_referencia if d else "") or "",
        "quantidade": d.quantidade if d else 1,
        "valor_custo": float(d.valor_custo) if d and d.valor_custo else None,
        "defeito_descricao": (d.defeito_descricao if d else "") or "",
        "data_devolucao": d.data_devolucao if d else date.today(),
        "data_compra_original": d.data_compra_original if d else None,
        "nf_origem": (d.nf_origem if d else "") or "",
        "nf_abatimento": (d.nf_abatimento if d else "") or "",
        "cliente_nome": (d.cliente_nome if d else "") or "",
        "cliente_contato": (d.cliente_contato if d else "") or "",
        "cliente_aguardando_retorno": d.cliente_aguardando_retorno if d else False,
        "status_processo": d.status_processo if d else StatusProcesso.DEFEITO_IDENTIFICADO,
        "destino_fisico": d.destino_fisico if d else DestinoFisico.NA_LOJA,
        "forma_ressarcimento": d.forma_ressarcimento if d else None,
        "observacoes": (d.observacoes if d else "") or "",
    }
    imagens_temp: list[Path] = []

    dlg = ui.dialog().props("position=right persistent=false")
    with dlg, ui.card().style(
        "width: 560px; height: 100vh; padding: 0; border-radius: 0; "
        "background: var(--bg-base); border-left: 1px solid var(--border-subtle); "
        "display: flex; flex-direction: column;"
    ):
        # Header
        with ui.row().style(
            "padding: 16px 20px; border-bottom: 1px solid var(--border-faint); "
            "align-items: center; justify-content: space-between; flex-shrink: 0;"
        ):
            with ui.column().classes("gap-0"):
                ui.label("DEVOLUÇÃO").style(
                    "color: var(--text-muted); font-size: 11px; letter-spacing: 1px;"
                )
                ui.label("Editar" if d else "Nova").style(
                    "color: var(--text-primary); font-size: 15px; font-weight: 600;"
                )
            ui.button(icon="close", on_click=dlg.close) \
                .props("flat round dense").style("color: var(--text-secondary);")

        # Body
        with ui.column().classes("w-full") \
                .style("flex: 1; overflow-y: auto; padding: 20px; gap: 0;"):

            opcoes_marca = {mid: nome for mid, nome, _ in marcas}
            sel_marca = ui.select(opcoes_marca, label="Marca *").classes("w-full") \
                .props("outlined dense")
            sel_marca.value = valores["marca_id"]
            def sugerir_forma():
                for mid, _, forma in marcas:
                    if mid == sel_marca.value and forma and not valores["forma_ressarcimento"]:
                        sel_forma.value = forma.value
            sel_marca.on("update:model-value", lambda _: sugerir_forma())

            ui.html('<div class="app-divider"></div>')
            ui.label("PRODUTO").classes("app-section-label").style("margin-bottom: 8px;")
            i_modelo = ui.input("Modelo *", value=valores["produto_modelo"]) \
                .props("outlined dense").classes("w-full")
            i_ref = ui.input("Referência", value=valores["produto_referencia"]) \
                .props("outlined dense").classes("w-full")
            with ui.row().classes("w-full gap-2"):
                i_qtd = ui.number("Quantidade", value=valores["quantidade"], min=1) \
                    .props("outlined dense").style("flex: 1;")
                i_valor = ui.number("Valor custo (R$)", value=valores["valor_custo"], format="%.2f") \
                    .props("outlined dense").style("flex: 1;")
            i_defeito = ui.input("Defeito", value=valores["defeito_descricao"]) \
                .props("outlined dense").classes("w-full")

            async def on_upload_imagem(e: events.UploadEventArguments):
                from tempfile import mkdtemp
                nome = e.file.name or "imagem.jpg"
                tmp = Path(mkdtemp()) / nome
                await e.file.save(tmp)
                imagens_temp.append(tmp)
                ui.notify(f"Imagem adicionada: {nome}")

            ui.label("Imagens (opcional) — a primeira será a principal") \
                .style("color: var(--text-muted); font-size: 11px; margin-top: 6px;")
            ui.upload(label="+ Imagens", on_upload=on_upload_imagem,
                      auto_upload=True, multiple=True) \
                .props('accept=".jpg,.jpeg,.png,.webp" flat').classes("w-full app-upload-zone")

            ui.html('<div class="app-divider"></div>')
            ui.label("DATAS").classes("app-section-label").style("margin-bottom: 8px;")
            i_data_dev = ui.input("Data devolução *", value=valores["data_devolucao"].isoformat()) \
                .props("outlined dense type=date").classes("w-full")
            i_data_compra = ui.input(
                "Data da compra original",
                value=valores["data_compra_original"].isoformat() if valores["data_compra_original"] else ""
            ).props("outlined dense type=date").classes("w-full")

            ui.html('<div class="app-divider"></div>')
            ui.label("NOTAS FISCAIS (OPCIONAL)").classes("app-section-label").style("margin-bottom: 8px;")
            i_nf_orig = ui.input("NF de origem", value=valores["nf_origem"]) \
                .props("outlined dense").classes("w-full")
            i_nf_abat = ui.input("NF de abatimento", value=valores["nf_abatimento"]) \
                .props("outlined dense").classes("w-full")

            ui.html('<div class="app-divider"></div>')
            ui.label("CLIENTE (OPCIONAL)").classes("app-section-label").style("margin-bottom: 8px;")
            i_cli_nome = ui.input("Nome", value=valores["cliente_nome"]) \
                .props("outlined dense").classes("w-full")
            i_cli_ctt = ui.input("Contato", value=valores["cliente_contato"]) \
                .props("outlined dense").classes("w-full")
            i_aguardando = ui.checkbox("Cliente aguardando retorno",
                                        value=valores["cliente_aguardando_retorno"])

            ui.html('<div class="app-divider"></div>')
            ui.label("STATUS").classes("app-section-label").style("margin-bottom: 8px;")
            opcoes_status = {s.value: STATUS_PROCESSO_LABELS[s][0] for s in StatusProcesso}
            sel_status = ui.select(opcoes_status, label="Processo").classes("w-full") \
                .props("outlined dense")
            sel_status.value = valores["status_processo"].value
            opcoes_dest = {dd.value: DESTINO_FISICO_LABELS[dd][0] for dd in DestinoFisico}
            sel_dest = ui.select(opcoes_dest, label="Destino físico").classes("w-full") \
                .props("outlined dense")
            sel_dest.value = valores["destino_fisico"].value
            opcoes_forma = {None: "—"} | {f.value: FORMA_RESSARCIMENTO_LABELS[f][0]
                                           for f in FormaRessarcimento}
            sel_forma = ui.select(opcoes_forma, label="Forma de ressarcimento") \
                .classes("w-full").props("outlined dense")
            sel_forma.value = valores["forma_ressarcimento"].value if valores["forma_ressarcimento"] else None

            ui.html('<div class="app-divider"></div>')
            ui.label("OBSERVAÇÕES").classes("app-section-label").style("margin-bottom: 8px;")
            i_obs = ui.textarea(value=valores["observacoes"]) \
                .props("outlined dense").classes("w-full")

        # Footer
        with ui.row().style(
            "padding: 14px 20px; border-top: 1px solid var(--border-faint); "
            "justify-content: flex-end; gap: 8px; flex-shrink: 0;"
        ):
            def salvar():
                if not i_modelo.value or not i_modelo.value.strip():
                    ui.notify("Modelo é obrigatório", type="negative")
                    return
                try:
                    dd_ = date.fromisoformat(i_data_dev.value)
                except Exception:
                    ui.notify("Data de devolução inválida", type="negative")
                    return
                dc_ = None
                if i_data_compra.value:
                    try:
                        dc_ = date.fromisoformat(i_data_compra.value)
                    except Exception:
                        ui.notify("Data da compra inválida", type="negative")
                        return
                payload = dict(
                    marca_id=sel_marca.value,
                    produto_modelo=i_modelo.value.strip(),
                    produto_referencia=i_ref.value or None,
                    quantidade=int(i_qtd.value or 1),
                    valor_custo=i_valor.value,
                    defeito_descricao=i_defeito.value or None,
                    data_devolucao=dd_,
                    data_compra_original=dc_,
                    nf_origem=i_nf_orig.value or None,
                    nf_abatimento=i_nf_abat.value or None,
                    cliente_nome=i_cli_nome.value or None,
                    cliente_contato=i_cli_ctt.value or None,
                    cliente_aguardando_retorno=bool(i_aguardando.value),
                    status_processo=StatusProcesso(sel_status.value),
                    destino_fisico=DestinoFisico(sel_dest.value),
                    forma_ressarcimento=FormaRessarcimento(sel_forma.value) if sel_forma.value else None,
                    observacoes=i_obs.value or None,
                )
                with session_scope() as s:
                    if devolucao_id:
                        devolucao_service.atualizar(s, devolucao_id, **payload)
                        novo_id = devolucao_id
                    else:
                        nova = devolucao_service.criar(s, **payload)
                        s.flush()
                        novo_id = nova.id
                    for img_path in imagens_temp:
                        try:
                            anexo_service.salvar_anexo(s, novo_id, img_path)
                        except Exception as e:
                            ui.notify(f"Erro ao salvar imagem {img_path.name}: {e}", type="warning")
                ui.notify("Salvo", type="positive")
                dlg.close()
                if on_save:
                    on_save()

            ui.button("Cancelar", on_click=dlg.close).props("flat")
            ui.button("Salvar", on_click=salvar) \
                .props("unelevated").classes("bg-primary")

    dlg.open()
```

- [ ] **Step 2: Smoke test + testes**

```bash
uv run python -c "from app.ui.components import form_devolucao; print('ok')"
uv run pytest tests/ -q
```
Expected: `ok` + 39 passed

- [ ] **Step 3: Commit**

```bash
git add app/ui/components/form_devolucao.py
git commit -m "feat(ui): painel de form redesenhado com seccoes e divisores"
```

---

## FASE E — Páginas secundárias

### Task 9: Página Marcas redesenhada

**Files:**
- Rewrite: `app/ui/pages/marcas.py`

Mantém estrutura funcional, apenas substitui classes/estilos para o novo tema.

- [ ] **Step 1: Reescrever `app/ui/pages/marcas.py`**

Padrão: cabeçalho com título + botão "+ Nova marca", lista de cards com nome bold + "Padrão: X" em cinza + observações em cinza menor + ícones de editar/excluir à direita. Modal de criar/editar = `ui.dialog` centralizado pequeno (não painel lateral) com fundo `var(--bg-elevated)` e inputs `outlined dense`.

Manter toda lógica de CRUD do código atual; substituir apenas elementos visuais. Empty state: ícone 🏷️ grande + "Nenhuma marca cadastrada ainda." + botão "+ Nova marca".

- [ ] **Step 2: Smoke test**

```bash
uv run python -c "from app.ui.pages import marcas; print('ok')"
uv run pytest tests/ -q
```
Expected: `ok` + 39 passed

- [ ] **Step 3: Commit**

```bash
git add app/ui/pages/marcas.py
git commit -m "feat(ui): pagina Marcas no novo visual"
```

---

### Task 10: Página Lixeira redesenhada

**Files:**
- Rewrite: `app/ui/pages/lixeira.py`

- [ ] **Step 1: Reescrever** — usar mesmo padrão de rows da Lista (sem badges semânticos, com data de exclusão), botões "Restaurar" e "Apagar agora" à direita. Empty state: ícone 🗑️ grande + "Lixeira vazia.".

- [ ] **Step 2: Smoke test**

```bash
uv run python -c "from app.ui.pages import lixeira; print('ok')"
uv run pytest tests/ -q
```
Expected: `ok` + 39 passed

- [ ] **Step 3: Commit**

```bash
git add app/ui/pages/lixeira.py
git commit -m "feat(ui): pagina Lixeira no novo visual"
```

---

### Task 11: Página Configurações redesenhada

**Files:**
- Rewrite: `app/ui/pages/configuracoes.py`

- [ ] **Step 1: Reescrever** — layout vertical com `max-width: 600px`, seções separadas por `app-divider`, label uppercase pra título de seção (`DADOS`, `BACKUP`, `BACKUP MANUAL`), inputs `outlined dense`. Botão "Salvar" e "Fazer backup agora" com classe `bg-primary`. Lista dos últimos backups com fundo `var(--bg-elevated)` e font mono pra timestamp.

- [ ] **Step 2: Smoke test**

```bash
uv run python -c "from app.ui.pages import configuracoes; print('ok')"
uv run pytest tests/ -q
```
Expected: `ok` + 39 passed

- [ ] **Step 3: Commit**

```bash
git add app/ui/pages/configuracoes.py
git commit -m "feat(ui): pagina Configuracoes no novo visual"
```

---

## FASE F — Validação final

### Task 12: Validação E2E manual

- [ ] **Step 1: Rodar app**

```bash
uv run python main.py
```

- [ ] **Step 2: Roteiro de smoke test visual**

Conferir cada item:
- [ ] App abre com tema dark; nenhuma cor padrão Quasar (azul, cinza-claro) escapou
- [ ] Sidebar inicia no estado salvo (expandida ou recolhida)
- [ ] Botão de toggle alterna sidebar; Ctrl+B também alterna
- [ ] Estado da sidebar persiste após fechar/reabrir o app
- [ ] Lista mostra rows com thumbnail (ou placeholder), badges com bolinha colorida e formato uniforme
- [ ] Filtros funcionam, empty state aparece quando filtros não retornam nada
- [ ] Banner amarelo de backup aparece (se aplicável)
- [ ] Click em row abre painel lateral direito com slide animation
- [ ] No detalhe: badges são clicáveis e mudam status/destino/forma
- [ ] Galeria mostra cards quadrados com ★ Principal na primeira; botões aparecem no hover
- [ ] Documentos lista com upload-zone dashed
- [ ] Histórico tem timeline visual com pontos
- [ ] Click em "Editar" fecha detalhe e abre form com mesmo estilo
- [ ] Criar marca, criar devolução, anexar imagens — fluxo completo funciona
- [ ] Mover pra lixeira e restaurar — fluxo funciona
- [ ] Configurações com novo visual carrega; salvar funciona

- [ ] **Step 3: Se algum item falhou, corrigir antes de finalizar**

- [ ] **Step 4: Commit final + push**

```bash
git push origin master
```

---

## Self-Review

**Spec coverage check:**
- ✅ §2 Sistema visual (paleta, tipografia, espaçamento) → Task 1
- ✅ §3 App shell (sidebar retrátil) → Tasks 2, 3
- ✅ §4 Lista (rows, filtros, empty state, banner backup) → Task 6
- ✅ §5 Detalhe (painel direito, hero, pills clicáveis, galeria, docs, timeline) → Task 7
- ✅ §6 Form (painel direito, seções, inputs) → Task 8
- ✅ §7 Páginas secundárias → Tasks 9, 10, 11
- ✅ §8 Toasts e dialogs → cobertos pelo CSS global (Task 1)
- ✅ §9 Mudanças técnicas → distribuídas nas tasks
- ⚠️ §8 Lightbox de imagem → DEFERIDO (fora do escopo da v1 do redesign, anexado ao backlog)

**Placeholder scan:** Tasks 9-11 referenciam o padrão do spec em vez de mostrar código completo — isso é intencional pra esta fase porque seguem o mesmo padrão visual já estabelecido em Tasks 6 e 7. O implementer subagent tem o spec + as tasks anteriores como referência completa.

**Type consistency:** `_COR_PARA_VAR` é definido em Task 4 (`badge_status.py`) e reutilizado em Task 5 (`pill_dropdown.py`) — ok. `montar_layout()` em Task 3 mantém a assinatura usada pelas páginas (mesma da versão anterior). `Config.sidebar_collapsed` adicionada em Task 2 e consumida em Task 3.

**Decisões adicionadas neste plano:**
- Lightbox de imagem fica fora da v1 (vai pro backlog) pra reduzir escopo e tempo
- Tipografia usa system font stack em vez de baixar Inter/JBMono — simplifica, ainda fica boa
