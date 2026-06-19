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
        with ui.column().classes("w-full form-body") \
                .style("flex: 1; overflow-y: auto; padding: 20px; gap: 12px;"):

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

            ui.label("Imagens (opcional) — a primeira será a principal") \
                .style("color: var(--text-muted); font-size: 11px; margin-top: 6px;")

            async def on_upload_imagem(e: events.UploadEventArguments):
                from tempfile import mkdtemp
                nome = e.file.name or "imagem.jpg"
                tmp = Path(mkdtemp()) / nome
                await e.file.save(tmp)
                imagens_temp.append(tmp)
                with lista_imgs:
                    ui.label(f"📎 {nome}").style(
                        "color: var(--text-secondary); font-size: 12px;")

            ui.upload(label="+ Imagens", on_upload=on_upload_imagem,
                      auto_upload=True, multiple=True) \
                .props('accept=".jpg,.jpeg,.png,.webp" flat') \
                .classes("w-full app-upload-zone no-file-list")
            # Lista simples só com o nome do arquivo anexado (sem preview)
            lista_imgs = ui.column().classes("w-full gap-1").style("margin-top: 4px;")

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
