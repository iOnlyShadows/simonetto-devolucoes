import shutil
from pathlib import Path
from typing import Optional

from PIL import Image
from sqlalchemy.orm import Session

from app.config import Config
from app.constants import EXTENSOES_PERMITIDAS, TAMANHO_MAXIMO_BYTES
from app.models.anexo import Anexo
from app.repositories import anexos_repo

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


def _thumb_path_de(anexo: Anexo) -> Path:
    """Caminho absoluto do thumbnail de um anexo de imagem."""
    cfg = Config.load()
    pasta = cfg.anexos_dir / f"{anexo.devolucao_id:04d}"
    return pasta / f"{anexo.id}_thumb.jpg"


def thumb_url_de(anexo: Anexo) -> Optional[str]:
    """URL do thumbnail (relativa a /dados), com cache-buster por id+criado_em.
    Se o thumb ainda não existir (ex: anexo antigo), tenta gerar lazy.
    Retorna None se o anexo não for imagem ou o arquivo original sumiu."""
    if anexo.tipo != "imagem":
        return None
    thumb = _thumb_path_de(anexo)
    if not thumb.exists():
        # Lazy generation pra anexos pré-refatoração ou casos em que o thumb foi deletado
        cfg = Config.load()
        origem = cfg.data_dir / anexo.caminho_interno
        if not origem.exists():
            return None
        try:
            _gerar_thumbnail(origem, thumb)
        except Exception:
            return None
    cfg = Config.load()
    rel = thumb.relative_to(cfg.anexos_dir).as_posix()
    cb = int(anexo.criado_em.timestamp()) if anexo.criado_em else 0
    return f"/dados/{rel}?t={cb}_{anexo.id}"


def url_publica(caminho_interno: str) -> str:
    """URL HTTP de um anexo original (a rota /dados serve a pasta de anexos).

    `caminho_interno` é relativo à pasta de dados e começa com 'anexos/'.
    """
    rel = Path(caminho_interno)
    try:
        rel = rel.relative_to("anexos")
    except ValueError:
        pass
    return f"/dados/{rel.as_posix()}"


def salvar_anexo(session: Session, devolucao_id: int, origem: Path) -> Anexo:
    """Salva um anexo. Se for imagem, gera thumb automaticamente.
    O `ordem` é o próximo disponível (vai pro final da galeria)."""
    origem = Path(origem)
    _validar(origem)

    pasta = _pasta_da_devolucao(devolucao_id)
    destino = pasta / origem.name
    # Evita sobrescrita
    counter = 1
    while destino.exists():
        destino = pasta / f"{origem.stem}_{counter}{origem.suffix}"
        counter += 1
    shutil.copy2(origem, destino)

    cfg = Config.load()
    caminho_rel = destino.relative_to(cfg.data_dir).as_posix()

    ordem_proxima = anexos_repo.proxima_ordem(session, devolucao_id)
    anexo = anexos_repo.criar(
        session,
        devolucao_id=devolucao_id,
        nome_original=origem.name,
        caminho_interno=caminho_rel,
        tipo=_tipo_de(origem.suffix.lower()),
        tamanho_bytes=destino.stat().st_size,
        ordem=ordem_proxima,
    )
    session.flush()  # garante id pro nome do thumb

    if anexo.tipo == "imagem":
        _gerar_thumbnail(destino, _thumb_path_de(anexo))

    return anexo


def remover_anexo(session: Session, anexo_id: int) -> bool:
    anexo = anexos_repo.buscar_por_id(session, anexo_id)
    if anexo is None:
        return False

    cfg = Config.load()
    caminho_abs = cfg.data_dir / anexo.caminho_interno
    if caminho_abs.exists():
        caminho_abs.unlink()

    # Apaga thumb também se for imagem
    if anexo.tipo == "imagem":
        thumb = _thumb_path_de(anexo)
        if thumb.exists():
            thumb.unlink()

    anexos_repo.excluir(session, anexo_id)
    _reindexar_ordem(session, anexo.devolucao_id)
    return True


def _reindexar_ordem(session: Session, devolucao_id: int) -> None:
    """Reordena 0,1,2,... preservando a ordem relativa atual."""
    anexos = anexos_repo.listar_por_devolucao(session, devolucao_id)
    for i, a in enumerate(anexos):
        a.ordem = i


def mover_para_cima(session: Session, anexo_id: int) -> bool:
    """Troca de posição com o anexo anterior (entre os do mesmo tipo)."""
    anexo = anexos_repo.buscar_por_id(session, anexo_id)
    if anexo is None:
        return False
    irmaos = [a for a in anexos_repo.listar_por_devolucao(session, anexo.devolucao_id)
              if a.tipo == anexo.tipo]
    idx = next((i for i, a in enumerate(irmaos) if a.id == anexo_id), -1)
    if idx <= 0:
        return False
    anterior = irmaos[idx - 1]
    anexo.ordem, anterior.ordem = anterior.ordem, anexo.ordem
    return True


def mover_para_baixo(session: Session, anexo_id: int) -> bool:
    """Troca de posição com o anexo seguinte (entre os do mesmo tipo)."""
    anexo = anexos_repo.buscar_por_id(session, anexo_id)
    if anexo is None:
        return False
    irmaos = [a for a in anexos_repo.listar_por_devolucao(session, anexo.devolucao_id)
              if a.tipo == anexo.tipo]
    idx = next((i for i, a in enumerate(irmaos) if a.id == anexo_id), -1)
    if idx < 0 or idx >= len(irmaos) - 1:
        return False
    seguinte = irmaos[idx + 1]
    anexo.ordem, seguinte.ordem = seguinte.ordem, anexo.ordem
    return True


def definir_como_principal(session: Session, anexo_id: int) -> bool:
    """Move o anexo pro topo do seu tipo (ordem mínima entre os do mesmo tipo)."""
    anexo = anexos_repo.buscar_por_id(session, anexo_id)
    if anexo is None or anexo.tipo != "imagem":
        return False
    imagens = anexos_repo.listar_imagens(session, anexo.devolucao_id)
    if not imagens or imagens[0].id == anexo_id:
        return True  # já é o primeiro
    # Define o anexo escolhido como ordem do atual primeiro - 1 (ou apenas reordena tudo)
    # Estratégia simples: reordena explicitamente colocando o escolhido na frente
    nova_ordem_imagens = [anexo] + [a for a in imagens if a.id != anexo_id]
    # Pega ordens originais das imagens (em ordem), redistribui
    ordens_originais = sorted(a.ordem for a in imagens)
    for img, nova_ordem in zip(nova_ordem_imagens, ordens_originais):
        img.ordem = nova_ordem
    return True


def caminho_absoluto(anexo: Anexo) -> Path:
    return Config.load().data_dir / anexo.caminho_interno
