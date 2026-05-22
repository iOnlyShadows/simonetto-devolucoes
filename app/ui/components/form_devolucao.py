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
    """Abre modal lateral para criar (devolucao_id=None) ou editar."""
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
    foto_principal_temp: dict[str, Optional[Path]] = {"path": None}

    with ui.dialog().props("position=right") as dlg, ui.card().classes("w-[480px] h-screen overflow-auto"):
        ui.label("Editar Devolução" if d else "Nova Devolução").classes("text-h6")

        # Marca
        opcoes_marca = {mid: nome for mid, nome, _ in marcas}
        sel_marca = ui.select(opcoes_marca, label="Marca *").classes("w-full")
        sel_marca.value = valores["marca_id"]

        def _sugerir_forma():
            for mid, _, forma in marcas:
                if mid == sel_marca.value and forma and not valores["forma_ressarcimento"]:
                    sel_forma.value = forma.value

        sel_marca.on("update:model-value", lambda _: _sugerir_forma())

        # Produto
        ui.separator()
        ui.label("Produto").classes("text-subtitle2")
        i_modelo = ui.input("Modelo *", value=valores["produto_modelo"]).classes("w-full")
        i_ref = ui.input("Referência", value=valores["produto_referencia"]).classes("w-full")
        i_qtd = ui.number("Quantidade", value=valores["quantidade"], min=1).classes("w-full")
        i_valor = ui.number("Valor custo (R$)", value=valores["valor_custo"],
                             format="%.2f").classes("w-full")
        i_defeito = ui.input("Defeito", value=valores["defeito_descricao"]).classes("w-full")

        async def _on_upload_foto(e: events.UploadEventArguments):
            # Escreve bytes do upload num temp file preservando o nome original.
            from tempfile import mkdtemp
            nome = e.file.name or "upload.bin"
            tmp_dir = Path(mkdtemp())
            tmp = tmp_dir / nome
            await e.file.save(tmp)
            foto_principal_temp["path"] = tmp
            ui.notify(f"Foto principal selecionada: {nome}")

        ui.upload(label="Foto principal", on_upload=_on_upload_foto, auto_upload=True,
                  max_files=1).props('accept=".jpg,.jpeg,.png,.webp"').classes("w-full")

        # Datas
        ui.separator()
        ui.label("Datas").classes("text-subtitle2")
        i_data_dev = ui.input("Data devolução *",
                               value=valores["data_devolucao"].isoformat()).classes("w-full")
        i_data_dev.props('type=date')
        i_data_compra = ui.input("Data da compra original",
                                  value=valores["data_compra_original"].isoformat()
                                  if valores["data_compra_original"] else "").classes("w-full")
        i_data_compra.props('type=date')

        # NFs
        ui.separator()
        ui.label("Notas Fiscais (opcional)").classes("text-subtitle2")
        i_nf_orig = ui.input("NF de origem", value=valores["nf_origem"]).classes("w-full")
        i_nf_abat = ui.input("NF de abatimento", value=valores["nf_abatimento"]).classes("w-full")

        # Cliente
        ui.separator()
        ui.label("Cliente (opcional)").classes("text-subtitle2")
        i_cli_nome = ui.input("Nome", value=valores["cliente_nome"]).classes("w-full")
        i_cli_ctt = ui.input("Contato", value=valores["cliente_contato"]).classes("w-full")
        i_aguardando = ui.checkbox("Cliente aguardando retorno",
                                    value=valores["cliente_aguardando_retorno"])

        # Status
        ui.separator()
        ui.label("Status").classes("text-subtitle2")
        opcoes_status = {s.value: STATUS_PROCESSO_LABELS[s][0] for s in StatusProcesso}
        sel_status = ui.select(opcoes_status, label="Processo").classes("w-full")
        sel_status.value = valores["status_processo"].value

        opcoes_dest = {dd.value: DESTINO_FISICO_LABELS[dd][0] for dd in DestinoFisico}
        sel_dest = ui.select(opcoes_dest, label="Destino físico").classes("w-full")
        sel_dest.value = valores["destino_fisico"].value

        opcoes_forma = {None: "—"} | {f.value: FORMA_RESSARCIMENTO_LABELS[f][0]
                                       for f in FormaRessarcimento}
        sel_forma = ui.select(opcoes_forma, label="Forma de ressarcimento").classes("w-full")
        sel_forma.value = valores["forma_ressarcimento"].value if valores["forma_ressarcimento"] else None

        # Observações
        ui.separator()
        i_obs = ui.textarea("Observações", value=valores["observacoes"]).classes("w-full")

        # Botões
        def salvar():
            if not i_modelo.value or not i_modelo.value.strip():
                ui.notify("Modelo é obrigatório", type="negative")
                return
            try:
                dd = date.fromisoformat(i_data_dev.value)
            except Exception:
                ui.notify("Data de devolução inválida", type="negative")
                return
            dc = None
            if i_data_compra.value:
                try:
                    dc = date.fromisoformat(i_data_compra.value)
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
                data_devolucao=dd,
                data_compra_original=dc,
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

                if foto_principal_temp["path"]:
                    try:
                        anexo_service.salvar_anexo(s, novo_id, foto_principal_temp["path"],
                                                    como_principal=True)
                    except Exception as e:
                        ui.notify(f"Erro na foto principal: {e}", type="warning")

            ui.notify("Salvo", type="positive")
            dlg.close()
            if on_save:
                on_save()

        with ui.row().classes("w-full justify-end q-pt-md"):
            ui.button("Cancelar", on_click=dlg.close).props("flat")
            ui.button("Salvar", on_click=salvar).classes("bg-primary text-white")

    dlg.open()
