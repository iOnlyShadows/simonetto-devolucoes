from nicegui import ui

from app.constants import FormaRessarcimento, FORMA_RESSARCIMENTO_LABELS
from app.db import session_scope
from app.repositories import marcas_repo


def render():
    from app.ui.layout import montar_layout
    montar_layout("Marcas")

    container = ui.column().classes("w-full max-w-3xl")

    def recarregar():
        container.clear()
        with container:
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("Marcas cadastradas").classes("text-h6")
                ui.button("+ Nova marca", on_click=abrir_form_nova) \
                    .classes("bg-primary text-white")

            with session_scope() as s:
                marcas = marcas_repo.listar(s)
                marcas_data = [(m.id, m.nome,
                                 m.forma_ressarcimento_padrao.value if m.forma_ressarcimento_padrao else None,
                                 m.observacoes) for m in marcas]

            if not marcas_data:
                ui.label("Nenhuma marca cadastrada ainda.").classes("text-grey-7")
                return

            for mid, nome, forma, obs in marcas_data:
                with ui.card().classes("w-full"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.column():
                            ui.label(nome).classes("text-subtitle1 font-bold")
                            if forma:
                                label_forma = FORMA_RESSARCIMENTO_LABELS[FormaRessarcimento(forma)][0]
                                ui.label(f"Padrão: {label_forma}").classes("text-caption")
                            if obs:
                                ui.label(obs).classes("text-caption text-grey-7")
                        with ui.row():
                            ui.button(icon="edit",
                                      on_click=lambda _, i=mid: abrir_form_editar(i)).props("flat round")
                            ui.button(icon="delete",
                                      on_click=lambda _, i=mid, n=nome: confirmar_excluir(i, n)).props("flat round color=red")

    def abrir_form_nova():
        abrir_form(None)

    def abrir_form_editar(marca_id: int):
        abrir_form(marca_id)

    def abrir_form(marca_id):
        with session_scope() as s:
            marca = marcas_repo.buscar_por_id(s, marca_id) if marca_id else None
            nome = marca.nome if marca else ""
            forma = marca.forma_ressarcimento_padrao.value if marca and marca.forma_ressarcimento_padrao else None
            obs = marca.observacoes if marca else ""

        with ui.dialog() as dlg, ui.card().classes("w-96"):
            ui.label("Editar marca" if marca_id else "Nova marca").classes("text-h6")
            campo_nome = ui.input("Nome *").classes("w-full")
            campo_nome.value = nome
            campo_forma = ui.select(
                options={None: "—"} | {f.value: FORMA_RESSARCIMENTO_LABELS[f][0]
                                        for f in FormaRessarcimento},
                label="Forma padrão de ressarcimento"
            ).classes("w-full")
            campo_forma.value = forma
            campo_obs = ui.textarea("Observações").classes("w-full")
            campo_obs.value = obs

            def salvar():
                if not campo_nome.value or not campo_nome.value.strip():
                    ui.notify("Nome é obrigatório", type="negative")
                    return
                forma_enum = FormaRessarcimento(campo_forma.value) if campo_forma.value else None
                with session_scope() as s:
                    if marca_id:
                        marcas_repo.atualizar(s, marca_id, nome=campo_nome.value.strip(),
                                              forma_ressarcimento_padrao=forma_enum,
                                              observacoes=campo_obs.value or None)
                    else:
                        marcas_repo.criar(s, nome=campo_nome.value.strip(),
                                          forma_padrao=forma_enum,
                                          observacoes=campo_obs.value or None)
                dlg.close()
                ui.notify("Salvo", type="positive")
                recarregar()

            with ui.row().classes("justify-end w-full"):
                ui.button("Cancelar", on_click=dlg.close).props("flat")
                ui.button("Salvar", on_click=salvar).classes("bg-primary text-white")
        dlg.open()

    def confirmar_excluir(marca_id: int, nome: str):
        with ui.dialog() as dlg, ui.card():
            ui.label(f"Excluir marca '{nome}'?")
            ui.label("Atenção: só funciona se não houver devoluções vinculadas.").classes("text-caption text-grey-7")
            with ui.row():
                ui.button("Cancelar", on_click=dlg.close).props("flat")
                def fazer():
                    try:
                        with session_scope() as s:
                            marcas_repo.excluir(s, marca_id)
                        ui.notify("Excluída", type="positive")
                        dlg.close()
                        recarregar()
                    except Exception as e:
                        ui.notify(f"Não foi possível excluir: {e}", type="negative")
                ui.button("Excluir", on_click=fazer).classes("bg-red text-white")
        dlg.open()

    recarregar()
