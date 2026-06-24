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
                          on_click=lambda _, c=caminho: ui.navigate.to(
                              anexo_service.url_publica(c), new_tab=True)) \
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
