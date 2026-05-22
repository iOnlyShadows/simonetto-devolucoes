from datetime import date
from pathlib import Path

import pytest
from PIL import Image

from app.constants import EXTENSOES_PERMITIDAS, TAMANHO_MAXIMO_BYTES
from app.repositories import anexos_repo, marcas_repo
from app.services import anexo_service, devolucao_service


@pytest.fixture
def devolucao(session):
    m = marcas_repo.criar(session, nome="Vizzano")
    session.flush()
    d = devolucao_service.criar(session, marca_id=m.id, produto_modelo="X",
                                 data_devolucao=date(2026, 5, 1))
    session.flush()
    return d


def _criar_imagem(path: Path, tamanho=(800, 600), color="red"):
    img = Image.new("RGB", tamanho, color=color)
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


def test_salvar_imagem_gera_thumbnail_automaticamente(
    session, devolucao, tmp_path, isolated_data_dir
):
    origem = tmp_path / "foto.jpg"
    _criar_imagem(origem)

    anexo = anexo_service.salvar_anexo(session, devolucao.id, origem)
    session.flush()
    assert anexo.tipo == "imagem"
    # Thumb fica em <pasta>/<id>_thumb.jpg
    thumb_path = isolated_data_dir / "anexos" / f"{devolucao.id:04d}" / f"{anexo.id}_thumb.jpg"
    assert thumb_path.exists()
    with Image.open(thumb_path) as img:
        assert max(img.size) <= 200


def test_thumb_url_inclui_cache_buster(session, devolucao, tmp_path):
    origem = tmp_path / "foto.jpg"
    _criar_imagem(origem)
    anexo = anexo_service.salvar_anexo(session, devolucao.id, origem)
    session.flush()
    url = anexo_service.thumb_url_de(anexo)
    assert url is not None
    assert url.startswith("/dados/")
    assert "?t=" in url
    # PDF não tem thumb URL
    pdf_anexo = anexo_service.salvar_anexo(session, devolucao.id, _make_pdf(tmp_path))
    session.flush()
    assert anexo_service.thumb_url_de(pdf_anexo) is None


def _make_pdf(tmp_path):
    p = tmp_path / "doc.pdf"
    p.write_bytes(b"%PDF-1.4\nfake\n")
    return p


def test_ordem_incrementa_para_cada_novo_anexo(session, devolucao, tmp_path):
    origens = [tmp_path / f"foto{i}.jpg" for i in range(3)]
    for o in origens:
        _criar_imagem(o)
    anexos = [anexo_service.salvar_anexo(session, devolucao.id, o) for o in origens]
    session.flush()
    assert [a.ordem for a in anexos] == [0, 1, 2]


def test_mover_para_cima_troca_ordens(session, devolucao, tmp_path):
    origens = [tmp_path / f"foto{i}.jpg" for i in range(3)]
    for o in origens:
        _criar_imagem(o)
    anexos = [anexo_service.salvar_anexo(session, devolucao.id, o) for o in origens]
    session.flush()
    # Move o segundo pra cima
    assert anexo_service.mover_para_cima(session, anexos[1].id) is True
    session.flush()
    ordenados = anexos_repo.listar_imagens(session, devolucao.id)
    assert [a.id for a in ordenados] == [anexos[1].id, anexos[0].id, anexos[2].id]


def test_mover_para_cima_no_topo_eh_noop(session, devolucao, tmp_path):
    origem = tmp_path / "foto.jpg"
    _criar_imagem(origem)
    anexo = anexo_service.salvar_anexo(session, devolucao.id, origem)
    session.flush()
    assert anexo_service.mover_para_cima(session, anexo.id) is False


def test_mover_para_baixo_troca_ordens(session, devolucao, tmp_path):
    origens = [tmp_path / f"foto{i}.jpg" for i in range(3)]
    for o in origens:
        _criar_imagem(o)
    anexos = [anexo_service.salvar_anexo(session, devolucao.id, o) for o in origens]
    session.flush()
    assert anexo_service.mover_para_baixo(session, anexos[0].id) is True
    session.flush()
    ordenados = anexos_repo.listar_imagens(session, devolucao.id)
    assert [a.id for a in ordenados] == [anexos[1].id, anexos[0].id, anexos[2].id]


def test_definir_como_principal_move_para_o_topo(session, devolucao, tmp_path):
    origens = [tmp_path / f"foto{i}.jpg" for i in range(3)]
    for o in origens:
        _criar_imagem(o)
    anexos = [anexo_service.salvar_anexo(session, devolucao.id, o) for o in origens]
    session.flush()
    # O terceiro (índice 2) vira principal
    assert anexo_service.definir_como_principal(session, anexos[2].id) is True
    session.flush()
    ordenados = anexos_repo.listar_imagens(session, devolucao.id)
    assert ordenados[0].id == anexos[2].id


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


def test_remover_anexo_apaga_arquivo_e_thumb(session, devolucao, tmp_path, isolated_data_dir):
    origem = tmp_path / "foto.jpg"
    _criar_imagem(origem)
    anexo = anexo_service.salvar_anexo(session, devolucao.id, origem)
    session.flush()
    caminho = isolated_data_dir / anexo.caminho_interno
    thumb = isolated_data_dir / "anexos" / f"{devolucao.id:04d}" / f"{anexo.id}_thumb.jpg"
    assert caminho.exists() and thumb.exists()

    anexo_service.remover_anexo(session, anexo.id)
    session.flush()
    assert not caminho.exists()
    assert not thumb.exists()
