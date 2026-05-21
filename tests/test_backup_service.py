import zipfile
from datetime import datetime
from pathlib import Path

import pytest

from app.config import Config
from app.services import backup_service


def test_criar_backup_gera_zip(isolated_data_dir):
    # Cria conteúdo falso na pasta de dados
    (isolated_data_dir / "dados.db").write_bytes(b"db fake")
    (isolated_data_dir / "anexos" / "0001").mkdir(parents=True)
    (isolated_data_dir / "anexos" / "0001" / "x.pdf").write_bytes(b"pdf")

    cfg = Config.load()
    cfg.backup_folder = isolated_data_dir / "backups"
    cfg.save()

    caminho = backup_service.criar_backup()
    assert caminho.exists()
    assert caminho.suffix == ".zip"

    with zipfile.ZipFile(caminho) as zf:
        nomes = zf.namelist()
    assert "dados.db" in nomes
    assert any(n.startswith("anexos/0001/") for n in nomes)


def test_rotacao_mantem_apenas_n_mais_recentes(isolated_data_dir):
    (isolated_data_dir / "dados.db").write_bytes(b"db")
    cfg = Config.load()
    cfg.backup_folder = isolated_data_dir / "backups"
    cfg.backup_retention = 3
    cfg.save()

    for _ in range(5):
        backup_service.criar_backup()

    zips = sorted((isolated_data_dir / "backups").glob("*.zip"))
    assert len(zips) == 3


def test_ultimo_backup_retorna_data_correta(isolated_data_dir):
    cfg = Config.load()
    cfg.backup_folder = isolated_data_dir / "backups"
    cfg.save()
    assert backup_service.ultimo_backup() is None

    (isolated_data_dir / "dados.db").write_bytes(b"db")
    caminho = backup_service.criar_backup()
    info = backup_service.ultimo_backup()
    assert info is not None
    assert info.caminho == caminho
