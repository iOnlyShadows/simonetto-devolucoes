from nicegui import ui


PAGINAS = [
    ("/", "Devoluções", "list_alt"),
    ("/marcas", "Marcas", "label"),
    ("/lixeira", "Lixeira", "delete"),
    ("/configuracoes", "Configurações", "settings"),
]


def montar_layout(titulo_pagina: str) -> ui.column:
    """Monta header + menu lateral e devolve o container de conteúdo."""
    with ui.header().classes("items-center justify-between bg-primary text-white"):
        ui.label("Loja Simonetto — Devoluções").classes("text-lg font-bold")
        ui.label(titulo_pagina).classes("text-sm opacity-80")

    with ui.left_drawer(value=True, fixed=True).classes("bg-grey-2"):
        ui.label("Menu").classes("text-xs uppercase text-grey-7 q-pa-sm")
        for rota, label, icone in PAGINAS:
            ui.link(label, rota).classes("flex items-center gap-2 q-pa-sm hover:bg-grey-4 no-underline text-black") \
                .props(f'icon={icone}')

    container = ui.column().classes("w-full q-pa-md")
    return container
