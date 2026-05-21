from typing import Callable, Optional
from nicegui import ui


def abrir_detalhe(devolucao_id: int,
                   on_save: Optional[Callable[[], None]] = None) -> None:
    ui.notify(f"Detalhe da devolução {devolucao_id} em construção (Task 19)", type="warning")
