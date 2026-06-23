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


def _brl(v: float) -> str:
    """Formata um valor como moeda BR (R$ 1.234,56)."""
    s = f"{v:,.2f}"  # ex.: 1,234.56 (formato US)
    return "R$ " + s.replace(",", "_").replace(".", ",").replace("_", ".")


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

    def render_resumo(dados):
        resumo_container.clear()
        abertas = [x for x in dados if x["status"] != StatusProcesso.RESSARCIDO]
        a_ressarcir = sum(x["valor"] for x in abertas if x["valor"])
        stats = [
            (str(len(dados)), "devoluções", "var(--text-primary)"),
            (str(len(abertas)), "pendentes", "var(--status-orange)"),
            (_brl(a_ressarcir), "a ressarcir", "var(--status-yellow)"),
        ]
        with resumo_container:
            for valor, label, cor in stats:
                with ui.column().classes("app-stat"):
                    ui.label(valor).classes("app-stat-value").style(f"color: {cor};")
                    ui.label(label).classes("app-stat-label")

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
                    "valor": float(d.valor_custo) if d.valor_custo else None,
                })

        render_resumo(dados)

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

            with ui.element("div").classes("app-rows-grid w-full"):
                # cabeçalho de colunas
                with ui.element("div").classes("app-row app-row-head"):
                    ui.element("div")  # espaço do thumbnail
                    ui.label("Produto").classes("app-col-head")
                    ui.label("Status").classes("app-col-head")
                    ui.label("Destino").classes("app-col-head")
                    ui.label("Forma").classes("app-col-head")
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
                        badge_forma(d["forma"])

    def recarregar():
        render_lista()

    with container:
        render_banner_backup()
        resumo_container = ui.row().classes("items-center app-resumo")
        render_filtros()
    render_lista()
