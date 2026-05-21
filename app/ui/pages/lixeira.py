from nicegui import ui

from app.db import session_scope
from app.repositories import devolucoes_repo
from app.services import lixeira_service


def render():
    from app.ui.layout import montar_layout
    montar_layout("Lixeira")

    container = ui.column().classes("w-full max-w-3xl")

    def recarregar():
        container.clear()
        with container:
            ui.label("Devoluções na lixeira (auto-expurgo em 30 dias)") \
                .classes("text-h6")
            with session_scope() as s:
                itens = devolucoes_repo.listar_lixeira(s)
                dados = [(d.id, d.marca.nome, d.produto_modelo,
                          d.data_devolucao.strftime("%d/%m/%Y"),
                          d.excluido_em.strftime("%d/%m/%Y") if d.excluido_em else "")
                         for d in itens]

            if not dados:
                ui.label("Lixeira vazia.").classes("text-grey-7")
                return

            for did, marca, modelo, data_dev, excluido in dados:
                with ui.card().classes("w-full"):
                    with ui.row().classes("items-center justify-between w-full"):
                        with ui.column():
                            ui.label(f"{marca} · {modelo}").classes("font-bold")
                            ui.label(f"Devolução: {data_dev}   Excluída: {excluido}") \
                                .classes("text-caption text-grey-7")
                        with ui.row():
                            def _restaurar(did=did):
                                with session_scope() as s:
                                    lixeira_service.restaurar(s, did)
                                ui.notify("Restaurada")
                                recarregar()

                            def _apagar_definitivo(did=did):
                                with ui.dialog() as dlg, ui.card():
                                    ui.label("Apagar definitivamente? Não tem volta.")
                                    with ui.row():
                                        ui.button("Cancelar", on_click=dlg.close).props("flat")
                                        def fazer():
                                            with session_scope() as s:
                                                from datetime import datetime, timedelta
                                                from app.constants import LIXEIRA_DIAS
                                                d = devolucoes_repo.buscar_por_id(s, did)
                                                if d:
                                                    d.excluido_em = datetime.utcnow() - timedelta(days=LIXEIRA_DIAS + 1)
                                                lixeira_service.expurgar_antigas(s)
                                            ui.notify("Apagada definitivamente")
                                            dlg.close()
                                            recarregar()
                                        ui.button("Apagar", on_click=fazer).classes("bg-red text-white")
                                dlg.open()

                            ui.button("Restaurar", icon="restore",
                                      on_click=_restaurar).props("flat")
                            ui.button("Apagar agora", icon="delete_forever",
                                      on_click=_apagar_definitivo).props("flat color=red")

    recarregar()
