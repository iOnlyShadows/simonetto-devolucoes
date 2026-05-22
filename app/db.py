from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Config
from app.models.base import Base

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def init_engine(database_url: Optional[str] = None) -> Engine:
    """Cria o engine. Em testes, passe 'sqlite:///:memory:'."""
    global _engine, _SessionLocal
    if database_url is None:
        cfg = Config.load()
        database_url = f"sqlite:///{cfg.db_path}"

    _engine = create_engine(database_url, echo=False, future=True)

    # Habilita foreign keys no SQLite
    @event.listens_for(_engine, "connect")
    def _enable_fk(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    Base.metadata.create_all(_engine)
    _aplicar_migracoes(_engine)
    return _engine


def _aplicar_migracoes(engine: Engine) -> None:
    """Migrações idempotentes manuais para SQLite (sem alembic)."""
    with engine.begin() as conn:
        # 1) anexos.ordem — adicionado quando introduzimos galeria reordenável
        cols_anexos = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(anexos)")}
        if "ordem" not in cols_anexos:
            conn.exec_driver_sql(
                "ALTER TABLE anexos ADD COLUMN ordem INTEGER NOT NULL DEFAULT 0"
            )


def get_engine() -> Engine:
    if _engine is None:
        init_engine()
    return _engine  # type: ignore


@contextmanager
def session_scope() -> Iterator[Session]:
    """Contexto transacional. Commit no sucesso, rollback no erro."""
    if _SessionLocal is None:
        init_engine()
    session = _SessionLocal()  # type: ignore
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
