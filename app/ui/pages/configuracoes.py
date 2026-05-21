from pathlib import Path

from nicegui import ui

from app.config import Config
from app.services import backup_service


def render():
    from app.ui.layout import montar_layout
    montar_layout("Configurações")

    cfg = Config.load()

    with ui.column().classes("w-full max-w-3xl gap-4"):
        ui.label("Dados").classes("text-h6")
        ui.label(f"Pasta de dados: {cfg.data_dir}").classes("text-caption")
        ui.label(f"Banco: {cfg.db_path}").classes("text-caption")
        ui.label(f"Anexos: {cfg.anexos_dir}").classes("text-caption")

        ui.separator()
        ui.label("Backup").classes("text-h6")

        i_pasta = ui.input("Pasta de backup",
                            value=str(cfg.backup_folder)).classes("w-full")
        i_freq = ui.select(
            {"on_close": "Ao fechar o app",
             "daily": "Diariamente (futuro)",
             "weekly": "Semanalmente (futuro)",
             "manual": "Apenas manual"},
            value=cfg.backup_frequency,
            label="Frequência",
        ).classes("w-full")
        i_ret = ui.number("Manter últimos N backups",
                           value=cfg.backup_retention, min=1).classes("w-full")

        def salvar_cfg():
            cfg.backup_folder = Path(i_pasta.value)
            cfg.backup_frequency = i_freq.value
            cfg.backup_retention = int(i_ret.value or 30)
            cfg.save()
            ui.notify("Configurações salvas", type="positive")

        ui.button("Salvar", on_click=salvar_cfg).classes("bg-primary text-white")

        ui.separator()
        ui.label("Backup manual").classes("text-h6")

        def fazer_backup():
            try:
                caminho = backup_service.criar_backup()
                ui.notify(f"Backup criado: {caminho.name}", type="positive")
                recarregar_lista_backups()
            except Exception as e:
                ui.notify(f"Erro: {e}", type="negative")

        ui.button("Fazer backup agora", on_click=fazer_backup) \
            .classes("bg-primary text-white")

        lista_container = ui.column().classes("w-full")

        def recarregar_lista_backups():
            lista_container.clear()
            with lista_container:
                ui.label("Últimos backups").classes("text-subtitle1")
                infos = backup_service.listar_backups()
                if not infos:
                    ui.label("Nenhum backup ainda.").classes("text-grey-7")
                for info in infos[:10]:
                    ui.label(
                        f"• {info.criado_em.strftime('%d/%m/%Y %H:%M')} "
                        f"· {info.tamanho_bytes / 1024:.1f} KB "
                        f"· {info.caminho.name}"
                    ).classes("text-caption")

        recarregar_lista_backups()
