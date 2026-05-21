from typing import Optional

from sqlalchemy.orm import Session

from app.constants import DestinoFisico, StatusProcesso
from app.models.devolucao import Devolucao
from app.repositories import devolucoes_repo, historico_repo, marcas_repo


def criar(session: Session, **campos) -> Devolucao:
    marca_id = campos.get("marca_id")
    # Se nao foi informada forma_ressarcimento, usa a padrao da marca
    if "forma_ressarcimento" not in campos and marca_id is not None:
        marca = marcas_repo.buscar_por_id(session, marca_id)
        if marca and marca.forma_ressarcimento_padrao:
            campos["forma_ressarcimento"] = marca.forma_ressarcimento_padrao

    d = devolucoes_repo.criar(session, **campos)
    session.flush()  # garante id

    historico_repo.registrar(
        session, devolucao_id=d.id, campo="status_processo",
        valor_anterior=None, valor_novo=d.status_processo.value,
    )
    historico_repo.registrar(
        session, devolucao_id=d.id, campo="destino_fisico",
        valor_anterior=None, valor_novo=d.destino_fisico.value,
    )
    return d


def buscar(session: Session, devolucao_id: int) -> Optional[Devolucao]:
    return devolucoes_repo.buscar_por_id(session, devolucao_id)


def mudar_status_processo(session: Session, devolucao_id: int, *,
                           novo: StatusProcesso,
                           observacao: Optional[str] = None) -> Optional[Devolucao]:
    d = devolucoes_repo.buscar_por_id(session, devolucao_id)
    if d is None or d.status_processo == novo:
        return d
    anterior = d.status_processo.value
    d.status_processo = novo
    historico_repo.registrar(
        session, devolucao_id=d.id, campo="status_processo",
        valor_anterior=anterior, valor_novo=novo.value, observacao=observacao,
    )
    return d


def mudar_destino_fisico(session: Session, devolucao_id: int, *,
                          novo: DestinoFisico,
                          observacao: Optional[str] = None) -> Optional[Devolucao]:
    d = devolucoes_repo.buscar_por_id(session, devolucao_id)
    if d is None or d.destino_fisico == novo:
        return d
    anterior = d.destino_fisico.value
    d.destino_fisico = novo
    historico_repo.registrar(
        session, devolucao_id=d.id, campo="destino_fisico",
        valor_anterior=anterior, valor_novo=novo.value, observacao=observacao,
    )
    return d


def atualizar(session: Session, devolucao_id: int, **campos) -> Optional[Devolucao]:
    """Atualiza qualquer combinação de campos. Se status_processo ou
    destino_fisico forem alterados, gera histórico automaticamente."""
    d = devolucoes_repo.buscar_por_id(session, devolucao_id)
    if d is None:
        return None

    novo_status = campos.pop("status_processo", None)
    novo_destino = campos.pop("destino_fisico", None)

    for k, v in campos.items():
        setattr(d, k, v)

    if novo_status is not None:
        mudar_status_processo(session, devolucao_id, novo=novo_status)
    if novo_destino is not None:
        mudar_destino_fisico(session, devolucao_id, novo=novo_destino)

    return d
