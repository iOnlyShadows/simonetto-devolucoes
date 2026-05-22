import webbrowser
from pathlib import Path
from typing import Callable, Optional

from nicegui import ui

from app.config import Config
from app.constants import (DESTINO_FISICO_LABELS, FORMA_RESSARCIMENTO_LABELS,
                            STATUS_PROCESSO_LABELS)
from app.db import session_scope
from app.repositories import historico_repo
from app.services import anexo_service, devolucao_service, lixeira_service
from app.ui.components.badge_status import (badge_destino, badge_forma,
                                              badge_status_processo)


def abrir_detalhe(devolucao_id: int,
                   on_save: Optional[Callable[[], None]] = None) -> None:
    from app.ui.components.form_devolucao import abrir_form_devolucao

    with session_scope() as s:
        d = devolucao_service.buscar(s, devolucao_id)
        if d is None:
            ui.notify("Devolução não encontrada", type="negative")
            return
        # Carrega tudo agora pra usar fora da sessão
        dados = dict(
            id=d.id,
            marca=d.marca.nome,
            modelo=d.produto_modelo,
            referencia=d.produto_referencia,
            quantidade=d.quantidade,
            valor=float(d.valor_custo) if d.valor_custo else None,
            defeito=d.defeito_descricao,
            data_dev=d.data_devolucao,
            data_compra=d.data_compra_original,
            nf_origem=d.nf_origem,
            nf_abat=d.nf_abatimento,
            cliente_nome=d.cliente_nome,
            cliente_contato=d.cliente_contato,
            aguardando=d.cliente_aguardando_retorno,
            status=d.status_processo,
            destino=d.destino_fisico,
            forma=d.forma_ressarcimento,
            observacoes=d.observacoes,
            foto=d.foto_principal_caminho,
            anexos=[(a.id, a.nome_original, a.caminho_interno, a.tipo) for a in d.anexos],
        )
        historico = [(h.campo, h.valor_anterior, h.valor_novo, h.data, h.observacao)
                     for h in historico_repo.listar_por_devolucao(s, devolucao_id)]

    cfg = Config.load()

    with ui.dialog().props("maximized=false") as dlg, ui.card().classes("w-[700px] max-h-[90vh] overflow-auto"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(f"{dados['marca']} · {dados['modelo']}").classes("text-h6")
            ui.button(icon="close", on_click=dlg.close).props("flat round")

        # Foto + badges
        with ui.row().classes("w-full gap-4 items-start"):
            if dados["foto"]:
                ui.image((cfg.data_dir / dados["foto"]).as_posix()).classes("w-32 h-32 rounded")
            with ui.column().classes("gap-2"):
                ui.label(f"Devolvido em {dados['data_dev'].strftime('%d/%m/%Y')}").classes("text-caption")
                if dados["referencia"]:
                    ui.label(f"Ref: {dados['referencia']}").classes("text-caption")
                with ui.row().classes("gap-2 items-center"):
                    badge_status_processo(dados["status"])
                    badge_destino(dados["destino"])
                    badge_forma(dados["forma"])

        ui.separator()

        # Detalhes
        with ui.column().classes("gap-1"):
            ui.label("Detalhes").classes("text-subtitle2")
            ui.label(f"Quantidade: {dados['quantidade']}"
                     + (f"   Valor: R$ {dados['valor']:.2f}" if dados['valor'] else ""))
            if dados["defeito"]:
                ui.label(f"Defeito: {dados['defeito']}")
            if dados["nf_origem"] or dados["nf_abat"]:
                ui.label(f"NF origem: {dados['nf_origem'] or '—'}   "
                         f"NF abatimento: {dados['nf_abat'] or '—'}")
            if dados["cliente_nome"]:
                cli = dados["cliente_nome"]
                if dados["aguardando"]:
                    cli += " ⏳ (aguardando retorno)"
                if dados["cliente_contato"]:
                    cli += f" · {dados['cliente_contato']}"
                ui.label(f"Cliente: {cli}")

        # Anexos
        ui.separator()
        ui.label("Anexos").classes("text-subtitle2")

        def _on_upload_extra(e):
            from pathlib import Path
            from tempfile import mkdtemp
            tmp = Path(mkdtemp()) / e.name  # preserva nome original
            tmp.write_bytes(e.content.read())
            try:
                with session_scope() as s:
                    anexo_service.salvar_anexo(s, devolucao_id, tmp,
                                                como_principal=False)
                ui.notify("Anexo adicionado")
                dlg.close()
                abrir_detalhe(devolucao_id, on_save=on_save)
            except ValueError as err:
                ui.notify(str(err), type="negative")

        ui.upload(label="+ Adicionar anexo",
                  on_upload=_on_upload_extra, auto_upload=True) \
            .props('accept=".pdf,.jpg,.jpeg,.png,.webp"').classes("w-full")

        if not dados["anexos"]:
            ui.label("Nenhum anexo ainda.").classes("text-grey-7")
        else:
            for aid, nome, caminho, tipo in dados["anexos"]:
                with ui.row().classes("items-center gap-2"):
                    ui.icon("picture_as_pdf" if tipo == "pdf" else "image")
                    ui.label(nome)
                    ui.button("Abrir",
                              on_click=lambda _, c=caminho: webbrowser.open(
                                  (cfg.data_dir / c).as_uri())) \
                        .props("flat size=sm")
                    def _remover(aid=aid):
                        with session_scope() as s:
                            anexo_service.remover_anexo(s, aid)
                        ui.notify("Anexo removido")
                        dlg.close()
                        abrir_detalhe(devolucao_id, on_save=on_save)
                    ui.button("Remover", on_click=_remover).props("flat size=sm color=red")

        # Observações
        if dados["observacoes"]:
            ui.separator()
            ui.label("Observações").classes("text-subtitle2")
            ui.label(dados["observacoes"]).classes("whitespace-pre-wrap")

        # Linha do tempo
        ui.separator()
        ui.label("Linha do tempo").classes("text-subtitle2")
        with ui.column().classes("gap-1"):
            for campo, anterior, novo, data, obs in historico:
                data_str = data.strftime("%d/%m/%Y %H:%M")
                if campo == "status_processo":
                    from app.constants import StatusProcesso
                    label_novo = STATUS_PROCESSO_LABELS[StatusProcesso(novo)][0]
                    texto = f"• {data_str}  Status → {label_novo}"
                else:
                    from app.constants import DestinoFisico
                    label_novo = DESTINO_FISICO_LABELS[DestinoFisico(novo)][0]
                    texto = f"• {data_str}  Destino → {label_novo}"
                if obs:
                    texto += f"  ({obs})"
                ui.label(texto).classes("text-caption")

        # Ações
        ui.separator()
        with ui.row().classes("w-full justify-end gap-2"):
            def _excluir():
                with ui.dialog() as confirm, ui.card():
                    ui.label("Mover para a lixeira?")
                    ui.label("Você terá 30 dias para restaurar.").classes("text-caption text-grey-7")
                    with ui.row():
                        ui.button("Cancelar", on_click=confirm.close).props("flat")
                        def fazer():
                            with session_scope() as s:
                                lixeira_service.enviar_para_lixeira(s, devolucao_id)
                            ui.notify("Movida para a lixeira")
                            confirm.close()
                            dlg.close()
                            if on_save:
                                on_save()
                        ui.button("Mover", on_click=fazer).classes("bg-red text-white")
                confirm.open()

            ui.button("Excluir", icon="delete", on_click=_excluir).props("flat color=red")
            ui.button("Editar", icon="edit",
                      on_click=lambda: (dlg.close(),
                                         abrir_form_devolucao(devolucao_id, on_save=on_save))) \
                .classes("bg-primary text-white")

    dlg.open()
