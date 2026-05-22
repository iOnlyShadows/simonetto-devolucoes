from nicegui import ui

from app.db import session_scope
from app.repositories import devolucoes_repo
from app.services import lixeira_service


def render():
    from app.ui.layout import montar_layout
    montar_layout("Lixeira")

    ui.label("Auto-expurgo em 30 dias").style(
        "color: var(--text-muted); font-size: 13px; margin-bottom: 16px;"
    )

    container = ui.column().classes("w-full").style("max-width: 860px;")

    def recarregar():
        container.clear()
        with container:
            with session_scope() as s:
                itens = devolucoes_repo.listar_lixeira(s)
                dados = [
                    (
                        d.id,
                        d.marca.nome,
                        d.produto_modelo,
                        d.data_devolucao.strftime("%d/%m/%Y"),
                        d.excluido_em.strftime("%d/%m/%Y") if d.excluido_em else "",
                    )
                    for d in itens
                ]

            if not dados:
                with ui.column().classes("items-center").style(
                    "padding: 60px 20px; width: 100%; align-items: center;"
                ):
                    ui.label("🗑️").style("font-size: 48px; line-height: 1;")
                    ui.label("Lixeira vazia.").style(
                        "color: var(--text-secondary); margin-top: 12px;"
                    )
                return

            for did, marca, modelo, data_dev, excluido in dados:
                with ui.element("div").style(
                    "display: grid;"
                    "grid-template-columns: 1fr auto auto;"
                    "align-items: center;"
                    "border-bottom: 1px solid var(--border-faint);"
                    "padding: 14px 8px;"
                    "width: 100%;"
                ):
                    # Column 1: name + meta
                    with ui.column().style("gap: 2px;"):
                        ui.label(f"{marca} · {modelo}").style(
                            "color: var(--text-primary); font-size: 14px;"
                            " font-weight: 500;"
                        )
                        ui.label(
                            f"Devolução: {data_dev}   ·   Excluída: {excluido}"
                        ).style(
                            "color: var(--text-secondary); font-size: 11px;"
                        )

                    # Column 2: Restaurar button
                    def _restaurar(did=did):
                        with session_scope() as s:
                            lixeira_service.restaurar(s, did)
                        ui.notify("Restaurada")
                        recarregar()

                    ui.button("Restaurar", icon="restore", on_click=_restaurar).props(
                        "flat dense"
                    ).style("color: var(--text-primary);")

                    # Column 3: Apagar agora button
                    def _apagar_definitivo(did=did):
                        with ui.dialog() as dlg, ui.card().style(
                            "background: var(--bg-elevated); padding: 20px;"
                            " min-width: 320px;"
                        ):
                            ui.label("Apagar definitivamente? Não tem volta.").style(
                                "color: var(--text-primary); font-size: 14px;"
                                " margin-bottom: 16px;"
                            )
                            with ui.row().style("gap: 8px; justify-content: flex-end;"):
                                ui.button("Cancelar", on_click=dlg.close).props(
                                    "flat dense"
                                )

                                def fazer(did=did, dlg=dlg):
                                    with session_scope() as s:
                                        from datetime import datetime, timedelta
                                        from app.constants import LIXEIRA_DIAS

                                        d = devolucoes_repo.buscar_por_id(s, did)
                                        if d:
                                            d.excluido_em = datetime.utcnow() - timedelta(
                                                days=LIXEIRA_DIAS + 1
                                            )
                                        lixeira_service.expurgar_antigas(s)
                                    ui.notify("Apagada definitivamente")
                                    dlg.close()
                                    recarregar()

                                ui.button("Apagar", on_click=fazer).props(
                                    "dense"
                                ).style(
                                    "background: var(--danger); color: var(--accent-fg);"
                                )
                        dlg.open()

                    ui.button(
                        "Apagar agora", icon="delete_forever", on_click=_apagar_definitivo
                    ).props("flat dense").style("color: var(--danger);")

    recarregar()
