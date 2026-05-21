import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import db as db_module
from app.models.base import Base


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Cada teste roda com SIMONETTO_DATA_DIR isolado."""
    monkeypatch.setenv("SIMONETTO_DATA_DIR", str(tmp_path))
    yield tmp_path


@pytest.fixture
def session(monkeypatch):
    """Sessão SQLAlchemy em SQLite em memória, isolada por teste."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    monkeypatch.setattr(db_module, "_engine", engine)
    monkeypatch.setattr(db_module, "_SessionLocal", SessionLocal)

    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
