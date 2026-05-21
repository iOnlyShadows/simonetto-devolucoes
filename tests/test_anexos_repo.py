from datetime import date

import pytest

from app.repositories import anexos_repo, devolucoes_repo, historico_repo, marcas_repo


@pytest.fixture
def devolucao(session):
    m = marcas_repo.criar(session, nome="Vizzano")
    session.flush()
    d = devolucoes_repo.criar(session, marca_id=m.id, produto_modelo="X",
                               data_devolucao=date(2026, 5, 1))
    session.flush()
    return d


def test_criar_e_listar_anexo(session, devolucao):
    anexos_repo.criar(session, devolucao_id=devolucao.id,
                      nome_original="nota.pdf",
                      caminho_interno=f"anexos/{devolucao.id:04d}/nota.pdf",
                      tipo="pdf", tamanho_bytes=1024)
    session.flush()
    listados = anexos_repo.listar_por_devolucao(session, devolucao.id)
    assert len(listados) == 1
    assert listados[0].nome_original == "nota.pdf"


def test_historico_registra_e_lista(session, devolucao):
    historico_repo.registrar(session, devolucao_id=devolucao.id,
                              campo="status_processo",
                              valor_anterior=None, valor_novo="defeito_identificado")
    historico_repo.registrar(session, devolucao_id=devolucao.id,
                              campo="status_processo",
                              valor_anterior="defeito_identificado",
                              valor_novo="sinalizado",
                              observacao="mandei foto pro rep")
    session.flush()
    h = historico_repo.listar_por_devolucao(session, devolucao.id)
    assert len(h) == 2
    assert h[1].observacao == "mandei foto pro rep"
