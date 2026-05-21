from datetime import date
from pathlib import Path

import pytest
from PIL import Image

from app.constants import EXTENSOES_PERMITIDAS, TAMANHO_MAXIMO_BYTES
from app.repositories import marcas_repo
from app.services import anexo_service, devolucao_service


@pytest.fixture
def devolucao(session):
    m = marcas_repo.criar(session, nome="Vizzano")
    session.flush()
    d = devolucao_service.criar(session, marca_id=m.id, produto_modelo="X",
                                 data_devolucao=date(2026, 5, 1))
    session.flush()
    return d


def _criar_imagem(path: Path, tamanho=(800, 600)):
    img = Image.new("RGB", tamanho, color="red")
    img.save(path, "JPEG")


def test_salvar_anexo_pdf(session, devolucao, tmp_path, isolated_data_dir):
    origem = tmp_path / "nota.pdf"
    origem.write_bytes(b"%PDF-1.4\nfake pdf\n")

    anexo = anexo_service.salvar_anexo(session, devolucao.id, origem)
    session.flush()
    assert anexo.tipo == "pdf"
    assert anexo.nome_original == "nota.pdf"
    destino = isolated_data_dir / anexo.caminho_interno
    assert destino.exists()


def test_salvar_imagem_gera_thumbnail_se_for_principal(
    session, devolucao, tmp_path, isolated_data_dir
):
    origem = tmp_path / "foto.jpg"
    _criar_imagem(origem)

    anexo = anexo_service.salvar_anexo(
        session, devolucao.id, origem, como_principal=True
    )
    session.flush()
    assert devolucao.foto_principal_caminho is not None
    thumb_path = isolated_data_dir / devolucao.foto_principal_caminho
    assert thumb_path.exists()
    with Image.open(thumb_path) as img:
        assert max(img.size) <= 200


def test_rejeita_extensao_invalida(session, devolucao, tmp_path):
    origem = tmp_path / "planilha.xlsx"
    origem.write_bytes(b"x" * 100)
    with pytest.raises(ValueError, match="Extensão não permitida"):
        anexo_service.salvar_anexo(session, devolucao.id, origem)


def test_rejeita_tamanho_excessivo(session, devolucao, tmp_path):
    origem = tmp_path / "grande.pdf"
    origem.write_bytes(b"x" * (TAMANHO_MAXIMO_BYTES + 1))
    with pytest.raises(ValueError, match="Tamanho máximo"):
        anexo_service.salvar_anexo(session, devolucao.id, origem)


def test_remover_anexo_apaga_arquivo(session, devolucao, tmp_path, isolated_data_dir):
    origem = tmp_path / "foto.jpg"
    _criar_imagem(origem)
    anexo = anexo_service.salvar_anexo(session, devolucao.id, origem)
    session.flush()
    caminho = isolated_data_dir / anexo.caminho_interno
    assert caminho.exists()

    anexo_service.remover_anexo(session, anexo.id)
    session.flush()
    assert not caminho.exists()
