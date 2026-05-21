from datetime import date

from nicegui import ui

from app.config import Config
from app.constants import (BANNER_BACKUP_ALERTA_DIAS, DestinoFisico,
                            DESTINO_FISICO_LABELS, StatusProcesso,
                            STATUS_PROCESSO_LABELS)
from app.db import session_scope
from app.repositories import devolucoes_repo, marcas_repo
from app.services import backup_service
from app.ui.components.badge_status import (badge_destino, badge_forma,
                                              badge_status_processo)


def render():
    from app.ui.layout import montar_layout
    from app.ui.components.form_devolucao import abrir_form_devolucao
    from app.ui.components.detalhe_devolucao import abrir_detalhe

    montar_layout("Devoluções")

    # Estado dos filtros
    filtros = {
        "busca": "",
        "marca_id": None,
        "status": None,
        "destino": None,
        "aguardando": False,
    }

    container = ui.column().classes("w-full")

    def _banner_backup():
        info = backup_service.ultimo_backup()
        if info is None:
            with ui.row().classes("bg-yellow-2 q-pa-sm w-full items-center"):
                ui.label("⚠️ Nenhum backup foi feito ainda.")
                ui.button("Fazer backup agora",
                          on_click=lambda: (backup_service.criar_backup(),
                                            ui.notify("Backup criado"))
                          ).props("size=sm").classes("bg-primary text-white")
            return
        dias = (date.today() - info.criado_em.date()).days
        if dias >= BANNER_BACKUP_ALERTA_DIAS:
            with ui.row().classes("bg-yellow-2 q-pa-sm w-full items-center"):
                ui.label(f"⚠️ Último backup há {dias} dias.")
                ui.button("Fazer backup agora",
                          on_click=lambda: (backup_service.criar_backup(),
                                            ui.notify("Backup criado"))
                          ).props("size=sm").classes("bg-primary text-white")

    def recarregar():
        container.clear()
        with container:
            _banner_backup()

            # Barra de filtros
            with ui.row().classes("w-full items-end gap-2"):
                ui.input("Buscar...", on_change=lambda e: filtros.update(busca=e.value) or recarregar_lista()) \
                    .classes("w-64")

                with session_scope() as s:
                    marcas = [(m.id, m.nome) for m in marcas_repo.listar(s)]
                opcoes_marca = {None: "Todas marcas"} | {mid: nome for mid, nome in marcas}
                ui.select(opcoes_marca, label="Marca",
                          on_change=lambda e: filtros.update(marca_id=e.value) or recarregar_lista()) \
                    .classes("w-48").value = None

                opcoes_status = {None: "Todos status"} | {
                    s.value: STATUS_PROCESSO_LABELS[s][0] for s in StatusProcesso
                }
                ui.select(opcoes_status, label="Status",
                          on_change=lambda e: filtros.update(
                              status=StatusProcesso(e.value) if e.value else None) or recarregar_lista()) \
                    .classes("w-56").value = None

                opcoes_dest = {None: "Todos destinos"} | {
                    d.value: DESTINO_FISICO_LABELS[d][0] for d in DestinoFisico
                }
                ui.select(opcoes_dest, label="Destino",
                          on_change=lambda e: filtros.update(
                              destino=DestinoFisico(e.value) if e.value else None) or recarregar_lista()) \
                    .classes("w-48").value = None

                ui.checkbox("Aguardando retorno",
                            on_change=lambda e: filtros.update(aguardando=e.value) or recarregar_lista())

                ui.space()
                ui.button("+ Nova Devolução",
                          on_click=lambda: abrir_form_devolucao(on_save=recarregar)) \
                    .classes("bg-primary text-white")

            # Lista
            lista_container = ui.column().classes("w-full gap-2")

            def recarregar_lista():
                lista_container.clear()
                with session_scope() as s:
                    devs = devolucoes_repo.listar_ativas(
                        s,
                        marca_id=filtros["marca_id"],
                        status=filtros["status"],
                        destino=filtros["destino"],
                        aguardando_retorno=True if filtros["aguardando"] else None,
                        busca=filtros["busca"] or None,
                    )
                    cfg = Config.load()
                    dados = []
                    for d in devs:
                        thumb = (cfg.data_dir / d.foto_principal_caminho).as_posix() \
                            if d.foto_principal_caminho else None
                        dados.append({
                            "id": d.id,
                            "marca": d.marca.nome,
                            "modelo": d.produto_modelo,
                            "ref": d.produto_referencia,
                            "data": d.data_devolucao.strftime("%d/%m/%Y"),
                            "cliente": d.cliente_nome,
                            "aguardando": d.cliente_aguardando_retorno,
                            "status": d.status_processo,
                            "destino": d.destino_fisico,
                            "forma": d.forma_ressarcimento,
                            "thumb": thumb,
                        })

                with lista_container:
                    if not dados:
                        ui.label("Nenhuma devolução com esses filtros.").classes("text-grey-7 q-pa-md")
                        return
                    for d in dados:
                        with ui.card().classes("w-full cursor-pointer hover:bg-grey-1") \
                                .on("click", lambda _, i=d["id"]: abrir_detalhe(i, on_save=recarregar)):
                            with ui.row().classes("items-center w-full gap-4"):
                                if d["thumb"]:
                                    ui.image(d["thumb"]).classes("w-16 h-16 rounded")
                                else:
                                    ui.icon("image", size="lg").classes("text-grey-5")
                                with ui.column().classes("flex-grow gap-1"):
                                    ui.label(f"{d['marca']} · {d['modelo']}" +
                                             (f" · ref {d['ref']}" if d['ref'] else "")) \
                                        .classes("font-bold")
                                    cliente_str = ""
                                    if d["cliente"]:
                                        cliente_str = f"Cliente: {d['cliente']}"
                                        if d["aguardando"]:
                                            cliente_str += " ⏳"
                                    ui.label(f"Devolvido: {d['data']}" +
                                             (f"   {cliente_str}" if cliente_str else "")) \
                                        .classes("text-caption text-grey-7")
                                    with ui.row().classes("gap-2 items-center"):
                                        badge_status_processo(d["status"])
                                        badge_destino(d["destino"])
                                        badge_forma(d["forma"])

            recarregar_lista()

    recarregar()
