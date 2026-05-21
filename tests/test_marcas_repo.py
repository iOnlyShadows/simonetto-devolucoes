import pytest

from app.constants import FormaRessarcimento
from app.models.marca import Marca
from app.repositories import marcas_repo


def test_criar_e_buscar_marca(session):
    marca = marcas_repo.criar(session, nome="Vizzano",
                               forma_padrao=FormaRessarcimento.ABATE_NOTA,
                               observacoes="Rep: João")
    session.flush()
    assert marca.id is not None

    encontrada = marcas_repo.buscar_por_id(session, marca.id)
    assert encontrada is not None
    assert encontrada.nome == "Vizzano"
    assert encontrada.forma_ressarcimento_padrao == FormaRessarcimento.ABATE_NOTA


def test_nome_unico(session):
    marcas_repo.criar(session, nome="Vizzano")
    session.flush()
    with pytest.raises(Exception):
        marcas_repo.criar(session, nome="Vizzano")
        session.flush()


def test_listar_ordenado_por_nome(session):
    marcas_repo.criar(session, nome="Olympikus")
    marcas_repo.criar(session, nome="Vizzano")
    marcas_repo.criar(session, nome="Adidas")
    session.flush()
    nomes = [m.nome for m in marcas_repo.listar(session)]
    assert nomes == ["Adidas", "Olympikus", "Vizzano"]


def test_atualizar_e_excluir(session):
    marca = marcas_repo.criar(session, nome="Teste")
    session.flush()
    marcas_repo.atualizar(session, marca.id, observacoes="nova obs")
    session.flush()
    assert marcas_repo.buscar_por_id(session, marca.id).observacoes == "nova obs"

    marcas_repo.excluir(session, marca.id)
    session.flush()
    assert marcas_repo.buscar_por_id(session, marca.id) is None
