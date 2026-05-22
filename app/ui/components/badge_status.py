"""Pílulas semânticas dos 3 eixos (status, destino, forma de ressarcimento).

Cada função renderiza uma pílula estática (apenas exibição).
Para pílulas clicáveis com dropdown, ver pill_dropdown.py.
"""
from nicegui import ui

from app.constants import (
    DESTINO_FISICO_LABELS, DestinoFisico,
    FORMA_RESSARCIMENTO_LABELS, FormaRessarcimento,
    STATUS_PROCESSO_LABELS, StatusProcesso,
)

# Mapeamento de cores Quasar (usadas no plano antigo) para as CSS vars do novo tema
_COR_PARA_VAR = {
    "red": "var(--status-red)",
    "yellow": "var(--status-yellow)",
    "orange": "var(--status-orange)",
    "green": "var(--status-green)",
    "grey": "var(--dest-slate)",
    "blue": "var(--dest-blue)",
    "purple": "var(--dest-purple)",
    "black": "var(--dest-zinc)",
}


def _pill(label: str, cor_quasar: str, icone: str) -> ui.html:
    cor = _COR_PARA_VAR.get(cor_quasar, "var(--text-secondary)")
    return ui.html(
        f'<span class="app-pill" '
        f'style="color: {cor}; border-color: color-mix(in srgb, {cor} 30%, transparent);">'
        f'<span class="dot" style="background: {cor};"></span>'
        f'{icone} {label}'
        f'</span>'
    )


def badge_status_processo(status: StatusProcesso) -> ui.html:
    label, cor, icone = STATUS_PROCESSO_LABELS[status]
    return _pill(label, cor, icone)


def badge_destino(destino: DestinoFisico) -> ui.html:
    label, cor, icone = DESTINO_FISICO_LABELS[destino]
    return _pill(label, cor, icone)


def badge_forma(forma: FormaRessarcimento | None) -> ui.html | None:
    if forma is None:
        return None
    label, icone = FORMA_RESSARCIMENTO_LABELS[forma]
    return ui.html(
        f'<span class="app-pill" '
        f'style="color: var(--text-secondary); border-color: var(--border-subtle);">'
        f'{icone} {label}'
        f'</span>'
    )
