from datetime import date

import pytest

from app.constants import DestinoFisico, FormaRessarcimento, StatusProcesso
from app.repositories import devolucoes_repo, marcas_repo


@pytest.fixture
def marca(session):
    m = marcas_repo.criar(session, nome="Vizzano")
    session.flush()
    return m


def test_criar_devolucao_com_defaults(session, marca):
    d = devolucoes_repo.criar(
        session, marca_id=marca.id, produto_modelo="Sandália X",
        data_devolucao=date(2026, 5, 12),
    )
    session.flush()
    assert d.id is not None
    assert d.status_processo == StatusProcesso.DEFEITO_IDENTIFICADO
    assert d.destino_fisico == DestinoFisico.NA_LOJA
    assert d.quantidade == 1
    assert d.excluido_em is None


def test_listar_exclui_da_lixeira(session, marca):
    d1 = devolucoes_repo.criar(session, marca_id=marca.id,
                                produto_modelo="A", data_devolucao=date(2026, 5, 1))
    d2 = devolucoes_repo.criar(session, marca_id=marca.id,
                                produto_modelo="B", data_devolucao=date(2026, 5, 2))
    session.flush()
    devolucoes_repo.marcar_como_excluida(session, d1.id)
    session.flush()

    ativas = devolucoes_repo.listar_ativas(session)
    assert [d.id for d in ativas] == [d2.id]

    lixeira = devolucoes_repo.listar_lixeira(session)
    assert [d.id for d in lixeira] == [d1.id]


def test_filtrar_por_status_e_marca(session, marca):
    outra = marcas_repo.criar(session, nome="Olympikus")
    session.flush()
    d1 = devolucoes_repo.criar(session, marca_id=marca.id, produto_modelo="A",
                                data_devolucao=date(2026, 5, 1))
    d2 = devolucoes_repo.criar(session, marca_id=outra.id, produto_modelo="B",
                                data_devolucao=date(2026, 5, 2))
    d2.status_processo = StatusProcesso.RESSARCIDO
    session.flush()

    so_vizzano = devolucoes_repo.listar_ativas(session, marca_id=marca.id)
    assert [d.id for d in so_vizzano] == [d1.id]

    so_ressarcidas = devolucoes_repo.listar_ativas(
        session, status=StatusProcesso.RESSARCIDO
    )
    assert [d.id for d in so_ressarcidas] == [d2.id]


def test_busca_textual(session, marca):
    devolucoes_repo.criar(session, marca_id=marca.id, produto_modelo="Sandália Salto",
                          data_devolucao=date(2026, 5, 1))
    devolucoes_repo.criar(session, marca_id=marca.id, produto_modelo="Bota",
                          data_devolucao=date(2026, 5, 2),
                          cliente_nome="Maria Santos")
    session.flush()

    r1 = devolucoes_repo.listar_ativas(session, busca="salto")
    assert len(r1) == 1
    r2 = devolucoes_repo.listar_ativas(session, busca="maria")
    assert len(r2) == 1
