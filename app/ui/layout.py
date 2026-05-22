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
