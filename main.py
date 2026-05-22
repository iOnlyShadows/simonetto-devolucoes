from nicegui import app, ui

from app.config import Config
from app.db import init_engine
from app.services import backup_service, lixeira_service
from app.db import session_scope


def _boot():
    cfg = Config.load()
    init_engine()
    with session_scope() as s:
        lixeira_service.expurgar_antigas(s)
    # Expoe a pasta de anexos como rota estatica /dados/...
    # Necessario pra ui.image() conseguir carregar fotos/thumbnails do disco.
    app.add_static_files("/dados", str(cfg.data_dir))


def _at_shutdown():
    try:
        backup_service.criar_backup()
    except Exception as e:
        print(f"Falha no backup automático: {e}")


# Registra páginas
from app.ui.pages import lista, marcas, lixeira, configuracoes  # noqa: E402


@ui.page("/")
def pagina_lista():
    lista.render()


@ui.page("/marcas")
def pagina_marcas():
    marcas.render()


@ui.page("/lixeira")
def pagina_lixeira():
    lixeira.render()


@ui.page("/configuracoes")
def pagina_configuracoes():
    configuracoes.render()


_boot()
app.on_shutdown(_at_shutdown)

ui.run(title="Simonetto Devoluções", native=True, window_size=(1280, 800),
       reload=False, show=False)
