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
            # ── cabeçalho ──────────────────────────────────────────────────
            with ui.element("div").style(
                "display:flex; align-items:center; justify-content:space-between;"
                "padding-bottom:12px; border-bottom:1px solid var(--border-subtle);"
                "margin-bottom:16px;"
            ):
                ui.label("Marcas cadastradas").classes("app-section-label")
                ui.button("+ Nova marca", on_click=abrir_form_nova) \
                    .classes("bg-primary").props("unelevated")

            # ── buscar dados ───────────────────────────────────────────────
            with session_scope() as s:
                marcas = marcas_repo.listar(s)
                marcas_data = [
                    (m.id, m.nome,
                     m.forma_ressarcimento_padrao.value if m.forma_ressarcimento_padrao else None,
                     m.observacoes)
                    for m in marcas
                ]

            # ── empty state ────────────────────────────────────────────────
            if not marcas_data:
                with ui.element("div").style(
                    "display:flex; flex-direction:column; align-items:center;"
                    "padding:60px 20px; gap:12px;"
                ):
                    ui.label("🏷️").style("font-size:48px; line-height:1;")
                    ui.label("Nenhuma marca cadastrada ainda.").style(
                        "color:var(--text-secondary); font-size:14px;"
                    )
                    ui.button("+ Nova marca", on_click=abrir_form_nova) \
                        .classes("bg-primary").props("unelevated")
                return

            # ── lista de marcas ────────────────────────────────────────────
            for mid, nome, forma, obs in marcas_data:
                with ui.element("div").style(
                    "display:grid; grid-template-columns:1fr auto auto;"
                    "gap:8px; padding:12px 8px;"
                    "border-bottom:1px solid var(--border-faint);"
                    "align-items:center;"
                ):
                    # coluna nome + meta
                    with ui.element("div").style("display:flex; flex-direction:column; gap:2px;"):
                        ui.label(nome).style(
                            "font-size:14px; font-weight:500;"
                            "color:var(--text-primary);"
                        )
                        if forma:
                            label_forma = FORMA_RESSARCIMENTO_LABELS[FormaRessarcimento(forma)][0]
                            ui.label(f"Padrão: {label_forma}").style(
                                "font-size:12px; color:var(--text-secondary);"
                            )
                        if obs:
                            ui.label(obs).style(
                                "font-size:11px; color:var(--text-muted);"
                            )

                    # botão editar
                    ui.button(
                        icon="edit",
                        on_click=lambda _, i=mid: abrir_form_editar(i),
                    ).props("flat round dense").style("color:var(--text-secondary);")

                    # botão excluir
                    ui.button(
                        icon="delete",
                        on_click=lambda _, i=mid, n=nome: confirmar_excluir(i, n),
                    ).props("flat round dense").style("color:var(--danger);")

    # ── handlers ───────────────────────────────────────────────────────────

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

        with ui.dialog() as dlg, ui.card().style("width:400px; padding:24px; gap:16px;"):
            ui.label("Editar marca" if marca_id else "Nova marca").style(
                "font-size:15px; font-weight:600; color:var(--text-primary);"
            )

            campo_nome = ui.input("Nome *").classes("w-full").props("outlined dense")
            campo_nome.value = nome

            campo_forma = ui.select(
                options={None: "—"} | {f.value: FORMA_RESSARCIMENTO_LABELS[f][0]
                                        for f in FormaRessarcimento},
                label="Forma padrão de ressarcimento",
            ).classes("w-full").props("outlined dense")
            campo_forma.value = forma

            campo_obs = ui.textarea("Observações").classes("w-full").props("outlined dense")
            campo_obs.value = obs

            def salvar():
                if not campo_nome.value or not campo_nome.value.strip():
                    ui.notify("Nome é obrigatório", type="negative")
                    return
                forma_enum = FormaRessarcimento(campo_forma.value) if campo_forma.value else None
                with session_scope() as s:
                    if marca_id:
                        marcas_repo.atualizar(
                            s, marca_id,
                            nome=campo_nome.value.strip(),
                            forma_ressarcimento_padrao=forma_enum,
                            observacoes=campo_obs.value or None,
                        )
                    else:
                        marcas_repo.criar(
                            s,
                            nome=campo_nome.value.strip(),
                            forma_padrao=forma_enum,
                            observacoes=campo_obs.value or None,
                        )
                dlg.close()
                ui.notify("Salvo", type="positive")
                recarregar()

            with ui.row().classes("justify-end w-full").style("gap:8px; margin-top:8px;"):
                ui.button("Cancelar", on_click=dlg.close).props("flat")
                ui.button("Salvar", on_click=salvar).classes("bg-primary").props("unelevated")

        dlg.open()

    def confirmar_excluir(marca_id: int, nome: str):
        with ui.dialog() as dlg, ui.card().style("padding:24px; gap:12px; min-width:320px;"):
            ui.label(f"Excluir marca '{nome}'?").style(
                "font-size:15px; font-weight:600; color:var(--text-primary);"
            )
            ui.label("Atenção: só funciona se não houver devoluções vinculadas.").style(
                "font-size:12px; color:var(--text-muted);"
            )

            def fazer():
                try:
                    with session_scope() as s:
                        marcas_repo.excluir(s, marca_id)
                    ui.notify("Excluída", type="positive")
                    dlg.close()
                    recarregar()
                except Exception as e:
                    ui.notify(f"Não foi possível excluir: {e}", type="negative")

            with ui.row().classes("justify-end w-full").style("gap:8px; margin-top:4px;"):
                ui.button("Cancelar", on_click=dlg.close).props("flat")
                ui.button("Excluir", on_click=fazer).style(
                    "background:var(--danger); color:#fff;"
                ).props("unelevated")

        dlg.open()

    recarregar()
