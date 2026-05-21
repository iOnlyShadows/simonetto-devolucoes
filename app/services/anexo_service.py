import shutil
from pathlib import Path
from typing import Optional

from PIL import Image
from sqlalchemy.orm import Session

from app.config import Config
from app.constants import EXTENSOES_PERMITIDAS, TAMANHO_MAXIMO_BYTES
from app.models.anexo import Anexo
from app.repositories import anexos_repo, devolucoes_repo

_TIPOS_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}


def _tipo_de(ext: str) -> str:
    if ext == ".pdf":
        return "pdf"
    if ext in _TIPOS_IMAGEM:
        return "imagem"
    return "outro"


def _pasta_da_devolucao(devolucao_id: int) -> Path:
    cfg = Config.load()
    pasta = cfg.anexos_dir / f"{devolucao_id:04d}"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _validar(origem: Path) -> None:
    if not origem.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {origem}")
    ext = origem.suffix.lower()
    if ext not in EXTENSOES_PERMITIDAS:
        raise ValueError(f"Extensão não permitida: {ext}")
    if origem.stat().st_size > TAMANHO_MAXIMO_BYTES:
        raise ValueError(f"Tamanho máximo excedido (limite {TAMANHO_MAXIMO_BYTES} bytes)")


def _gerar_thumbnail(origem_imagem: Path, destino: Path, max_dim: int = 200) -> None:
    with Image.open(origem_imagem) as img:
        img.thumbnail((max_dim, max_dim))
        img.convert("RGB").save(destino, "JPEG", quality=85)


def salvar_anexo(session: Session, devolucao_id: int, origem: Path,
                  *, como_principal: bool = False) -> Anexo:
    origem = Path(origem)
    _validar(origem)

    pasta = _pasta_da_devolucao(devolucao_id)
    destino = pasta / origem.name
    # Evita sobrescrita: se já existe, adiciona sufixo (_1, _2…)
    counter = 1
    while destino.exists():
        destino = pasta / f"{origem.stem}_{counter}{origem.suffix}"
        counter += 1
    shutil.copy2(origem, destino)

    cfg = Config.load()
    caminho_rel = destino.relative_to(cfg.data_dir).as_posix()

    anexo = anexos_repo.criar(
        session,
        devolucao_id=devolucao_id,
        nome_original=origem.name,
        caminho_interno=caminho_rel,
        tipo=_tipo_de(origem.suffix.lower()),
        tamanho_bytes=destino.stat().st_size,
    )

    if como_principal and anexo.tipo == "imagem":
        thumb_path = pasta / "thumb.jpg"
        _gerar_thumbnail(destino, thumb_path)
        d = devolucoes_repo.buscar_por_id(session, devolucao_id)
        if d:
            d.foto_principal_caminho = thumb_path.relative_to(cfg.data_dir).as_posix()

    return anexo


def remover_anexo(session: Session, anexo_id: int) -> bool:
    anexo = anexos_repo.buscar_por_id(session, anexo_id)
    if anexo is None:
        return False

    cfg = Config.load()
    caminho_abs = cfg.data_dir / anexo.caminho_interno
    if caminho_abs.exists():
        caminho_abs.unlink()

    anexos_repo.excluir(session, anexo_id)
    return True


def caminho_absoluto(anexo: Anexo) -> Path:
    return Config.load().data_dir / anexo.caminho_interno
