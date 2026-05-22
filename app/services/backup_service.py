import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import Config


@dataclass
class InfoBackup:
    caminho: Path
    criado_em: datetime
    tamanho_bytes: int


def _proxima_pasta(cfg: Config) -> Path:
    cfg.backup_folder.mkdir(parents=True, exist_ok=True)
    return cfg.backup_folder


def criar_backup() -> Path:
    """Cria um .zip com dados.db, anexos/ e config.json. Retorna o caminho."""
    cfg = Config.load()
    destino_dir = _proxima_pasta(cfg)
    # Windows tem resolucao de relogio grosseira (~15ms) — datetime.now() pode
    # repetir em loop apertado. Usa contador suffix se o arquivo ja existir.
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    destino = destino_dir / f"{timestamp}_backup.zip"
    counter = 1
    while destino.exists():
        destino = destino_dir / f"{timestamp}_{counter}_backup.zip"
        counter += 1

    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        if cfg.db_path.exists():
            zf.write(cfg.db_path, arcname="dados.db")
        if cfg.config_file.exists():
            zf.write(cfg.config_file, arcname="config.json")
        if cfg.anexos_dir.exists():
            for arquivo in cfg.anexos_dir.rglob("*"):
                if arquivo.is_file():
                    arcname = arquivo.relative_to(cfg.data_dir).as_posix()
                    zf.write(arquivo, arcname=arcname)

    _rotacionar(cfg)
    return destino


def _rotacionar(cfg: Config) -> None:
    zips = sorted(cfg.backup_folder.glob("*.zip"))
    excedente = len(zips) - cfg.backup_retention
    if excedente > 0:
        for antigo in zips[:excedente]:
            antigo.unlink(missing_ok=True)


def listar_backups() -> list[InfoBackup]:
    cfg = Config.load()
    if not cfg.backup_folder.exists():
        return []
    infos = []
    for z in cfg.backup_folder.glob("*.zip"):
        st = z.stat()
        infos.append(InfoBackup(
            caminho=z,
            criado_em=datetime.fromtimestamp(st.st_mtime),
            tamanho_bytes=st.st_size,
        ))
    return sorted(infos, key=lambda x: x.criado_em, reverse=True)


def ultimo_backup() -> Optional[InfoBackup]:
    backups = listar_backups()
    return backups[0] if backups else None
