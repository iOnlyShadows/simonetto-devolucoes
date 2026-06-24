import multiprocessing
import os
import sys
from pathlib import Path

from nicegui import app, ui

from app.config import Config
from app.db import init_engine
from app.services import backup_service, lixeira_service
from app.db import session_scope

# Em modo "congelado" (PyInstaller) os assets ficam na pasta temporaria _MEIPASS;
# rodando do codigo, ficam ao lado do main.py.
_BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
ASSETS_DIR = _BASE_DIR / "app" / "ui" / "assets"
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
    # Expoe APENAS a pasta de anexos como rota estatica /dados/...
    # (nao a data_dir inteira: assim o banco e os backups NAO ficam baixaveis
    # pela rede no modo servidor). Necessario pra ui.image() carregar fotos.
    app.add_static_files("/dados", str(cfg.anexos_dir))


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


def _modo_servidor() -> bool:
    # O executavel (.exe) sempre roda como servidor de rede.
    if getattr(sys, "frozen", False):
        return True
    return os.environ.get("SIMONETTO_SERVER", "").strip().lower() in (
        "1", "true", "yes", "on")


def _print_banner(porta: int) -> None:
    import socket
    ip = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    linha = "=" * 52
    print(linha)
    print("  Simonetto Devolucoes - servidor da rede local")
    print(linha)
    print(f"  Neste PC:      http://localhost:{porta}")
    if ip:
        print(f"  No outro PC:   http://{ip}:{porta}")
    print("  Deixe esta janela ABERTA enquanto usar o app.")
    print(linha, flush=True)


if __name__ in {"__main__", "__mp_main__"}:
    multiprocessing.freeze_support()  # necessario p/ executavel onefile no Windows
    if _modo_servidor():
        # Modo rede local: servidor web acessivel pelos 2 PCs.
        # host=0.0.0.0 -> aceita conexoes da rede; o 2o PC abre http://<ip>:<porta>
        _porta = int(os.environ.get("SIMONETTO_PORT", "8080"))
        _print_banner(_porta)
        ui.run(
            title="Simonetto Devoluções",
            host="0.0.0.0",
            port=_porta,
            native=False,
            reload=False,
            show=False,
            storage_secret=os.environ.get("SIMONETTO_SECRET", "simonetto-devolucoes-lan"),
        )
    else:
        # Modo desktop: janela nativa (uso em 1 PC / desenvolvimento)
        ui.run(title="Simonetto Devoluções", native=True, window_size=(1280, 800),
               reload=False, show=False)
