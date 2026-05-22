"""Pílulas clicáveis que abrem dropdown para mudar status/destino/forma direto
do detalhe da devolução, sem precisar abrir o formulário de edição.
"""
from typing import Callable, Optional
from nicegui import ui

from app.constants import (
    DESTINO_FISICO_LABELS, DestinoFisico,
    FORMA_RESSARCIMENTO_LABELS, FormaRessarcimento,
    STATUS_PROCESSO_LABELS, StatusProcesso,
)
from app.ui.components.badge_status import _COR_PARA_VAR


def _pill_button(label: str, cor_quasar: str, icone: str,
                  on_click: Callable[[], None]) -> ui.element:
    cor = _COR_PARA_VAR.get(cor_quasar, "var(--text-secondary)")
    el = ui.html(
        f'<span class="app-pill clickable" '
        f'style="color: {cor}; border-color: color-mix(in srgb, {cor} 30%, transparent);">'
        f'<span class="dot" style="background: {cor};"></span>'
        f'{icone} {label}'
        f'</span>'
    ).on("click", lambda _: on_click())
    return el


def pill_dropdown_status(atual: StatusProcesso,
                          on_change: Callable[[StatusProcesso], None]) -> None:
    label, cor, icone = STATUS_PROCESSO_LABELS[atual]
    with ui.element("div").style("display: inline-block; position: relative;"):
        def abrir():
            with ui.menu() as menu:
                for s in StatusProcesso:
                    if s == atual:
                        continue
                    s_label, _, s_icone = STATUS_PROCESSO_LABELS[s]
                    ui.menu_item(f"{s_icone} {s_label}",
                                 lambda s=s: (on_change(s), menu.close()))
            menu.open()
        _pill_button(label, cor, icone, abrir)


def pill_dropdown_destino(atual: DestinoFisico,
                           on_change: Callable[[DestinoFisico], None]) -> None:
    label, cor, icone = DESTINO_FISICO_LABELS[atual]
    with ui.element("div").style("display: inline-block; position: relative;"):
        def abrir():
            with ui.menu() as menu:
                for d in DestinoFisico:
                    if d == atual:
                        continue
                    d_label, _, d_icone = DESTINO_FISICO_LABELS[d]
                    ui.menu_item(f"{d_icone} {d_label}",
                                 lambda d=d: (on_change(d), menu.close()))
            menu.open()
        _pill_button(label, cor, icone, abrir)


def pill_dropdown_forma(atual: Optional[FormaRessarcimento],
                         on_change: Callable[[Optional[FormaRessarcimento]], None]) -> None:
    if atual is None:
        label, icone = ("Sem forma", "❓")
    else:
        label, icone = FORMA_RESSARCIMENTO_LABELS[atual]
    cor = "var(--text-secondary)"

    with ui.element("div").style("display: inline-block; position: relative;"):
        def abrir():
            with ui.menu() as menu:
                for f in FormaRessarcimento:
                    if f == atual:
                        continue
                    f_label, f_icone = FORMA_RESSARCIMENTO_LABELS[f]
                    ui.menu_item(f"{f_icone} {f_label}",
                                 lambda f=f: (on_change(f), menu.close()))
            menu.open()
        el = ui.html(
            f'<span class="app-pill clickable" '
            f'style="color: {cor}; border-color: var(--border-subtle);">'
            f'{icone} {label}'
            f'</span>'
        ).on("click", lambda _: abrir())
