from pathlib import Path

from nicegui import ui

from app.config import Config
from app.services import backup_service


def render():
    from app.ui.layout import montar_layout
    montar_layout("Configurações")

    cfg = Config.load()

    with ui.column().style("width:100%; max-width:600px; gap:0"):

        # ── DADOS ──────────────────────────────────────────────────────────
        ui.label("DADOS").classes("app-section-label")

        ui.label(f"Pasta de dados: {cfg.data_dir}").style(
            "color:var(--text-secondary); font-size:12px; font-family:var(--font-mono)"
        )
        ui.label(f"Banco: {cfg.db_path}").style(
            "color:var(--text-secondary); font-size:12px; font-family:var(--font-mono)"
        )
        ui.label(f"Anexos: {cfg.anexos_dir}").style(
            "color:var(--text-secondary); font-size:12px; font-family:var(--font-mono)"
        )

        ui.element("div").classes("app-divider")

        # ── BACKUP ─────────────────────────────────────────────────────────
        ui.label("BACKUP").classes("app-section-label")

        i_pasta = ui.input("Pasta de backup", value=str(cfg.backup_folder)) \
            .props("outlined dense").classes("w-full")
        i_freq = ui.select(
            {"on_close": "Ao fechar o app",
             "daily": "Diariamente (futuro)",
             "weekly": "Semanalmente (futuro)",
             "manual": "Apenas manual"},
            value=cfg.backup_frequency,
            label="Frequência",
        ).props("outlined dense").classes("w-full")
        i_ret = ui.number("Manter últimos N backups",
                           value=cfg.backup_retention, min=1) \
            .props("outlined dense").classes("w-full")

        def salvar_cfg():
            cfg.backup_folder = Path(i_pasta.value)
            cfg.backup_frequency = i_freq.value
            cfg.backup_retention = int(i_ret.value or 30)
            cfg.save()
            ui.notify("Configurações salvas", type="positive")

        ui.button("Salvar", on_click=salvar_cfg) \
            .props("unelevated").classes("bg-primary text-white")

        ui.element("div").classes("app-divider")

        # ── BACKUP MANUAL ──────────────────────────────────────────────────
        ui.label("BACKUP MANUAL").classes("app-section-label")

        def fazer_backup():
            try:
                caminho = backup_service.criar_backup()
                ui.notify(f"Backup criado: {caminho.name}", type="positive")
                recarregar_lista_backups()
            except Exception as e:
                ui.notify(f"Erro: {e}", type="negative")

        ui.button("Fazer backup agora", on_click=fazer_backup) \
            .props("unelevated").classes("bg-primary text-white")

        ui.label("Últimos backups").classes("app-section-label").style("margin-top:12px")

        lista_container = ui.column().classes("w-full").style("gap:4px")

        def recarregar_lista_backups():
            lista_container.clear()
            with lista_container:
                infos = backup_service.listar_backups()
                if not infos:
                    ui.label("Nenhum backup ainda.").style(
                        "color:var(--text-muted)"
                    )
                for info in infos[:10]:
                    data_hora = info.criado_em.strftime("%d/%m/%Y %H:%M")
                    tamanho = f"{info.tamanho_bytes / 1024:.1f} KB"
                    nome = info.caminho.name
                    with ui.row().style(
                        "background:var(--bg-elevated); "
                        "border:1px solid var(--border-faint); "
                        "padding:8px 10px; font-size:12px; "
                        "width:100%; align-items:center; gap:8px"
                    ):
                        ui.label(data_hora).style(
                            "font-family:var(--font-mono); "
                            "color:var(--text-secondary)"
                        )
                        ui.label(tamanho).style(
                            "color:var(--text-muted)"
                        )
                        ui.label(nome).style(
                            "font-family:var(--font-mono); "
                            "color:var(--text-secondary); "
                            "word-break:break-all"
                        )

        recarregar_lista_backups()
