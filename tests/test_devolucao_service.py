from datetime import date

import pytest

from app.constants import DestinoFisico, FormaRessarcimento, StatusProcesso
from app.repositories import historico_repo, marcas_repo
from app.services import devolucao_service


@pytest.fixture
def marca(session):
    m = marcas_repo.criar(session, nome="Vizzano",
                          forma_padrao=FormaRessarcimento.ABATE_NOTA)
    session.flush()
    return m


def test_criar_registra_historico_inicial(session, marca):
    d = devolucao_service.criar(session, marca_id=marca.id,
                                 produto_modelo="X",
                                 data_devolucao=date(2026, 5, 1))
    session.flush()
    h = historico_repo.listar_por_devolucao(session, d.id)
    # Espera 2 registros: status inicial + destino inicial
    campos = {(x.campo, x.valor_novo) for x in h}
    assert ("status_processo", "defeito_identificado") in campos
    assert ("destino_fisico", "na_loja") in campos


def test_criar_aplica_forma_padrao_da_marca(session, marca):
    d = devolucao_service.criar(session, marca_id=marca.id,
                                 produto_modelo="X",
                                 data_devolucao=date(2026, 5, 1))
    session.flush()
    assert d.forma_ressarcimento == FormaRessarcimento.ABATE_NOTA


def test_mudar_status_processo_registra_historico(session, marca):
    d = devolucao_service.criar(session, marca_id=marca.id,
                                 produto_modelo="X",
                                 data_devolucao=date(2026, 5, 1))
    session.flush()

    devolucao_service.mudar_status_processo(
        session, d.id, novo=StatusProcesso.SINALIZADO,
        observacao="mandei foto"
    )
    session.flush()

    h = historico_repo.listar_por_devolucao(session, d.id)
    transicoes_status = [x for x in h if x.campo == "status_processo"]
    assert len(transicoes_status) == 2
    assert transicoes_status[-1].valor_anterior == "defeito_identificado"
    assert transicoes_status[-1].valor_novo == "sinalizado"
    assert transicoes_status[-1].observacao == "mandei foto"


def test_mudar_status_mesmo_valor_nao_registra(session, marca):
    d = devolucao_service.criar(session, marca_id=marca.id,
                                 produto_modelo="X",
                                 data_devolucao=date(2026, 5, 1))
    session.flush()
    devolucao_service.mudar_status_processo(
        session, d.id, novo=StatusProcesso.DEFEITO_IDENTIFICADO
    )
    session.flush()
    h = [x for x in historico_repo.listar_por_devolucao(session, d.id)
         if x.campo == "status_processo"]
    assert len(h) == 1  # só o inicial


def test_atualizar_campos_simples(session, marca):
    d = devolucao_service.criar(session, marca_id=marca.id,
                                 produto_modelo="X",
                                 data_devolucao=date(2026, 5, 1))
    session.flush()
    devolucao_service.atualizar(session, d.id,
                                 produto_modelo="X melhorado",
                                 valor_custo=89.90,
                                 cliente_nome="João")
    session.flush()
    d2 = devolucao_service.buscar(session, d.id)
    assert d2.produto_modelo == "X melhorado"
    assert float(d2.valor_custo) == 89.90
    assert d2.cliente_nome == "João"


def test_atualizar_via_geral_tambem_registra_historico_de_status(session, marca):
    """Se o usuário editar via form (que envia tudo), mudanças nos eixos
    1 e 2 devem virar histórico mesmo passando por atualizar()."""
    d = devolucao_service.criar(session, marca_id=marca.id,
                                 produto_modelo="X",
                                 data_devolucao=date(2026, 5, 1))
    session.flush()
    devolucao_service.atualizar(
        session, d.id,
        status_processo=StatusProcesso.RESSARCIDO,
        destino_fisico=DestinoFisico.RECOLHIDO,
    )
    session.flush()
    h = historico_repo.listar_por_devolucao(session, d.id)
    novos = {(x.campo, x.valor_novo) for x in h
             if x.valor_anterior is not None}
    assert ("status_processo", "ressarcido") in novos
    assert ("destino_fisico", "recolhido") in novos
