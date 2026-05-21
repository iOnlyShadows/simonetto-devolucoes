from datetime import datetime
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.constants import DestinoFisico, StatusProcesso
from app.models.devolucao import Devolucao


def criar(session: Session, **campos) -> Devolucao:
    d = Devolucao(**campos)
    session.add(d)
    return d


def buscar_por_id(session: Session, devolucao_id: int) -> Optional[Devolucao]:
    return session.get(Devolucao, devolucao_id)


def _base_query():
    return select(Devolucao).options(
        joinedload(Devolucao.marca),
        joinedload(Devolucao.anexos),
    )


def listar_ativas(session: Session, *,
                  marca_id: Optional[int] = None,
                  status: Optional[StatusProcesso] = None,
                  destino: Optional[DestinoFisico] = None,
                  aguardando_retorno: Optional[bool] = None,
                  busca: Optional[str] = None) -> list[Devolucao]:
    q = _base_query().where(Devolucao.excluido_em.is_(None))
    if marca_id is not None:
        q = q.where(Devolucao.marca_id == marca_id)
    if status is not None:
        q = q.where(Devolucao.status_processo == status)
    if destino is not None:
        q = q.where(Devolucao.destino_fisico == destino)
    if aguardando_retorno is True:
        q = q.where(Devolucao.cliente_aguardando_retorno.is_(True))
    if busca:
        termo = f"%{busca.lower()}%"
        q = q.where(or_(
            Devolucao.produto_modelo.ilike(termo),
            Devolucao.produto_referencia.ilike(termo),
            Devolucao.cliente_nome.ilike(termo),
            Devolucao.observacoes.ilike(termo),
        ))
    q = q.order_by(Devolucao.data_devolucao.desc(), Devolucao.id.desc())
    return list(session.scalars(q).unique())


def listar_lixeira(session: Session) -> list[Devolucao]:
    q = _base_query().where(Devolucao.excluido_em.is_not(None)) \
        .order_by(Devolucao.excluido_em.desc())
    return list(session.scalars(q).unique())


def marcar_como_excluida(session: Session, devolucao_id: int) -> bool:
    d = session.get(Devolucao, devolucao_id)
    if d is None:
        return False
    d.excluido_em = datetime.utcnow()
    return True


def restaurar(session: Session, devolucao_id: int) -> bool:
    d = session.get(Devolucao, devolucao_id)
    if d is None or d.excluido_em is None:
        return False
    d.excluido_em = None
    return True


def excluir_definitivo(session: Session, devolucao_id: int) -> bool:
    d = session.get(Devolucao, devolucao_id)
    if d is None:
        return False
    session.delete(d)
    return True
