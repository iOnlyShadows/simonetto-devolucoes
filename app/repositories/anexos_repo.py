from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.anexo import Anexo


def criar(session: Session, *, devolucao_id: int, nome_original: str,
          caminho_interno: str, tipo: str, tamanho_bytes: int) -> Anexo:
    a = Anexo(devolucao_id=devolucao_id, nome_original=nome_original,
              caminho_interno=caminho_interno, tipo=tipo, tamanho_bytes=tamanho_bytes)
    session.add(a)
    return a


def buscar_por_id(session: Session, anexo_id: int) -> Optional[Anexo]:
    return session.get(Anexo, anexo_id)


def listar_por_devolucao(session: Session, devolucao_id: int) -> list[Anexo]:
    q = select(Anexo).where(Anexo.devolucao_id == devolucao_id) \
        .order_by(Anexo.criado_em)
    return list(session.scalars(q))


def excluir(session: Session, anexo_id: int) -> bool:
    a = session.get(Anexo, anexo_id)
    if a is None:
        return False
    session.delete(a)
    return True
