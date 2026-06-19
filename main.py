from pathlib import Path

from nicegui import app, ui

from app.config import Config
from app.db import init_engine
from app.services import backup_service, lixeira_service
from app.db import session_scope

ASSETS_DIR = Path(__file__).parent / "app" / "ui" / "assets"
app.add_static_files("/assets", str(ASSETS_DIR))
ui.add_head_html('<link rel="stylesheet" href="/assets/app.css">', shared=True)

# Delegação global: clicar em qualquer lugar de uma .app-upload-zone abre o
# seletor de arquivo (não só no botão "+"). Quasar coloca o <input type=file>
# escondido dentro do botão; aqui encaminhamos o clique da div inteira pra ele.
ui.add_head_html('''<script>
(function () {
  if (window.__simUploadDelegate) return;
  window.__simUploadDelegate = true;
  document.addEventListener('click', function (e) {
    var zone = e.target.closest('.app-upload-zone');
    if (!zone) return;
    if (e.target.closest('button')) return;            // botões agem normalmente
    if (e.target.matches('input[type=file]')) return;  // evita clique duplo
    var input = zone.querySelector('input[type=file]');
    if (input) input.click();
  }, true);
})();
</script>''', shared=True)


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
