import shutil
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import Config
from app.constants import LIXEIRA_DIAS
from app.repositories import devolucoes_repo


def enviar_para_lixeira(session: Session, devolucao_id: int) -> bool:
    return devolucoes_repo.marcar_como_excluida(session, devolucao_id)


def restaurar(session: Session, devolucao_id: int) -> bool:
    return devolucoes_repo.restaurar(session, devolucao_id)


def expurgar_antigas(session: Session) -> list[int]:
    """Apaga DEFINITIVAMENTE devoluções excluídas há mais de LIXEIRA_DIAS dias.
    Remove também a pasta de anexos do disco."""
    limite = datetime.utcnow() - timedelta(days=LIXEIRA_DIAS)
    cfg = Config.load()
    antigas = devolucoes_repo.listar_lixeira(session)
    ids_apagados: list[int] = []
    for d in antigas:
        if d.excluido_em is not None and d.excluido_em < limite:
            pasta = cfg.anexos_dir / f"{d.id:04d}"
            if pasta.exists():
                shutil.rmtree(pasta, ignore_errors=True)
            devolucoes_repo.excluir_definitivo(session, d.id)
            ids_apagados.append(d.id)
    return ids_apagados
