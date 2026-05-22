from datetime import date, datetime, timedelta

import pytest
from PIL import Image

from app.repositories import devolucoes_repo, marcas_repo
from app.services import anexo_service, lixeira_service, devolucao_service


@pytest.fixture
def devolucao(session):
    m = marcas_repo.criar(session, nome="Vizzano")
    session.flush()
    d = devolucao_service.criar(session, marca_id=m.id, produto_modelo="X",
                                 data_devolucao=date(2026, 5, 1))
    session.flush()
    return d


def test_enviar_para_lixeira_e_restaurar(session, devolucao):
    lixeira_service.enviar_para_lixeira(session, devolucao.id)
    session.flush()
    assert devolucao.excluido_em is not None
    assert devolucoes_repo.buscar_por_id(session, devolucao.id) is not None  # ainda existe

    lixeira_service.restaurar(session, devolucao.id)
    session.flush()
    assert devolucao.excluido_em is None


def test_purga_apaga_apenas_antigas(session, devolucao):
    # Marca como excluída há 40 dias
    devolucao.excluido_em = datetime.utcnow() - timedelta(days=40)
    session.flush()

    apagadas = lixeira_service.expurgar_antigas(session)
    session.flush()
    assert devolucao.id in apagadas
    assert devolucoes_repo.buscar_por_id(session, devolucao.id) is None


def test_purga_nao_apaga_recentes(session, devolucao):
    devolucao.excluido_em = datetime.utcnow() - timedelta(days=10)
    session.flush()
    apagadas = lixeira_service.expurgar_antigas(session)
    assert apagadas == []
    assert devolucoes_repo.buscar_por_id(session, devolucao.id) is not None


def test_expurgo_remove_arquivos_de_anexos(session, devolucao, tmp_path,
                                            isolated_data_dir):
    img = tmp_path / "foto.jpg"
    Image.new("RGB", (10, 10)).save(img, "JPEG")
    anexo = anexo_service.salvar_anexo(session, devolucao.id, img)
    session.flush()
    pasta_devolucao = (isolated_data_dir / "anexos" / f"{devolucao.id:04d}")
    assert pasta_devolucao.exists()

    devolucao.excluido_em = datetime.utcnow() - timedelta(days=40)
    session.flush()
    lixeira_service.expurgar_antigas(session)
    session.flush()
    assert not pasta_devolucao.exists()
