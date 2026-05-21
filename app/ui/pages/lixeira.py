from nicegui import ui


def render():
    from app.ui.layout import montar_layout
    montar_layout("Lixeira")
    ui.label("(página em construção — Task 20)")
