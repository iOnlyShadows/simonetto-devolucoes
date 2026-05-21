from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.historico import HistoricoStatus


def registrar(session: Session, *, devolucao_id: int, campo: str,
              valor_anterior: Optional[str], valor_novo: str,
              observacao: Optional[str] = None) -> HistoricoStatus:
    h = HistoricoStatus(
        devolucao_id=devolucao_id, campo=campo,
        valor_anterior=valor_anterior, valor_novo=valor_novo,
        observacao=observacao,
    )
    session.add(h)
    return h


def listar_por_devolucao(session: Session, devolucao_id: int) -> list[HistoricoStatus]:
    q = select(HistoricoStatus).where(HistoricoStatus.devolucao_id == devolucao_id) \
        .order_by(HistoricoStatus.data)
    return list(session.scalars(q))
