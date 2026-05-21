from typing import Callable, Optional
from nicegui import ui


def abrir_form_devolucao(devolucao_id: Optional[int] = None,
                          on_save: Optional[Callable[[], None]] = None) -> None:
    ui.notify("Form de devolução em construção (Task 18)", type="warning")
