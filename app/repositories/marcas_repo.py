from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import FormaRessarcimento
from app.models.marca import Marca


def criar(session: Session, *, nome: str,
          forma_padrao: Optional[FormaRessarcimento] = None,
          observacoes: Optional[str] = None) -> Marca:
    marca = Marca(nome=nome, forma_ressarcimento_padrao=forma_padrao,
                  observacoes=observacoes)
    session.add(marca)
    return marca


def buscar_por_id(session: Session, marca_id: int) -> Optional[Marca]:
    return session.get(Marca, marca_id)


def listar(session: Session) -> list[Marca]:
    return list(session.scalars(select(Marca).order_by(Marca.nome)))


def atualizar(session: Session, marca_id: int, **campos) -> Optional[Marca]:
    marca = session.get(Marca, marca_id)
    if marca is None:
        return None
    for k, v in campos.items():
        setattr(marca, k, v)
    return marca


def excluir(session: Session, marca_id: int) -> bool:
    marca = session.get(Marca, marca_id)
    if marca is None:
        return False
    session.delete(marca)
    return True
