"""Cliente nativo do Simonetto Devoluções.

Abre o servidor (que roda no PC principal) numa JANELA NATIVA, sem navegador.
Roda nos 2 PCs; a URL do servidor é resolvida nesta ordem:

1. argumento de linha de comando:  Simonetto-Cliente.exe http://192.168.1.12:8080
2. variável de ambiente SIMONETTO_URL
3. arquivo `servidor.txt` ao lado do executável (uma linha com a URL)
4. padrão: http://localhost:8080  (uso no próprio PC principal)
"""
import os
import sys
from pathlib import Path

import webview


def _resolver_url() -> str:
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()
    env = os.environ.get("SIMONETTO_URL", "").strip()
    if env:
        return env
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    txt = base / "servidor.txt"
    if txt.exists():
        linha = txt.read_text(encoding="utf-8").strip()
        if linha:
            return linha
    return "http://localhost:8080"


def main() -> None:
    url = _resolver_url()
    webview.create_window("Simonetto Devoluções", url, width=1280, height=800)
    # gui=edgechromium: forca o backend moderno (Edge WebView2).
    # private_mode=False: mantem cookies/localStorage (a sessao do NiceGUI usa).
    webview.start(gui="edgechromium", private_mode=False)


if __name__ == "__main__":
    main()
