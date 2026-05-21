from sqlalchemy import inspect

from app.db import get_engine


def test_todas_as_tabelas_existem(session):
    insp = inspect(session.get_bind())
    tabelas = set(insp.get_table_names())
    assert {"marcas", "devolucoes", "anexos", "historico_status"} <= tabelas
