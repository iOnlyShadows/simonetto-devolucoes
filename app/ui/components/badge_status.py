from nicegui import ui

from app.constants import (
    DESTINO_FISICO_LABELS,
    DestinoFisico,
    FORMA_RESSARCIMENTO_LABELS,
    FormaRessarcimento,
    STATUS_PROCESSO_LABELS,
    StatusProcesso,
)


def badge_status_processo(status: StatusProcesso) -> None:
    label, cor, icone = STATUS_PROCESSO_LABELS[status]
    ui.badge(f"{icone} {label}", color=cor).classes("text-white q-pa-xs")


def badge_destino(destino: DestinoFisico) -> None:
    label, cor, icone = DESTINO_FISICO_LABELS[destino]
    ui.badge(f"{icone} {label}", color=cor).classes("text-white q-pa-xs")


def badge_forma(forma: FormaRessarcimento | None) -> None:
    if forma is None:
        return
    label, icone = FORMA_RESSARCIMENTO_LABELS[forma]
    ui.label(f"{icone} {label}").classes("text-caption")
