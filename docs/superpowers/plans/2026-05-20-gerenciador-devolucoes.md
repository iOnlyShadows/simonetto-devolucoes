# Gerenciador de Devoluções — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir um app desktop Python (NiceGUI + SQLite) para gerenciar devoluções de produtos da Loja Simonetto, com 3 eixos de status independentes, anexos, backup automático e lixeira soft-delete.

**Architecture:** Arquitetura em camadas — `ui → services → repositories → db`. UI nunca acessa banco direto. Banco SQLite via SQLAlchemy ORM. Dados em `%LOCALAPPDATA%\SimonettoDevolucoes\`. TDD nos services (onde estão as regras); repositories ganham testes básicos de CRUD; UI sem testes automatizados.

**Tech Stack:** Python 3.11+, `uv` (gerenciador de pacotes), NiceGUI (UI), SQLAlchemy (ORM), Pillow (thumbnails), Pydantic (validação), pytest (testes).

**Spec de referência:** `docs/superpowers/specs/2026-05-20-gerenciador-devolucoes-design.md`

---

## Mapa de Arquivos

Estrutura final esperada do projeto:

```
simonetto_devolucoes/
├── pyproject.toml
├── README.md
├── .gitignore
├── main.py                          # entry point
├── app/
│   ├── __init__.py
│   ├── config.py                    # paths, leitura/escrita do config.json
│   ├── constants.py                 # enums + cores
│   ├── db.py                        # engine + Session factory
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                  # Base declarativa
│   │   ├── marca.py
│   │   ├── devolucao.py
│   │   ├── anexo.py
│   │   └── historico.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── marcas_repo.py
│   │   ├── devolucoes_repo.py
│   │   ├── anexos_repo.py
│   │   └── historico_repo.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── devolucao_service.py
│   │   ├── anexo_service.py
│   │   ├── lixeira_service.py
│   │   └── backup_service.py
│   └── ui/
│       ├── __init__.py
│       ├── layout.py                # menu lateral, estrutura geral
│       ├── pages/
│       │   ├── __init__.py
│       │   ├── lista.py
│       │   ├── marcas.py
│       │   ├── lixeira.py
│       │   └── configuracoes.py
│       └── components/
│           ├── __init__.py
│           ├── badge_status.py
│           ├── form_devolucao.py
│           ├── detalhe_devolucao.py
│           └── upload_anexo.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # fixtures: engine em memória, paths temp
│   ├── test_marcas_repo.py
│   ├── test_devolucoes_repo.py
│   ├── test_anexos_repo.py
│   ├── test_devolucao_service.py
│   ├── test_anexo_service.py
│   ├── test_lixeira_service.py
│   └── test_backup_service.py
└── scripts/
    └── seed_demo.py
```

---

## FASE 1 — Fundação

### Task 1: Bootstrap do projeto

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `.python-version`
- Create: estrutura inicial de pastas (vazias com `__init__.py`)

- [x] **Step 1: Inicializar projeto com uv**

```bash
uv init --python 3.11 --no-readme
```

- [x] **Step 2: Substituir `pyproject.toml` pelo conteúdo abaixo**

```toml
[project]
name = "simonetto-devolucoes"
version = "0.1.0"
description = "Gerenciador de devoluções para a Loja Simonetto"
requires-python = ">=3.11"
dependencies = [
    "nicegui>=2.0",
    "sqlalchemy>=2.0",
    "pillow>=10.0",
    "pydantic>=2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]
```

- [x] **Step 3: Criar `.gitignore`**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
# dados de runtime ficam em AppData, mas se rodarmos com dev path local:
.dev_data/
```

- [x] **Step 4: Criar estrutura de pastas com __init__.py vazios**

```bash
mkdir -p app/models app/repositories app/services app/ui/pages app/ui/components tests scripts
touch app/__init__.py app/models/__init__.py app/repositories/__init__.py \
      app/services/__init__.py app/ui/__init__.py app/ui/pages/__init__.py \
      app/ui/components/__init__.py tests/__init__.py
```

- [x] **Step 5: Instalar dependências e validar**

```bash
uv sync
uv run python -c "import nicegui, sqlalchemy, PIL, pydantic; print('OK')"
```
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock .gitignore .python-version app/ tests/ scripts/
git commit -m "chore: bootstrap projeto com uv e dependencias principais"
```

---

### Task 2: Configuração de paths e config.json

**Files:**
- Create: `app/config.py`
- Create: `tests/test_config.py`

A `Config` resolve a pasta de dados (`%LOCALAPPDATA%\SimonettoDevolucoes\` por padrão, ou um path passado via variável de ambiente `SIMONETTO_DATA_DIR` — útil para testes).

- [ ] **Step 1: Escrever teste falhando em `tests/test_config.py`**

```python
import json
import os
from pathlib import Path

from app.config import Config


def test_config_uses_env_var_when_set(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMONETTO_DATA_DIR", str(tmp_path))
    cfg = Config.load()
    assert cfg.data_dir == tmp_path
    assert cfg.db_path == tmp_path / "dados.db"
    assert cfg.anexos_dir == tmp_path / "anexos"
    assert cfg.backups_dir == tmp_path / "backups"


def test_config_creates_dirs_if_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMONETTO_DATA_DIR", str(tmp_path))
    Config.load()
    assert (tmp_path / "anexos").is_dir()
    assert (tmp_path / "backups").is_dir()


def test_config_persists_preferences(tmp_path, monkeypatch):
    monkeypatch.setenv("SIMONETTO_DATA_DIR", str(tmp_path))
    cfg = Config.load()
    cfg.backup_folder = tmp_path / "custom_backups"
    cfg.backup_retention = 50
    cfg.save()

    reloaded = Config.load()
    assert reloaded.backup_folder == tmp_path / "custom_backups"
    assert reloaded.backup_retention == 50
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_config.py -v
```
Expected: FAIL (`ModuleNotFoundError: app.config`)

- [ ] **Step 3: Implementar `app/config.py`**

```python
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


def _default_data_dir() -> Path:
    env = os.environ.get("SIMONETTO_DATA_DIR")
    if env:
        return Path(env)
    local_appdata = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    return Path(local_appdata) / "SimonettoDevolucoes"


@dataclass
class Config:
    data_dir: Path
    backup_folder: Path
    backup_retention: int = 30
    backup_frequency: str = "on_close"  # on_close | daily | weekly | manual

    @property
    def db_path(self) -> Path:
        return self.data_dir / "dados.db"

    @property
    def anexos_dir(self) -> Path:
        return self.data_dir / "anexos"

    @property
    def backups_dir(self) -> Path:
        return self.data_dir / "backups"

    @property
    def config_file(self) -> Path:
        return self.data_dir / "config.json"

    @classmethod
    def load(cls) -> "Config":
        data_dir = _default_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "anexos").mkdir(exist_ok=True)
        (data_dir / "backups").mkdir(exist_ok=True)

        config_file = data_dir / "config.json"
        defaults = {
            "backup_folder": str(data_dir / "backups"),
            "backup_retention": 30,
            "backup_frequency": "on_close",
        }
        if config_file.exists():
            defaults.update(json.loads(config_file.read_text(encoding="utf-8")))

        return cls(
            data_dir=data_dir,
            backup_folder=Path(defaults["backup_folder"]),
            backup_retention=defaults["backup_retention"],
            backup_frequency=defaults["backup_frequency"],
        )

    def save(self) -> None:
        payload = {
            "backup_folder": str(self.backup_folder),
            "backup_retention": self.backup_retention,
            "backup_frequency": self.backup_frequency,
        }
        self.config_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
```

- [ ] **Step 4: Rodar e ver passar**

```bash
uv run pytest tests/test_config.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/config.py tests/test_config.py
git commit -m "feat(config): resolucao de paths + persistencia em config.json"
```

---

### Task 3: Constantes (enums e cores)

**Files:**
- Create: `app/constants.py`

Sem teste — é só constante. Erro de digitação aparece imediatamente nos testes que consomem.

- [ ] **Step 1: Escrever `app/constants.py`**

```python
from enum import Enum


class StatusProcesso(str, Enum):
    DEFEITO_IDENTIFICADO = "defeito_identificado"
    SINALIZADO = "sinalizado"
    PENDENTE_RESSARCIMENTO = "pendente_ressarcimento"
    RESSARCIDO = "ressarcido"


class DestinoFisico(str, Enum):
    NA_LOJA = "na_loja"
    RECOLHIDO = "recolhido"
    ENVIADO = "enviado"
    DESCARTADO = "descartado"


class FormaRessarcimento(str, Enum):
    ABATE_NOTA = "abate_nota"
    DINHEIRO = "dinheiro"
    TROCA = "troca"
    CREDITO = "credito"
    OUTRO = "outro"


STATUS_PROCESSO_LABELS = {
    StatusProcesso.DEFEITO_IDENTIFICADO: ("Defeito identificado", "red", "⚠️"),
    StatusProcesso.SINALIZADO: ("Sinalizado", "yellow", "📨"),
    StatusProcesso.PENDENTE_RESSARCIMENTO: ("Pendente ressarcimento", "orange", "⏳"),
    StatusProcesso.RESSARCIDO: ("Ressarcido", "green", "✅"),
}

DESTINO_FISICO_LABELS = {
    DestinoFisico.NA_LOJA: ("Na loja", "grey", "📦"),
    DestinoFisico.RECOLHIDO: ("Recolhido", "blue", "🛠️"),
    DestinoFisico.ENVIADO: ("Enviado", "purple", "📤"),
    DestinoFisico.DESCARTADO: ("Descartado", "black", "🗑️"),
}

FORMA_RESSARCIMENTO_LABELS = {
    FormaRessarcimento.ABATE_NOTA: ("Abate na nota", "💸"),
    FormaRessarcimento.DINHEIRO: ("Dinheiro", "💵"),
    FormaRessarcimento.TROCA: ("Troca", "🔄"),
    FormaRessarcimento.CREDITO: ("Crédito", "🎟️"),
    FormaRessarcimento.OUTRO: ("Outro", "❓"),
}

EXTENSOES_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
TAMANHO_MAXIMO_BYTES = 20 * 1024 * 1024  # 20 MB
LIXEIRA_DIAS = 30
BACKUP_RETENCAO_DEFAULT = 30
BANNER_BACKUP_ALERTA_DIAS = 7
```

- [ ] **Step 2: Sanity check**

```bash
uv run python -c "from app.constants import StatusProcesso; print(StatusProcesso.SINALIZADO.value)"
```
Expected: `sinalizado`

- [ ] **Step 3: Commit**

```bash
git add app/constants.py
git commit -m "feat(constants): enums dos 3 eixos + labels + limites"
```

---

### Task 4: Base do banco e engine

**Files:**
- Create: `app/db.py`, `app/models/base.py`

- [ ] **Step 1: Criar `app/models/base.py`**

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 2: Criar `app/db.py`**

```python
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Config
from app.models.base import Base

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def init_engine(database_url: Optional[str] = None) -> Engine:
    """Cria o engine. Em testes, passe 'sqlite:///:memory:'."""
    global _engine, _SessionLocal
    if database_url is None:
        cfg = Config.load()
        database_url = f"sqlite:///{cfg.db_path}"

    _engine = create_engine(database_url, echo=False, future=True)

    # Habilita foreign keys no SQLite
    @event.listens_for(_engine, "connect")
    def _enable_fk(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    Base.metadata.create_all(_engine)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        init_engine()
    return _engine  # type: ignore


@contextmanager
def session_scope() -> Iterator[Session]:
    """Contexto transacional. Commit no sucesso, rollback no erro."""
    if _SessionLocal is None:
        init_engine()
    session = _SessionLocal()  # type: ignore
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

- [ ] **Step 3: Criar `tests/conftest.py` com fixture compartilhada**

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import db as db_module
from app.models.base import Base


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Cada teste roda com SIMONETTO_DATA_DIR isolado."""
    monkeypatch.setenv("SIMONETTO_DATA_DIR", str(tmp_path))
    yield tmp_path


@pytest.fixture
def session(monkeypatch):
    """Sessão SQLAlchemy em SQLite em memória, isolada por teste."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    monkeypatch.setattr(db_module, "_engine", engine)
    monkeypatch.setattr(db_module, "_SessionLocal", SessionLocal)

    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
```

- [ ] **Step 4: Sanity check**

```bash
uv run pytest tests/ -v
```
Expected: testes anteriores (3 do Task 2) continuam passando

- [ ] **Step 5: Commit**

```bash
git add app/db.py app/models/base.py tests/conftest.py
git commit -m "feat(db): engine SQLAlchemy + session scope + fixture de testes"
```

---

## FASE 2 — Modelos e Repositórios

### Task 5: Modelo e repositório de Marca

**Files:**
- Create: `app/models/marca.py`, `app/repositories/marcas_repo.py`, `tests/test_marcas_repo.py`

- [ ] **Step 1: Escrever teste em `tests/test_marcas_repo.py`**

```python
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
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_marcas_repo.py -v
```
Expected: FAIL (módulos inexistentes)

- [ ] **Step 3: Criar `app/models/marca.py`**

```python
from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import FormaRessarcimento
from app.models.base import Base


class Marca(Base):
    __tablename__ = "marcas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    forma_ressarcimento_padrao: Mapped[FormaRessarcimento | None] = mapped_column(
        Enum(FormaRessarcimento), nullable=True
    )
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    devolucoes: Mapped[list["Devolucao"]] = relationship(  # type: ignore
        back_populates="marca", cascade="all"
    )
```

- [ ] **Step 4: Criar `app/repositories/marcas_repo.py`**

```python
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import FormaRessarcimento
from app.models.marca import Marca


def criar(session: Session, *, nome: str,
          forma_padrao: Optional[FormaRessarcimento] = None,
          observacoes: Optional[str] = None) -> Marca:
    marca = Marca(nome=nome, forma_ressarcimento_padrao=forma_padrao,
                  observacoes=observacoes)
    session.add(marca)
    return marca


def buscar_por_id(session: Session, marca_id: int) -> Optional[Marca]:
    return session.get(Marca, marca_id)


def listar(session: Session) -> list[Marca]:
    return list(session.scalars(select(Marca).order_by(Marca.nome)))


def atualizar(session: Session, marca_id: int, **campos) -> Optional[Marca]:
    marca = session.get(Marca, marca_id)
    if marca is None:
        return None
    for k, v in campos.items():
        setattr(marca, k, v)
    return marca


def excluir(session: Session, marca_id: int) -> bool:
    marca = session.get(Marca, marca_id)
    if marca is None:
        return False
    session.delete(marca)
    return True
```

- [ ] **Step 5: Rodar e ver passar**

```bash
uv run pytest tests/test_marcas_repo.py -v
```
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add app/models/marca.py app/repositories/marcas_repo.py tests/test_marcas_repo.py
git commit -m "feat(marca): modelo + repositorio com CRUD basico"
```

---

### Task 6: Modelo Devolucao + HistoricoStatus + Anexo (schema completo)

**Files:**
- Create: `app/models/devolucao.py`, `app/models/historico.py`, `app/models/anexo.py`

Faço os três modelos juntos porque têm FK entre si e querer testar Devolucao sem os outros vira muambada.

- [ ] **Step 1: Criar `app/models/devolucao.py`**

```python
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import DestinoFisico, FormaRessarcimento, StatusProcesso
from app.models.base import Base


class Devolucao(Base):
    __tablename__ = "devolucoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marca_id: Mapped[int] = mapped_column(ForeignKey("marcas.id"), nullable=False)

    # Produto
    produto_modelo: Mapped[str] = mapped_column(String(200), nullable=False)
    produto_referencia: Mapped[Optional[str]] = mapped_column(String(120))
    quantidade: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    valor_custo: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    defeito_descricao: Mapped[Optional[str]] = mapped_column(Text)
    foto_principal_caminho: Mapped[Optional[str]] = mapped_column(String(500))

    # Datas
    data_devolucao: Mapped[date] = mapped_column(Date, nullable=False)
    data_compra_original: Mapped[Optional[date]] = mapped_column(Date)

    # NFs
    nf_origem: Mapped[Optional[str]] = mapped_column(String(60))
    nf_abatimento: Mapped[Optional[str]] = mapped_column(String(60))

    # Cliente
    cliente_nome: Mapped[Optional[str]] = mapped_column(String(200))
    cliente_contato: Mapped[Optional[str]] = mapped_column(String(120))
    cliente_aguardando_retorno: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Status (3 eixos)
    status_processo: Mapped[StatusProcesso] = mapped_column(
        Enum(StatusProcesso), default=StatusProcesso.DEFEITO_IDENTIFICADO, nullable=False
    )
    destino_fisico: Mapped[DestinoFisico] = mapped_column(
        Enum(DestinoFisico), default=DestinoFisico.NA_LOJA, nullable=False
    )
    forma_ressarcimento: Mapped[Optional[FormaRessarcimento]] = mapped_column(Enum(FormaRessarcimento))

    # Texto livre
    observacoes: Mapped[Optional[str]] = mapped_column(Text)

    # Auditoria + lixeira
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    excluido_em: Mapped[Optional[datetime]] = mapped_column(DateTime)

    marca: Mapped["Marca"] = relationship(back_populates="devolucoes")  # type: ignore
    anexos: Mapped[list["Anexo"]] = relationship(  # type: ignore
        back_populates="devolucao", cascade="all, delete-orphan"
    )
    historicos: Mapped[list["HistoricoStatus"]] = relationship(  # type: ignore
        back_populates="devolucao", cascade="all, delete-orphan", order_by="HistoricoStatus.data"
    )
```

- [ ] **Step 2: Criar `app/models/historico.py`**

```python
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HistoricoStatus(Base):
    __tablename__ = "historico_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    devolucao_id: Mapped[int] = mapped_column(ForeignKey("devolucoes.id"), nullable=False)
    campo: Mapped[str] = mapped_column(String(40), nullable=False)  # status_processo | destino_fisico
    valor_anterior: Mapped[Optional[str]] = mapped_column(String(60))
    valor_novo: Mapped[str] = mapped_column(String(60), nullable=False)
    observacao: Mapped[Optional[str]] = mapped_column(Text)
    data: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    devolucao: Mapped["Devolucao"] = relationship(back_populates="historicos")  # type: ignore
```

- [ ] **Step 3: Criar `app/models/anexo.py`**

```python
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Anexo(Base):
    __tablename__ = "anexos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    devolucao_id: Mapped[int] = mapped_column(ForeignKey("devolucoes.id"), nullable=False)
    nome_original: Mapped[str] = mapped_column(String(300), nullable=False)
    caminho_interno: Mapped[str] = mapped_column(String(500), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf | imagem | outro
    tamanho_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    devolucao: Mapped["Devolucao"] = relationship(back_populates="anexos")  # type: ignore
```

- [ ] **Step 4: Garantir que models são importados (registra no metadata)**

Adicionar em `app/models/__init__.py`:

```python
from app.models.marca import Marca
from app.models.devolucao import Devolucao
from app.models.anexo import Anexo
from app.models.historico import HistoricoStatus

__all__ = ["Marca", "Devolucao", "Anexo", "HistoricoStatus"]
```

- [ ] **Step 5: Sanity check — banco em memória cria todas as tabelas**

Adicionar `tests/test_schema.py`:

```python
from sqlalchemy import inspect

from app.db import get_engine


def test_todas_as_tabelas_existem(session):
    insp = inspect(session.get_bind())
    tabelas = set(insp.get_table_names())
    assert {"marcas", "devolucoes", "anexos", "historico_status"} <= tabelas
```

```bash
uv run pytest tests/test_schema.py -v
```
Expected: 1 passed

- [ ] **Step 6: Commit**

```bash
git add app/models/ tests/test_schema.py
git commit -m "feat(models): Devolucao + Anexo + HistoricoStatus com relacionamentos"
```

---

### Task 7: Repositório de Devoluções

**Files:**
- Create: `app/repositories/devolucoes_repo.py`, `tests/test_devolucoes_repo.py`

- [ ] **Step 1: Escrever testes**

```python
# tests/test_devolucoes_repo.py
from datetime import date

import pytest

from app.constants import DestinoFisico, FormaRessarcimento, StatusProcesso
from app.repositories import devolucoes_repo, marcas_repo


@pytest.fixture
def marca(session):
    m = marcas_repo.criar(session, nome="Vizzano")
    session.flush()
    return m


def test_criar_devolucao_com_defaults(session, marca):
    d = devolucoes_repo.criar(
        session, marca_id=marca.id, produto_modelo="Sandália X",
        data_devolucao=date(2026, 5, 12),
    )
    session.flush()
    assert d.id is not None
    assert d.status_processo == StatusProcesso.DEFEITO_IDENTIFICADO
    assert d.destino_fisico == DestinoFisico.NA_LOJA
    assert d.quantidade == 1
    assert d.excluido_em is None


def test_listar_exclui_da_lixeira(session, marca):
    d1 = devolucoes_repo.criar(session, marca_id=marca.id,
                                produto_modelo="A", data_devolucao=date(2026, 5, 1))
    d2 = devolucoes_repo.criar(session, marca_id=marca.id,
                                produto_modelo="B", data_devolucao=date(2026, 5, 2))
    session.flush()
    devolucoes_repo.marcar_como_excluida(session, d1.id)
    session.flush()

    ativas = devolucoes_repo.listar_ativas(session)
    assert [d.id for d in ativas] == [d2.id]

    lixeira = devolucoes_repo.listar_lixeira(session)
    assert [d.id for d in lixeira] == [d1.id]


def test_filtrar_por_status_e_marca(session, marca):
    outra = marcas_repo.criar(session, nome="Olympikus")
    session.flush()
    d1 = devolucoes_repo.criar(session, marca_id=marca.id, produto_modelo="A",
                                data_devolucao=date(2026, 5, 1))
    d2 = devolucoes_repo.criar(session, marca_id=outra.id, produto_modelo="B",
                                data_devolucao=date(2026, 5, 2))
    d2.status_processo = StatusProcesso.RESSARCIDO
    session.flush()

    so_vizzano = devolucoes_repo.listar_ativas(session, marca_id=marca.id)
    assert [d.id for d in so_vizzano] == [d1.id]

    so_ressarcidas = devolucoes_repo.listar_ativas(
        session, status=StatusProcesso.RESSARCIDO
    )
    assert [d.id for d in so_ressarcidas] == [d2.id]


def test_busca_textual(session, marca):
    devolucoes_repo.criar(session, marca_id=marca.id, produto_modelo="Sandália Salto",
                          data_devolucao=date(2026, 5, 1))
    devolucoes_repo.criar(session, marca_id=marca.id, produto_modelo="Bota",
                          data_devolucao=date(2026, 5, 2),
                          cliente_nome="Maria Santos")
    session.flush()

    r1 = devolucoes_repo.listar_ativas(session, busca="salto")
    assert len(r1) == 1
    r2 = devolucoes_repo.listar_ativas(session, busca="maria")
    assert len(r2) == 1
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_devolucoes_repo.py -v
```
Expected: FAIL (módulo inexistente)

- [ ] **Step 3: Implementar `app/repositories/devolucoes_repo.py`**

```python
from datetime import datetime
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.constants import DestinoFisico, StatusProcesso
from app.models.devolucao import Devolucao


def criar(session: Session, **campos) -> Devolucao:
    d = Devolucao(**campos)
    session.add(d)
    return d


def buscar_por_id(session: Session, devolucao_id: int) -> Optional[Devolucao]:
    return session.get(Devolucao, devolucao_id)


def _base_query():
    return select(Devolucao).options(
        joinedload(Devolucao.marca),
        joinedload(Devolucao.anexos),
    )


def listar_ativas(session: Session, *,
                  marca_id: Optional[int] = None,
                  status: Optional[StatusProcesso] = None,
                  destino: Optional[DestinoFisico] = None,
                  aguardando_retorno: Optional[bool] = None,
                  busca: Optional[str] = None) -> list[Devolucao]:
    q = _base_query().where(Devolucao.excluido_em.is_(None))
    if marca_id is not None:
        q = q.where(Devolucao.marca_id == marca_id)
    if status is not None:
        q = q.where(Devolucao.status_processo == status)
    if destino is not None:
        q = q.where(Devolucao.destino_fisico == destino)
    if aguardando_retorno is True:
        q = q.where(Devolucao.cliente_aguardando_retorno.is_(True))
    if busca:
        termo = f"%{busca.lower()}%"
        q = q.where(or_(
            Devolucao.produto_modelo.ilike(termo),
            Devolucao.produto_referencia.ilike(termo),
            Devolucao.cliente_nome.ilike(termo),
            Devolucao.observacoes.ilike(termo),
        ))
    q = q.order_by(Devolucao.data_devolucao.desc(), Devolucao.id.desc())
    return list(session.scalars(q).unique())


def listar_lixeira(session: Session) -> list[Devolucao]:
    q = _base_query().where(Devolucao.excluido_em.is_not(None)) \
        .order_by(Devolucao.excluido_em.desc())
    return list(session.scalars(q).unique())


def marcar_como_excluida(session: Session, devolucao_id: int) -> bool:
    d = session.get(Devolucao, devolucao_id)
    if d is None:
        return False
    d.excluido_em = datetime.utcnow()
    return True


def restaurar(session: Session, devolucao_id: int) -> bool:
    d = session.get(Devolucao, devolucao_id)
    if d is None or d.excluido_em is None:
        return False
    d.excluido_em = None
    return True


def excluir_definitivo(session: Session, devolucao_id: int) -> bool:
    d = session.get(Devolucao, devolucao_id)
    if d is None:
        return False
    session.delete(d)
    return True
```

- [ ] **Step 4: Rodar e ver passar**

```bash
uv run pytest tests/test_devolucoes_repo.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/repositories/devolucoes_repo.py tests/test_devolucoes_repo.py
git commit -m "feat(devolucoes_repo): CRUD + filtros + soft delete"
```

---

### Task 8: Repositórios de Anexo e Histórico

**Files:**
- Create: `app/repositories/anexos_repo.py`, `app/repositories/historico_repo.py`, `tests/test_anexos_repo.py`

Esses dois são pequenos. Faço juntos.

- [ ] **Step 1: Criar `app/repositories/historico_repo.py`**

```python
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.historico import HistoricoStatus


def registrar(session: Session, *, devolucao_id: int, campo: str,
              valor_anterior: Optional[str], valor_novo: str,
              observacao: Optional[str] = None) -> HistoricoStatus:
    h = HistoricoStatus(
        devolucao_id=devolucao_id, campo=campo,
        valor_anterior=valor_anterior, valor_novo=valor_novo,
        observacao=observacao,
    )
    session.add(h)
    return h


def listar_por_devolucao(session: Session, devolucao_id: int) -> list[HistoricoStatus]:
    q = select(HistoricoStatus).where(HistoricoStatus.devolucao_id == devolucao_id) \
        .order_by(HistoricoStatus.data)
    return list(session.scalars(q))
```

- [ ] **Step 2: Criar `app/repositories/anexos_repo.py`**

```python
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.anexo import Anexo


def criar(session: Session, *, devolucao_id: int, nome_original: str,
          caminho_interno: str, tipo: str, tamanho_bytes: int) -> Anexo:
    a = Anexo(devolucao_id=devolucao_id, nome_original=nome_original,
              caminho_interno=caminho_interno, tipo=tipo, tamanho_bytes=tamanho_bytes)
    session.add(a)
    return a


def buscar_por_id(session: Session, anexo_id: int) -> Optional[Anexo]:
    return session.get(Anexo, anexo_id)


def listar_por_devolucao(session: Session, devolucao_id: int) -> list[Anexo]:
    q = select(Anexo).where(Anexo.devolucao_id == devolucao_id) \
        .order_by(Anexo.criado_em)
    return list(session.scalars(q))


def excluir(session: Session, anexo_id: int) -> bool:
    a = session.get(Anexo, anexo_id)
    if a is None:
        return False
    session.delete(a)
    return True
```

- [ ] **Step 3: Teste em `tests/test_anexos_repo.py`**

```python
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
```

- [ ] **Step 4: Rodar**

```bash
uv run pytest tests/test_anexos_repo.py -v
```
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/repositories/anexos_repo.py app/repositories/historico_repo.py tests/test_anexos_repo.py
git commit -m "feat(repos): anexos_repo + historico_repo"
```

---

## FASE 3 — Services

### Task 9: DevolucaoService (criação + mudança de status com histórico)

**Files:**
- Create: `app/services/devolucao_service.py`, `tests/test_devolucao_service.py`

A regra principal: ao mudar `status_processo` ou `destino_fisico`, registrar no histórico.

- [ ] **Step 1: Escrever testes**

```python
# tests/test_devolucao_service.py
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
```

- [ ] **Step 2: Rodar — ver falhar**

```bash
uv run pytest tests/test_devolucao_service.py -v
```
Expected: FAIL

- [ ] **Step 3: Implementar `app/services/devolucao_service.py`**

```python
from typing import Optional

from sqlalchemy.orm import Session

from app.constants import DestinoFisico, StatusProcesso
from app.models.devolucao import Devolucao
from app.repositories import devolucoes_repo, historico_repo, marcas_repo


def criar(session: Session, **campos) -> Devolucao:
    marca_id = campos.get("marca_id")
    # Se nao foi informada forma_ressarcimento, usa a padrao da marca
    if "forma_ressarcimento" not in campos and marca_id is not None:
        marca = marcas_repo.buscar_por_id(session, marca_id)
        if marca and marca.forma_ressarcimento_padrao:
            campos["forma_ressarcimento"] = marca.forma_ressarcimento_padrao

    d = devolucoes_repo.criar(session, **campos)
    session.flush()  # garante id

    historico_repo.registrar(
        session, devolucao_id=d.id, campo="status_processo",
        valor_anterior=None, valor_novo=d.status_processo.value,
    )
    historico_repo.registrar(
        session, devolucao_id=d.id, campo="destino_fisico",
        valor_anterior=None, valor_novo=d.destino_fisico.value,
    )
    return d


def buscar(session: Session, devolucao_id: int) -> Optional[Devolucao]:
    return devolucoes_repo.buscar_por_id(session, devolucao_id)


def mudar_status_processo(session: Session, devolucao_id: int, *,
                           novo: StatusProcesso,
                           observacao: Optional[str] = None) -> Optional[Devolucao]:
    d = devolucoes_repo.buscar_por_id(session, devolucao_id)
    if d is None or d.status_processo == novo:
        return d
    anterior = d.status_processo.value
    d.status_processo = novo
    historico_repo.registrar(
        session, devolucao_id=d.id, campo="status_processo",
        valor_anterior=anterior, valor_novo=novo.value, observacao=observacao,
    )
    return d


def mudar_destino_fisico(session: Session, devolucao_id: int, *,
                          novo: DestinoFisico,
                          observacao: Optional[str] = None) -> Optional[Devolucao]:
    d = devolucoes_repo.buscar_por_id(session, devolucao_id)
    if d is None or d.destino_fisico == novo:
        return d
    anterior = d.destino_fisico.value
    d.destino_fisico = novo
    historico_repo.registrar(
        session, devolucao_id=d.id, campo="destino_fisico",
        valor_anterior=anterior, valor_novo=novo.value, observacao=observacao,
    )
    return d


def atualizar(session: Session, devolucao_id: int, **campos) -> Optional[Devolucao]:
    """Atualiza qualquer combinação de campos. Se status_processo ou
    destino_fisico forem alterados, gera histórico automaticamente."""
    d = devolucoes_repo.buscar_por_id(session, devolucao_id)
    if d is None:
        return None

    novo_status = campos.pop("status_processo", None)
    novo_destino = campos.pop("destino_fisico", None)

    for k, v in campos.items():
        setattr(d, k, v)

    if novo_status is not None:
        mudar_status_processo(session, devolucao_id, novo=novo_status)
    if novo_destino is not None:
        mudar_destino_fisico(session, devolucao_id, novo=novo_destino)

    return d
```

- [ ] **Step 4: Rodar e ver passar**

```bash
uv run pytest tests/test_devolucao_service.py -v
```
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add app/services/devolucao_service.py tests/test_devolucao_service.py
git commit -m "feat(devolucao_service): criar/editar com historico automatico de status"
```

---

### Task 10: AnexoService (upload, thumbnail, validação)

**Files:**
- Create: `app/services/anexo_service.py`, `tests/test_anexo_service.py`

- [ ] **Step 1: Escrever testes**

```python
# tests/test_anexo_service.py
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
```

- [ ] **Step 2: Implementar `app/services/anexo_service.py`**

```python
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
```

- [ ] **Step 3: Rodar**

```bash
uv run pytest tests/test_anexo_service.py -v
```
Expected: 5 passed

- [ ] **Step 4: Commit**

```bash
git add app/services/anexo_service.py tests/test_anexo_service.py
git commit -m "feat(anexo_service): upload com validacao + thumbnail + remocao"
```

---

### Task 11: LixeiraService (soft delete, restore, purge)

**Files:**
- Create: `app/services/lixeira_service.py`, `tests/test_lixeira_service.py`

- [ ] **Step 1: Escrever testes**

```python
# tests/test_lixeira_service.py
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
    anexo = anexo_service.salvar_anexo(session, devolucao.id, img, como_principal=True)
    session.flush()
    pasta_devolucao = (isolated_data_dir / "anexos" / f"{devolucao.id:04d}")
    assert pasta_devolucao.exists()

    devolucao.excluido_em = datetime.utcnow() - timedelta(days=40)
    session.flush()
    lixeira_service.expurgar_antigas(session)
    session.flush()
    assert not pasta_devolucao.exists()
```

- [ ] **Step 2: Implementar `app/services/lixeira_service.py`**

```python
import shutil
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import Config
from app.constants import LIXEIRA_DIAS
from app.repositories import devolucoes_repo


def enviar_para_lixeira(session: Session, devolucao_id: int) -> bool:
    return devolucoes_repo.marcar_como_excluida(session, devolucao_id)


def restaurar(session: Session, devolucao_id: int) -> bool:
    return devolucoes_repo.restaurar(session, devolucao_id)


def expurgar_antigas(session: Session) -> list[int]:
    """Apaga DEFINITIVAMENTE devoluções excluídas há mais de LIXEIRA_DIAS dias.
    Remove também a pasta de anexos do disco."""
    limite = datetime.utcnow() - timedelta(days=LIXEIRA_DIAS)
    cfg = Config.load()
    antigas = devolucoes_repo.listar_lixeira(session)
    ids_apagados: list[int] = []
    for d in antigas:
        if d.excluido_em is not None and d.excluido_em < limite:
            pasta = cfg.anexos_dir / f"{d.id:04d}"
            if pasta.exists():
                shutil.rmtree(pasta, ignore_errors=True)
            devolucoes_repo.excluir_definitivo(session, d.id)
            ids_apagados.append(d.id)
    return ids_apagados
```

- [ ] **Step 3: Rodar**

```bash
uv run pytest tests/test_lixeira_service.py -v
```
Expected: 4 passed

- [ ] **Step 4: Commit**

```bash
git add app/services/lixeira_service.py tests/test_lixeira_service.py
git commit -m "feat(lixeira_service): soft delete + restore + expurgo de 30 dias"
```

---

### Task 12: BackupService (zip + rotação)

**Files:**
- Create: `app/services/backup_service.py`, `tests/test_backup_service.py`

- [ ] **Step 1: Escrever testes**

```python
# tests/test_backup_service.py
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
```

- [ ] **Step 2: Implementar `app/services/backup_service.py`**

```python
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
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destino = destino_dir / f"{timestamp}_backup.zip"

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
```

- [ ] **Step 3: Rodar**

```bash
uv run pytest tests/test_backup_service.py -v
```
Expected: 3 passed

- [ ] **Step 4: Commit**

```bash
git add app/services/backup_service.py tests/test_backup_service.py
git commit -m "feat(backup_service): zip + rotacao + ultimo_backup"
```

---

### Task 13: Roda toda a suíte e confere cobertura mínima dos services

- [ ] **Step 1: Rodar tudo**

```bash
uv run pytest --cov=app/services --cov=app/repositories -v
```
Expected: todos os testes passam; cobertura de `app/services` ≥ 85%

- [ ] **Step 2: Se algum service estiver abaixo de 80%, adicionar um teste rápido cobrindo o caminho faltando**

Olhe o output `Missing` do pytest-cov, identifique a linha, adicione 1 teste curto para cobrir.

- [ ] **Step 3: Commit (se houve mudança)**

```bash
git add tests/
git commit -m "test: cobertura adicional onde estava abaixo de 80%"
```

---

## FASE 4 — UI (NiceGUI)

> **Padrão geral**: todas as páginas NiceGUI seguem `def render() -> None:` e são montadas pelo `layout.py`. As páginas leem/escrevem via `session_scope()` para garantir transações atômicas. UI sem testes automatizados.

### Task 14: Layout principal e menu lateral

**Files:**
- Create: `app/ui/layout.py`, `main.py`

- [ ] **Step 1: Criar `app/ui/layout.py`**

```python
from nicegui import ui


PAGINAS = [
    ("/", "Devoluções", "list_alt"),
    ("/marcas", "Marcas", "label"),
    ("/lixeira", "Lixeira", "delete"),
    ("/configuracoes", "Configurações", "settings"),
]


def montar_layout(titulo_pagina: str) -> ui.column:
    """Monta header + menu lateral e devolve o container de conteúdo."""
    with ui.header().classes("items-center justify-between bg-primary text-white"):
        ui.label("Loja Simonetto — Devoluções").classes("text-lg font-bold")
        ui.label(titulo_pagina).classes("text-sm opacity-80")

    with ui.left_drawer(value=True, fixed=True).classes("bg-grey-2"):
        ui.label("Menu").classes("text-xs uppercase text-grey-7 q-pa-sm")
        for rota, label, icone in PAGINAS:
            ui.link(label, rota).classes("flex items-center gap-2 q-pa-sm hover:bg-grey-4 no-underline text-black") \
                .props(f'icon={icone}')

    container = ui.column().classes("w-full q-pa-md")
    return container
```

- [ ] **Step 2: Criar `main.py`**

```python
from nicegui import app, ui

from app.config import Config
from app.db import init_engine
from app.services import backup_service, lixeira_service
from app.db import session_scope


def _boot():
    Config.load()
    init_engine()
    with session_scope() as s:
        lixeira_service.expurgar_antigas(s)


def _at_shutdown():
    try:
        backup_service.criar_backup()
    except Exception as e:
        print(f"Falha no backup automático: {e}")


# Registra páginas
from app.ui.pages import lista, marcas, lixeira, configuracoes  # noqa: E402

@ui.page("/")
def pagina_lista():
    lista.render()


@ui.page("/marcas")
def pagina_marcas():
    marcas.render()


@ui.page("/lixeira")
def pagina_lixeira():
    lixeira.render()


@ui.page("/configuracoes")
def pagina_configuracoes():
    configuracoes.render()


_boot()
app.on_shutdown(_at_shutdown)

ui.run(title="Simonetto Devoluções", native=True, window_size=(1280, 800),
       reload=False, show=False, prefer_local=True)
```

> **Nota:** `prefer_local=True` faz NiceGUI servir assets do disco em vez de CDN. `native=True` abre janela tipo desktop. Se `native` der problema (ex: pywebview ausente), trocar por `native=False` e abrir no navegador padrão.

- [ ] **Step 3: Sanity check — app sobe sem erro**

```bash
uv run python -c "from app.ui import layout; print('layout ok')"
```
Expected: `layout ok` (não testamos `main.py` por causa do `ui.run`)

- [ ] **Step 4: Commit**

```bash
git add app/ui/layout.py main.py
git commit -m "feat(ui): layout principal + menu lateral + main.py com boot e shutdown"
```

---

### Task 15: Página Marcas (CRUD simples)

**Files:**
- Create: `app/ui/pages/marcas.py`

Implementação curta, sem teste automatizado (UI).

- [ ] **Step 1: Criar `app/ui/pages/marcas.py`**

```python
from nicegui import ui

from app.constants import FormaRessarcimento, FORMA_RESSARCIMENTO_LABELS
from app.db import session_scope
from app.repositories import marcas_repo


def render():
    from app.ui.layout import montar_layout
    montar_layout("Marcas")

    container = ui.column().classes("w-full max-w-3xl")

    def recarregar():
        container.clear()
        with container:
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("Marcas cadastradas").classes("text-h6")
                ui.button("+ Nova marca", on_click=abrir_form_nova) \
                    .classes("bg-primary text-white")

            with session_scope() as s:
                marcas = marcas_repo.listar(s)
                marcas_data = [(m.id, m.nome,
                                 m.forma_ressarcimento_padrao.value if m.forma_ressarcimento_padrao else None,
                                 m.observacoes) for m in marcas]

            if not marcas_data:
                ui.label("Nenhuma marca cadastrada ainda.").classes("text-grey-7")
                return

            for mid, nome, forma, obs in marcas_data:
                with ui.card().classes("w-full"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.column():
                            ui.label(nome).classes("text-subtitle1 font-bold")
                            if forma:
                                label_forma = FORMA_RESSARCIMENTO_LABELS[FormaRessarcimento(forma)][0]
                                ui.label(f"Padrão: {label_forma}").classes("text-caption")
                            if obs:
                                ui.label(obs).classes("text-caption text-grey-7")
                        with ui.row():
                            ui.button(icon="edit",
                                      on_click=lambda _, i=mid: abrir_form_editar(i)).props("flat round")
                            ui.button(icon="delete",
                                      on_click=lambda _, i=mid, n=nome: confirmar_excluir(i, n)).props("flat round color=red")

    def abrir_form_nova():
        abrir_form(None)

    def abrir_form_editar(marca_id: int):
        abrir_form(marca_id)

    def abrir_form(marca_id):
        with session_scope() as s:
            marca = marcas_repo.buscar_por_id(s, marca_id) if marca_id else None
            nome = marca.nome if marca else ""
            forma = marca.forma_ressarcimento_padrao.value if marca and marca.forma_ressarcimento_padrao else None
            obs = marca.observacoes if marca else ""

        with ui.dialog() as dlg, ui.card().classes("w-96"):
            ui.label("Editar marca" if marca_id else "Nova marca").classes("text-h6")
            campo_nome = ui.input("Nome *").classes("w-full").bind_value_to(globals(), "_tmp")
            campo_nome.value = nome
            campo_forma = ui.select(
                options={None: "—"} | {f.value: FORMA_RESSARCIMENTO_LABELS[f][0]
                                        for f in FormaRessarcimento},
                label="Forma padrão de ressarcimento"
            ).classes("w-full")
            campo_forma.value = forma
            campo_obs = ui.textarea("Observações").classes("w-full")
            campo_obs.value = obs

            def salvar():
                if not campo_nome.value or not campo_nome.value.strip():
                    ui.notify("Nome é obrigatório", type="negative")
                    return
                forma_enum = FormaRessarcimento(campo_forma.value) if campo_forma.value else None
                with session_scope() as s:
                    if marca_id:
                        marcas_repo.atualizar(s, marca_id, nome=campo_nome.value.strip(),
                                              forma_ressarcimento_padrao=forma_enum,
                                              observacoes=campo_obs.value or None)
                    else:
                        marcas_repo.criar(s, nome=campo_nome.value.strip(),
                                          forma_padrao=forma_enum,
                                          observacoes=campo_obs.value or None)
                dlg.close()
                ui.notify("Salvo", type="positive")
                recarregar()

            with ui.row().classes("justify-end w-full"):
                ui.button("Cancelar", on_click=dlg.close).props("flat")
                ui.button("Salvar", on_click=salvar).classes("bg-primary text-white")
        dlg.open()

    def confirmar_excluir(marca_id: int, nome: str):
        with ui.dialog() as dlg, ui.card():
            ui.label(f"Excluir marca '{nome}'?")
            ui.label("Atenção: só funciona se não houver devoluções vinculadas.").classes("text-caption text-grey-7")
            with ui.row():
                ui.button("Cancelar", on_click=dlg.close).props("flat")
                def fazer():
                    try:
                        with session_scope() as s:
                            marcas_repo.excluir(s, marca_id)
                        ui.notify("Excluída", type="positive")
                        dlg.close()
                        recarregar()
                    except Exception as e:
                        ui.notify(f"Não foi possível excluir: {e}", type="negative")
                ui.button("Excluir", on_click=fazer).classes("bg-red text-white")
        dlg.open()

    recarregar()
```

- [ ] **Step 2: Smoke test manual (opcional, mas faz)**

```bash
uv run python main.py
```
Esperado: janela abre, clica em "Marcas", consegue criar uma marca, editar, excluir.

- [ ] **Step 3: Commit**

```bash
git add app/ui/pages/marcas.py
git commit -m "feat(ui): pagina Marcas com CRUD"
```

---

### Task 16: Componente badge_status (reutilizável)

**Files:**
- Create: `app/ui/components/badge_status.py`

- [ ] **Step 1: Implementar**

```python
from nicegui import ui

from app.constants import (
    DESTINO_FISICO_LABELS,
    DestinoFisico,
    FORMA_RESSARCIMENTO_LABELS,
    FormaRessarcimento,
    STATUS_PROCESSO_LABELS,
    StatusProcesso,
)


def badge_status_processo(status: StatusProcesso) -> None:
    label, cor, icone = STATUS_PROCESSO_LABELS[status]
    ui.badge(f"{icone} {label}", color=cor).classes("text-white q-pa-xs")


def badge_destino(destino: DestinoFisico) -> None:
    label, cor, icone = DESTINO_FISICO_LABELS[destino]
    ui.badge(f"{icone} {label}", color=cor).classes("text-white q-pa-xs")


def badge_forma(forma: FormaRessarcimento | None) -> None:
    if forma is None:
        return
    label, icone = FORMA_RESSARCIMENTO_LABELS[forma]
    ui.label(f"{icone} {label}").classes("text-caption")
```

- [ ] **Step 2: Commit**

```bash
git add app/ui/components/badge_status.py
git commit -m "feat(ui): componente reutilizavel de badges dos 3 eixos"
```

---

### Task 17: Página Lista de Devoluções (com filtros)

**Files:**
- Create: `app/ui/pages/lista.py`

- [ ] **Step 1: Implementar**

```python
from datetime import date

from nicegui import ui

from app.config import Config
from app.constants import (BANNER_BACKUP_ALERTA_DIAS, DestinoFisico,
                            DESTINO_FISICO_LABELS, StatusProcesso,
                            STATUS_PROCESSO_LABELS)
from app.db import session_scope
from app.repositories import devolucoes_repo, marcas_repo
from app.services import backup_service
from app.ui.components.badge_status import (badge_destino, badge_forma,
                                              badge_status_processo)


def render():
    from app.ui.layout import montar_layout
    from app.ui.components.form_devolucao import abrir_form_devolucao
    from app.ui.components.detalhe_devolucao import abrir_detalhe

    montar_layout("Devoluções")

    # Estado dos filtros
    filtros = {
        "busca": "",
        "marca_id": None,
        "status": None,
        "destino": None,
        "aguardando": False,
    }

    container = ui.column().classes("w-full")

    def _banner_backup():
        info = backup_service.ultimo_backup()
        if info is None:
            with ui.row().classes("bg-yellow-2 q-pa-sm w-full items-center"):
                ui.label("⚠️ Nenhum backup foi feito ainda.")
                ui.button("Fazer backup agora",
                          on_click=lambda: (backup_service.criar_backup(),
                                            ui.notify("Backup criado"))
                          ).props("size=sm").classes("bg-primary text-white")
            return
        dias = (date.today() - info.criado_em.date()).days
        if dias >= BANNER_BACKUP_ALERTA_DIAS:
            with ui.row().classes("bg-yellow-2 q-pa-sm w-full items-center"):
                ui.label(f"⚠️ Último backup há {dias} dias.")
                ui.button("Fazer backup agora",
                          on_click=lambda: (backup_service.criar_backup(),
                                            ui.notify("Backup criado"))
                          ).props("size=sm").classes("bg-primary text-white")

    def recarregar():
        container.clear()
        with container:
            _banner_backup()

            # Barra de filtros
            with ui.row().classes("w-full items-end gap-2"):
                ui.input("Buscar...", on_change=lambda e: filtros.update(busca=e.value) or recarregar_lista()) \
                    .classes("w-64")

                with session_scope() as s:
                    marcas = [(m.id, m.nome) for m in marcas_repo.listar(s)]
                opcoes_marca = {None: "Todas marcas"} | {mid: nome for mid, nome in marcas}
                ui.select(opcoes_marca, label="Marca",
                          on_change=lambda e: filtros.update(marca_id=e.value) or recarregar_lista()) \
                    .classes("w-48").value = None

                opcoes_status = {None: "Todos status"} | {
                    s.value: STATUS_PROCESSO_LABELS[s][0] for s in StatusProcesso
                }
                ui.select(opcoes_status, label="Status",
                          on_change=lambda e: filtros.update(
                              status=StatusProcesso(e.value) if e.value else None) or recarregar_lista()) \
                    .classes("w-56").value = None

                opcoes_dest = {None: "Todos destinos"} | {
                    d.value: DESTINO_FISICO_LABELS[d][0] for d in DestinoFisico
                }
                ui.select(opcoes_dest, label="Destino",
                          on_change=lambda e: filtros.update(
                              destino=DestinoFisico(e.value) if e.value else None) or recarregar_lista()) \
                    .classes("w-48").value = None

                ui.checkbox("Aguardando retorno",
                            on_change=lambda e: filtros.update(aguardando=e.value) or recarregar_lista())

                ui.space()
                ui.button("+ Nova Devolução",
                          on_click=lambda: abrir_form_devolucao(on_save=recarregar)) \
                    .classes("bg-primary text-white")

            # Lista
            lista_container = ui.column().classes("w-full gap-2")

            def recarregar_lista():
                lista_container.clear()
                with session_scope() as s:
                    devs = devolucoes_repo.listar_ativas(
                        s,
                        marca_id=filtros["marca_id"],
                        status=filtros["status"],
                        destino=filtros["destino"],
                        aguardando_retorno=True if filtros["aguardando"] else None,
                        busca=filtros["busca"] or None,
                    )
                    cfg = Config.load()
                    dados = []
                    for d in devs:
                        thumb = (cfg.data_dir / d.foto_principal_caminho).as_posix() \
                            if d.foto_principal_caminho else None
                        dados.append({
                            "id": d.id,
                            "marca": d.marca.nome,
                            "modelo": d.produto_modelo,
                            "ref": d.produto_referencia,
                            "data": d.data_devolucao.strftime("%d/%m/%Y"),
                            "cliente": d.cliente_nome,
                            "aguardando": d.cliente_aguardando_retorno,
                            "status": d.status_processo,
                            "destino": d.destino_fisico,
                            "forma": d.forma_ressarcimento,
                            "thumb": thumb,
                        })

                with lista_container:
                    if not dados:
                        ui.label("Nenhuma devolução com esses filtros.").classes("text-grey-7 q-pa-md")
                        return
                    for d in dados:
                        with ui.card().classes("w-full cursor-pointer hover:bg-grey-1") \
                                .on("click", lambda _, i=d["id"]: abrir_detalhe(i, on_save=recarregar)):
                            with ui.row().classes("items-center w-full gap-4"):
                                if d["thumb"]:
                                    ui.image(d["thumb"]).classes("w-16 h-16 rounded")
                                else:
                                    ui.icon("image", size="lg").classes("text-grey-5")
                                with ui.column().classes("flex-grow gap-1"):
                                    ui.label(f"{d['marca']} · {d['modelo']}" +
                                             (f" · ref {d['ref']}" if d['ref'] else "")) \
                                        .classes("font-bold")
                                    cliente_str = ""
                                    if d["cliente"]:
                                        cliente_str = f"Cliente: {d['cliente']}"
                                        if d["aguardando"]:
                                            cliente_str += " ⏳"
                                    ui.label(f"Devolvido: {d['data']}" +
                                             (f"   {cliente_str}" if cliente_str else "")) \
                                        .classes("text-caption text-grey-7")
                                    with ui.row().classes("gap-2 items-center"):
                                        badge_status_processo(d["status"])
                                        badge_destino(d["destino"])
                                        badge_forma(d["forma"])

            recarregar_lista()

    recarregar()
```

- [ ] **Step 2: Commit**

```bash
git add app/ui/pages/lista.py
git commit -m "feat(ui): pagina Lista de devolucoes com filtros e banner de backup"
```

---

### Task 18: Componente form_devolucao (modal lateral)

**Files:**
- Create: `app/ui/components/form_devolucao.py`

- [ ] **Step 1: Implementar**

```python
from datetime import date
from pathlib import Path
from typing import Callable, Optional

from nicegui import events, ui

from app.constants import (DestinoFisico, DESTINO_FISICO_LABELS,
                            FormaRessarcimento, FORMA_RESSARCIMENTO_LABELS,
                            StatusProcesso, STATUS_PROCESSO_LABELS)
from app.db import session_scope
from app.repositories import marcas_repo
from app.services import anexo_service, devolucao_service


def abrir_form_devolucao(devolucao_id: Optional[int] = None,
                          on_save: Optional[Callable[[], None]] = None) -> None:
    """Abre modal lateral para criar (devolucao_id=None) ou editar."""
    with session_scope() as s:
        d = devolucao_service.buscar(s, devolucao_id) if devolucao_id else None
        marcas = [(m.id, m.nome, m.forma_ressarcimento_padrao) for m in marcas_repo.listar(s)]

    if not marcas:
        ui.notify("Cadastre ao menos uma marca antes de criar devolução.", type="warning")
        return

    valores = {
        "marca_id": d.marca_id if d else marcas[0][0],
        "produto_modelo": d.produto_modelo if d else "",
        "produto_referencia": (d.produto_referencia if d else "") or "",
        "quantidade": d.quantidade if d else 1,
        "valor_custo": float(d.valor_custo) if d and d.valor_custo else None,
        "defeito_descricao": (d.defeito_descricao if d else "") or "",
        "data_devolucao": d.data_devolucao if d else date.today(),
        "data_compra_original": d.data_compra_original if d else None,
        "nf_origem": (d.nf_origem if d else "") or "",
        "nf_abatimento": (d.nf_abatimento if d else "") or "",
        "cliente_nome": (d.cliente_nome if d else "") or "",
        "cliente_contato": (d.cliente_contato if d else "") or "",
        "cliente_aguardando_retorno": d.cliente_aguardando_retorno if d else False,
        "status_processo": d.status_processo if d else StatusProcesso.DEFEITO_IDENTIFICADO,
        "destino_fisico": d.destino_fisico if d else DestinoFisico.NA_LOJA,
        "forma_ressarcimento": d.forma_ressarcimento if d else None,
        "observacoes": (d.observacoes if d else "") or "",
    }
    foto_principal_temp: dict[str, Optional[Path]] = {"path": None}
    anexos_extras_temp: list[Path] = []

    with ui.dialog().props("position=right") as dlg, ui.card().classes("w-[480px] h-screen overflow-auto"):
        ui.label("Editar Devolução" if d else "Nova Devolução").classes("text-h6")

        # Marca
        opcoes_marca = {mid: nome for mid, nome, _ in marcas}
        sel_marca = ui.select(opcoes_marca, label="Marca *").classes("w-full")
        sel_marca.value = valores["marca_id"]

        def _sugerir_forma():
            for mid, _, forma in marcas:
                if mid == sel_marca.value and forma and not valores["forma_ressarcimento"]:
                    sel_forma.value = forma.value

        sel_marca.on("update:model-value", lambda _: _sugerir_forma())

        # Produto
        ui.separator()
        ui.label("Produto").classes("text-subtitle2")
        i_modelo = ui.input("Modelo *", value=valores["produto_modelo"]).classes("w-full")
        i_ref = ui.input("Referência", value=valores["produto_referencia"]).classes("w-full")
        i_qtd = ui.number("Quantidade", value=valores["quantidade"], min=1).classes("w-full")
        i_valor = ui.number("Valor custo (R$)", value=valores["valor_custo"],
                             format="%.2f").classes("w-full")
        i_defeito = ui.input("Defeito", value=valores["defeito_descricao"]).classes("w-full")

        def _on_upload_foto(e: events.UploadEventArguments):
            # Escreve bytes do upload num temp file preservando o nome original.
            from tempfile import mkdtemp
            tmp_dir = Path(mkdtemp())
            tmp = tmp_dir / e.name
            tmp.write_bytes(e.content.read())
            foto_principal_temp["path"] = tmp
            ui.notify(f"Foto principal selecionada: {e.name}")

        ui.upload(label="Foto principal", on_upload=_on_upload_foto, auto_upload=True,
                  max_files=1).props('accept=".jpg,.jpeg,.png,.webp"').classes("w-full")

        # Datas
        ui.separator()
        ui.label("Datas").classes("text-subtitle2")
        i_data_dev = ui.input("Data devolução *",
                               value=valores["data_devolucao"].isoformat()).classes("w-full")
        i_data_dev.props('type=date')
        i_data_compra = ui.input("Data da compra original",
                                  value=valores["data_compra_original"].isoformat()
                                  if valores["data_compra_original"] else "").classes("w-full")
        i_data_compra.props('type=date')

        # NFs
        ui.separator()
        ui.label("Notas Fiscais (opcional)").classes("text-subtitle2")
        i_nf_orig = ui.input("NF de origem", value=valores["nf_origem"]).classes("w-full")
        i_nf_abat = ui.input("NF de abatimento", value=valores["nf_abatimento"]).classes("w-full")

        # Cliente
        ui.separator()
        ui.label("Cliente (opcional)").classes("text-subtitle2")
        i_cli_nome = ui.input("Nome", value=valores["cliente_nome"]).classes("w-full")
        i_cli_ctt = ui.input("Contato", value=valores["cliente_contato"]).classes("w-full")
        i_aguardando = ui.checkbox("Cliente aguardando retorno",
                                    value=valores["cliente_aguardando_retorno"])

        # Status
        ui.separator()
        ui.label("Status").classes("text-subtitle2")
        opcoes_status = {s.value: STATUS_PROCESSO_LABELS[s][0] for s in StatusProcesso}
        sel_status = ui.select(opcoes_status, label="Processo").classes("w-full")
        sel_status.value = valores["status_processo"].value

        opcoes_dest = {dd.value: DESTINO_FISICO_LABELS[dd][0] for dd in DestinoFisico}
        sel_dest = ui.select(opcoes_dest, label="Destino físico").classes("w-full")
        sel_dest.value = valores["destino_fisico"].value

        opcoes_forma = {None: "—"} | {f.value: FORMA_RESSARCIMENTO_LABELS[f][0]
                                       for f in FormaRessarcimento}
        sel_forma = ui.select(opcoes_forma, label="Forma de ressarcimento").classes("w-full")
        sel_forma.value = valores["forma_ressarcimento"].value if valores["forma_ressarcimento"] else None

        # Observações
        ui.separator()
        i_obs = ui.textarea("Observações", value=valores["observacoes"]).classes("w-full")

        # Botões
        def salvar():
            if not i_modelo.value or not i_modelo.value.strip():
                ui.notify("Modelo é obrigatório", type="negative")
                return
            try:
                dd = date.fromisoformat(i_data_dev.value)
            except Exception:
                ui.notify("Data de devolução inválida", type="negative")
                return
            dc = None
            if i_data_compra.value:
                try:
                    dc = date.fromisoformat(i_data_compra.value)
                except Exception:
                    ui.notify("Data da compra inválida", type="negative")
                    return

            payload = dict(
                marca_id=sel_marca.value,
                produto_modelo=i_modelo.value.strip(),
                produto_referencia=i_ref.value or None,
                quantidade=int(i_qtd.value or 1),
                valor_custo=i_valor.value,
                defeito_descricao=i_defeito.value or None,
                data_devolucao=dd,
                data_compra_original=dc,
                nf_origem=i_nf_orig.value or None,
                nf_abatimento=i_nf_abat.value or None,
                cliente_nome=i_cli_nome.value or None,
                cliente_contato=i_cli_ctt.value or None,
                cliente_aguardando_retorno=bool(i_aguardando.value),
                status_processo=StatusProcesso(sel_status.value),
                destino_fisico=DestinoFisico(sel_dest.value),
                forma_ressarcimento=FormaRessarcimento(sel_forma.value) if sel_forma.value else None,
                observacoes=i_obs.value or None,
            )

            with session_scope() as s:
                if devolucao_id:
                    devolucao_service.atualizar(s, devolucao_id, **payload)
                    novo_id = devolucao_id
                else:
                    nova = devolucao_service.criar(s, **payload)
                    s.flush()
                    novo_id = nova.id

                if foto_principal_temp["path"]:
                    try:
                        anexo_service.salvar_anexo(s, novo_id, foto_principal_temp["path"],
                                                    como_principal=True)
                    except Exception as e:
                        ui.notify(f"Erro na foto principal: {e}", type="warning")

            ui.notify("Salvo", type="positive")
            dlg.close()
            if on_save:
                on_save()

        with ui.row().classes("w-full justify-end q-pt-md"):
            ui.button("Cancelar", on_click=dlg.close).props("flat")
            ui.button("Salvar", on_click=salvar).classes("bg-primary text-white")

    dlg.open()
```

> **Nota sobre upload:** `events.UploadEventArguments.content` é um stream BytesIO. O helper escreve o conteúdo num arquivo temporário preservando o nome original do arquivo (importante porque `anexo_service.salvar_anexo` usa o nome para determinar tipo/extensão).

- [ ] **Step 2: Commit**

```bash
git add app/ui/components/form_devolucao.py
git commit -m "feat(ui): modal lateral de nova/editar devolucao"
```

---

### Task 19: Componente detalhe_devolucao (com linha do tempo)

**Files:**
- Create: `app/ui/components/detalhe_devolucao.py`

- [ ] **Step 1: Implementar**

```python
import webbrowser
from pathlib import Path
from typing import Callable, Optional

from nicegui import ui

from app.config import Config
from app.constants import (DESTINO_FISICO_LABELS, FORMA_RESSARCIMENTO_LABELS,
                            STATUS_PROCESSO_LABELS)
from app.db import session_scope
from app.repositories import historico_repo
from app.services import anexo_service, devolucao_service, lixeira_service
from app.ui.components.badge_status import (badge_destino, badge_forma,
                                              badge_status_processo)


def abrir_detalhe(devolucao_id: int,
                   on_save: Optional[Callable[[], None]] = None) -> None:
    from app.ui.components.form_devolucao import abrir_form_devolucao

    with session_scope() as s:
        d = devolucao_service.buscar(s, devolucao_id)
        if d is None:
            ui.notify("Devolução não encontrada", type="negative")
            return
        # Carrega tudo agora pra usar fora da sessão
        dados = dict(
            id=d.id,
            marca=d.marca.nome,
            modelo=d.produto_modelo,
            referencia=d.produto_referencia,
            quantidade=d.quantidade,
            valor=float(d.valor_custo) if d.valor_custo else None,
            defeito=d.defeito_descricao,
            data_dev=d.data_devolucao,
            data_compra=d.data_compra_original,
            nf_origem=d.nf_origem,
            nf_abat=d.nf_abatimento,
            cliente_nome=d.cliente_nome,
            cliente_contato=d.cliente_contato,
            aguardando=d.cliente_aguardando_retorno,
            status=d.status_processo,
            destino=d.destino_fisico,
            forma=d.forma_ressarcimento,
            observacoes=d.observacoes,
            foto=d.foto_principal_caminho,
            anexos=[(a.id, a.nome_original, a.caminho_interno, a.tipo) for a in d.anexos],
        )
        historico = [(h.campo, h.valor_anterior, h.valor_novo, h.data, h.observacao)
                     for h in historico_repo.listar_por_devolucao(s, devolucao_id)]

    cfg = Config.load()

    with ui.dialog().props("maximized=false") as dlg, ui.card().classes("w-[700px] max-h-[90vh] overflow-auto"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(f"{dados['marca']} · {dados['modelo']}").classes("text-h6")
            ui.button(icon="close", on_click=dlg.close).props("flat round")

        # Foto + badges
        with ui.row().classes("w-full gap-4 items-start"):
            if dados["foto"]:
                ui.image((cfg.data_dir / dados["foto"]).as_posix()).classes("w-32 h-32 rounded")
            with ui.column().classes("gap-2"):
                ui.label(f"Devolvido em {dados['data_dev'].strftime('%d/%m/%Y')}").classes("text-caption")
                if dados["referencia"]:
                    ui.label(f"Ref: {dados['referencia']}").classes("text-caption")
                with ui.row().classes("gap-2 items-center"):
                    badge_status_processo(dados["status"])
                    badge_destino(dados["destino"])
                    badge_forma(dados["forma"])

        ui.separator()

        # Detalhes
        with ui.column().classes("gap-1"):
            ui.label("Detalhes").classes("text-subtitle2")
            ui.label(f"Quantidade: {dados['quantidade']}"
                     + (f"   Valor: R$ {dados['valor']:.2f}" if dados['valor'] else ""))
            if dados["defeito"]:
                ui.label(f"Defeito: {dados['defeito']}")
            if dados["nf_origem"] or dados["nf_abat"]:
                ui.label(f"NF origem: {dados['nf_origem'] or '—'}   "
                         f"NF abatimento: {dados['nf_abat'] or '—'}")
            if dados["cliente_nome"]:
                cli = dados["cliente_nome"]
                if dados["aguardando"]:
                    cli += " ⏳ (aguardando retorno)"
                if dados["cliente_contato"]:
                    cli += f" · {dados['cliente_contato']}"
                ui.label(f"Cliente: {cli}")

        # Anexos
        ui.separator()
        ui.label("Anexos").classes("text-subtitle2")
        if not dados["anexos"]:
            ui.label("Nenhum anexo.").classes("text-grey-7")
        else:
            for aid, nome, caminho, tipo in dados["anexos"]:
                with ui.row().classes("items-center gap-2"):
                    ui.icon("picture_as_pdf" if tipo == "pdf" else "image")
                    ui.label(nome)
                    ui.button("Abrir",
                              on_click=lambda _, c=caminho: webbrowser.open(
                                  (cfg.data_dir / c).as_uri())) \
                        .props("flat size=sm")
                    def _remover(aid=aid):
                        with session_scope() as s:
                            anexo_service.remover_anexo(s, aid)
                        ui.notify("Anexo removido")
                        dlg.close()
                        abrir_detalhe(devolucao_id, on_save=on_save)
                    ui.button("Remover", on_click=_remover).props("flat size=sm color=red")

        # Observações
        if dados["observacoes"]:
            ui.separator()
            ui.label("Observações").classes("text-subtitle2")
            ui.label(dados["observacoes"]).classes("whitespace-pre-wrap")

        # Linha do tempo
        ui.separator()
        ui.label("Linha do tempo").classes("text-subtitle2")
        with ui.column().classes("gap-1"):
            for campo, anterior, novo, data, obs in historico:
                data_str = data.strftime("%d/%m/%Y %H:%M")
                if campo == "status_processo":
                    from app.constants import StatusProcesso
                    label_novo = STATUS_PROCESSO_LABELS[StatusProcesso(novo)][0]
                    texto = f"• {data_str}  Status → {label_novo}"
                else:
                    from app.constants import DestinoFisico
                    label_novo = DESTINO_FISICO_LABELS[DestinoFisico(novo)][0]
                    texto = f"• {data_str}  Destino → {label_novo}"
                if obs:
                    texto += f"  ({obs})"
                ui.label(texto).classes("text-caption")

        # Ações
        ui.separator()
        with ui.row().classes("w-full justify-end gap-2"):
            def _excluir():
                with ui.dialog() as confirm, ui.card():
                    ui.label("Mover para a lixeira?")
                    ui.label("Você terá 30 dias para restaurar.").classes("text-caption text-grey-7")
                    with ui.row():
                        ui.button("Cancelar", on_click=confirm.close).props("flat")
                        def fazer():
                            with session_scope() as s:
                                lixeira_service.enviar_para_lixeira(s, devolucao_id)
                            ui.notify("Movida para a lixeira")
                            confirm.close()
                            dlg.close()
                            if on_save:
                                on_save()
                        ui.button("Mover", on_click=fazer).classes("bg-red text-white")
                confirm.open()

            ui.button("Excluir", icon="delete", on_click=_excluir).props("flat color=red")
            ui.button("Editar", icon="edit",
                      on_click=lambda: (dlg.close(),
                                         abrir_form_devolucao(devolucao_id, on_save=on_save))) \
                .classes("bg-primary text-white")

    dlg.open()
```

- [ ] **Step 2: Commit**

```bash
git add app/ui/components/detalhe_devolucao.py
git commit -m "feat(ui): modal de detalhe com linha do tempo e acoes"
```

---

### Task 20: Página Lixeira

**Files:**
- Create: `app/ui/pages/lixeira.py`

- [ ] **Step 1: Implementar**

```python
from nicegui import ui

from app.db import session_scope
from app.repositories import devolucoes_repo
from app.services import lixeira_service


def render():
    from app.ui.layout import montar_layout
    montar_layout("Lixeira")

    container = ui.column().classes("w-full max-w-3xl")

    def recarregar():
        container.clear()
        with container:
            ui.label("Devoluções na lixeira (auto-expurgo em 30 dias)") \
                .classes("text-h6")
            with session_scope() as s:
                itens = devolucoes_repo.listar_lixeira(s)
                dados = [(d.id, d.marca.nome, d.produto_modelo,
                          d.data_devolucao.strftime("%d/%m/%Y"),
                          d.excluido_em.strftime("%d/%m/%Y") if d.excluido_em else "")
                         for d in itens]

            if not dados:
                ui.label("Lixeira vazia.").classes("text-grey-7")
                return

            for did, marca, modelo, data_dev, excluido in dados:
                with ui.card().classes("w-full"):
                    with ui.row().classes("items-center justify-between w-full"):
                        with ui.column():
                            ui.label(f"{marca} · {modelo}").classes("font-bold")
                            ui.label(f"Devolução: {data_dev}   Excluída: {excluido}") \
                                .classes("text-caption text-grey-7")
                        with ui.row():
                            def _restaurar(did=did):
                                with session_scope() as s:
                                    lixeira_service.restaurar(s, did)
                                ui.notify("Restaurada")
                                recarregar()

                            def _apagar_definitivo(did=did):
                                with ui.dialog() as dlg, ui.card():
                                    ui.label("Apagar definitivamente? Não tem volta.")
                                    with ui.row():
                                        ui.button("Cancelar", on_click=dlg.close).props("flat")
                                        def fazer():
                                            with session_scope() as s:
                                                # Reaproveita a lógica de expurgo para essa devolução:
                                                from datetime import datetime, timedelta
                                                from app.constants import LIXEIRA_DIAS
                                                d = devolucoes_repo.buscar_por_id(s, did)
                                                if d:
                                                    d.excluido_em = datetime.utcnow() - timedelta(days=LIXEIRA_DIAS + 1)
                                                lixeira_service.expurgar_antigas(s)
                                            ui.notify("Apagada definitivamente")
                                            dlg.close()
                                            recarregar()
                                        ui.button("Apagar", on_click=fazer).classes("bg-red text-white")
                                dlg.open()

                            ui.button("Restaurar", icon="restore",
                                      on_click=_restaurar).props("flat")
                            ui.button("Apagar agora", icon="delete_forever",
                                      on_click=_apagar_definitivo).props("flat color=red")

    recarregar()
```

- [ ] **Step 2: Commit**

```bash
git add app/ui/pages/lixeira.py
git commit -m "feat(ui): pagina Lixeira com restaurar e apagar definitivo"
```

---

### Task 21: Página Configurações

**Files:**
- Create: `app/ui/pages/configuracoes.py`

- [ ] **Step 1: Implementar**

```python
from pathlib import Path

from nicegui import ui

from app.config import Config
from app.services import backup_service


def render():
    from app.ui.layout import montar_layout
    montar_layout("Configurações")

    cfg = Config.load()

    with ui.column().classes("w-full max-w-3xl gap-4"):
        ui.label("Dados").classes("text-h6")
        ui.label(f"Pasta de dados: {cfg.data_dir}").classes("text-caption")
        ui.label(f"Banco: {cfg.db_path}").classes("text-caption")
        ui.label(f"Anexos: {cfg.anexos_dir}").classes("text-caption")

        ui.separator()
        ui.label("Backup").classes("text-h6")

        i_pasta = ui.input("Pasta de backup",
                            value=str(cfg.backup_folder)).classes("w-full")
        i_freq = ui.select(
            {"on_close": "Ao fechar o app",
             "daily": "Diariamente (futuro)",
             "weekly": "Semanalmente (futuro)",
             "manual": "Apenas manual"},
            value=cfg.backup_frequency,
            label="Frequência",
        ).classes("w-full")
        i_ret = ui.number("Manter últimos N backups",
                           value=cfg.backup_retention, min=1).classes("w-full")

        def salvar_cfg():
            cfg.backup_folder = Path(i_pasta.value)
            cfg.backup_frequency = i_freq.value
            cfg.backup_retention = int(i_ret.value or 30)
            cfg.save()
            ui.notify("Configurações salvas", type="positive")

        ui.button("Salvar", on_click=salvar_cfg).classes("bg-primary text-white")

        ui.separator()
        ui.label("Backup manual").classes("text-h6")
        def fazer_backup():
            try:
                caminho = backup_service.criar_backup()
                ui.notify(f"Backup criado: {caminho.name}", type="positive")
                recarregar_lista_backups()
            except Exception as e:
                ui.notify(f"Erro: {e}", type="negative")

        ui.button("Fazer backup agora", on_click=fazer_backup) \
            .classes("bg-primary text-white")

        lista_container = ui.column().classes("w-full")

        def recarregar_lista_backups():
            lista_container.clear()
            with lista_container:
                ui.label("Últimos backups").classes("text-subtitle1")
                infos = backup_service.listar_backups()
                if not infos:
                    ui.label("Nenhum backup ainda.").classes("text-grey-7")
                for info in infos[:10]:
                    ui.label(
                        f"• {info.criado_em.strftime('%d/%m/%Y %H:%M')} "
                        f"· {info.tamanho_bytes / 1024:.1f} KB "
                        f"· {info.caminho.name}"
                    ).classes("text-caption")

        recarregar_lista_backups()
```

- [ ] **Step 2: Commit**

```bash
git add app/ui/pages/configuracoes.py
git commit -m "feat(ui): pagina Configuracoes com backup manual e preferencias"
```

---

## FASE 5 — Integração final, seed e docs

### Task 22: Validação manual ponta a ponta

Não é código novo — é executar o fluxo completo e confirmar que tudo funciona junto.

- [ ] **Step 1: Subir o app**

```bash
uv run python main.py
```
Esperado: janela abre na tela de Devoluções (vazia).

- [ ] **Step 2: Criar marca**

Menu → Marcas → "+ Nova marca" → "Vizzano", forma padrão "Abate na nota". Salvar.

- [ ] **Step 3: Criar devolução**

Menu → Devoluções → "+ Nova Devolução". Preencher: marca Vizzano, modelo "Sandália 123", data hoje, salvar. Conferir que apareceu na lista com badges 🔴 / ⚪ / 💸.

- [ ] **Step 4: Abrir detalhe e mudar status via edição**

Clicar na devolução → "Editar" → mudar status para "Sinalizado" → salvar. Conferir que badge ficou 🟡 e que a linha do tempo registrou a transição.

- [ ] **Step 5: Anexar arquivo PDF**

(criar `nota.pdf` qualquer no desktop antes) Editar devolução → upload foto principal não, mas: vamos validar via outro caminho — abrir detalhe e confirmar que a foto aparece se carregada. Para PDF normal, ainda não temos UI dedicada (fica como melhoria futura). Por ora valida pela seção Anexos do detalhe se houver.

- [ ] **Step 6: Enviar para lixeira e restaurar**

No detalhe → "Excluir" → confirmar. Vai pra Lixeira. Restaurar de volta.

- [ ] **Step 7: Fechar app → conferir backup criado**

Fechar a janela. Reabrir. Em Configurações, ver lista de backups — deve ter ao menos 1.

- [ ] **Step 8: Se algum passo falhou, registrar como issue no README e corrigir antes de seguir**

---

### Task 23: Adicionar UI de upload de anexos extras no detalhe

Durante a Task 22 vai ficar claro que falta um caminho para anexar PDFs (NF de abatimento etc.) **depois** da devolução criada. Vamos adicionar isso.

**Files:**
- Modify: `app/ui/components/detalhe_devolucao.py:Anexos`

- [ ] **Step 1: Adicionar bloco de upload acima da lista de anexos no detalhe**

Localizar o trecho:

```python
        ui.separator()
        ui.label("Anexos").classes("text-subtitle2")
        if not dados["anexos"]:
            ui.label("Nenhum anexo.").classes("text-grey-7")
```

E substituir por:

```python
        ui.separator()
        ui.label("Anexos").classes("text-subtitle2")

        def _on_upload_extra(e):
            from pathlib import Path
            from tempfile import mkdtemp
            tmp = Path(mkdtemp()) / e.name  # preserva nome original
            tmp.write_bytes(e.content.read())
            try:
                with session_scope() as s:
                    anexo_service.salvar_anexo(s, devolucao_id, tmp,
                                                como_principal=False)
                ui.notify("Anexo adicionado")
                dlg.close()
                abrir_detalhe(devolucao_id, on_save=on_save)
            except ValueError as err:
                ui.notify(str(err), type="negative")

        ui.upload(label="+ Adicionar anexo",
                  on_upload=_on_upload_extra, auto_upload=True) \
            .props('accept=".pdf,.jpg,.jpeg,.png,.webp"').classes("w-full")

        if not dados["anexos"]:
            ui.label("Nenhum anexo ainda.").classes("text-grey-7")
```

- [ ] **Step 2: Smoke test**

```bash
uv run python main.py
```
Anexar um PDF qualquer pelo detalhe; conferir que aparece na lista.

- [ ] **Step 3: Commit**

```bash
git add app/ui/components/detalhe_devolucao.py
git commit -m "feat(ui): upload de anexos extras direto no detalhe"
```

---

### Task 24: Script de seed para dev/demo

**Files:**
- Create: `scripts/seed_demo.py`

- [ ] **Step 1: Criar script**

```python
"""Popula o banco com dados de exemplo (para testar manualmente).
Uso: uv run python scripts/seed_demo.py
"""
from datetime import date, timedelta

from app.constants import (DestinoFisico, FormaRessarcimento, StatusProcesso)
from app.db import init_engine, session_scope
from app.repositories import marcas_repo
from app.services import devolucao_service


def main():
    init_engine()
    with session_scope() as s:
        if marcas_repo.listar(s):
            print("Já há marcas cadastradas. Pulei o seed.")
            return

        viz = marcas_repo.criar(s, nome="Vizzano",
                                 forma_padrao=FormaRessarcimento.ABATE_NOTA,
                                 observacoes="Rep: João — 47 99999-0000")
        oly = marcas_repo.criar(s, nome="Olympikus",
                                 forma_padrao=FormaRessarcimento.DINHEIRO,
                                 observacoes="Portal online, prazo de 2 anos")
        viv = marcas_repo.criar(s, nome="Vivara",
                                 forma_padrao=FormaRessarcimento.TROCA,
                                 observacoes="Joias: cliente fica aguardando")
        s.flush()

        hoje = date.today()
        devolucao_service.criar(
            s, marca_id=viz.id, produto_modelo="Sandália Salto 8cm",
            produto_referencia="VZ-4521", data_devolucao=hoje - timedelta(days=8),
            defeito_descricao="solado descolando", valor_custo=89.90,
            nf_origem="1234",
            status_processo=StatusProcesso.SINALIZADO,
        )
        devolucao_service.criar(
            s, marca_id=oly.id, produto_modelo="Tênis Corre 3",
            produto_referencia="OLY-9012", data_devolucao=hoje - timedelta(days=12),
            data_compra_original=hoje - timedelta(days=120),
            valor_custo=349.90,
            status_processo=StatusProcesso.PENDENTE_RESSARCIMENTO,
            destino_fisico=DestinoFisico.ENVIADO,
        )
        devolucao_service.criar(
            s, marca_id=viv.id, produto_modelo="Anel ouro 18k",
            data_devolucao=hoje - timedelta(days=18),
            cliente_nome="Maria Silva", cliente_contato="47 98888-1111",
            cliente_aguardando_retorno=True,
            valor_custo=2400.00,
            status_processo=StatusProcesso.PENDENTE_RESSARCIMENTO,
            destino_fisico=DestinoFisico.RECOLHIDO,
        )
        devolucao_service.criar(
            s, marca_id=viz.id, produto_modelo="Bota Cano Longo",
            data_devolucao=hoje - timedelta(days=28),
            status_processo=StatusProcesso.RESSARCIDO,
            nf_abatimento="5678",
        )
    print("Seed concluído.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar (mas só num ambiente dev — vai criar/escrever no AppData!)**

Recomendação: setar `SIMONETTO_DATA_DIR` para uma pasta de teste antes:

```bash
SIMONETTO_DATA_DIR=./.dev_data uv run python scripts/seed_demo.py
SIMONETTO_DATA_DIR=./.dev_data uv run python main.py
```

Conferir que aparecem 4 devoluções com badges corretos.

- [ ] **Step 3: Commit**

```bash
git add scripts/seed_demo.py
git commit -m "feat(scripts): seed_demo com 3 marcas e 4 devolucoes de exemplo"
```

---

### Task 25: README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Escrever README**

```markdown
# Simonetto Devoluções

Gerenciador desktop de devoluções de produtos da Loja Simonetto.

## Requisitos

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

## Instalação

```bash
uv sync
```

## Rodar

```bash
uv run python main.py
```

A primeira execução cria a pasta de dados em `%LOCALAPPDATA%\SimonettoDevolucoes\`.

## Rodar com dados de exemplo (dev)

```bash
SIMONETTO_DATA_DIR=./.dev_data uv run python scripts/seed_demo.py
SIMONETTO_DATA_DIR=./.dev_data uv run python main.py
```

## Testes

```bash
uv run pytest -v
uv run pytest --cov=app/services --cov=app/repositories
```

## Estrutura

- `app/models/` — modelos SQLAlchemy
- `app/repositories/` — acesso ao banco (CRUD puro)
- `app/services/` — regras de negócio
- `app/ui/` — interface NiceGUI
- `docs/superpowers/specs/` — spec do produto
- `docs/superpowers/plans/` — plano de implementação

## Backup

- Automático ao fechar o app
- Configurável em **Configurações → Backup**
- Para apontar pro OneDrive: salvar a pasta de backup como
  `C:\Users\<você>\OneDrive\Devoluções\Backups`

## Restaurar de backup

1. Fechar o app
2. Extrair o `.zip` desejado sobre `%LOCALAPPDATA%\SimonettoDevolucoes\`
3. Reabrir o app
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README com instrucoes de instalacao, uso e backup"
```

---

## Conclusão

Ao terminar a Task 25, o app está pronto para uso real diário:

- ✅ Cadastro completo de devoluções com 3 eixos independentes
- ✅ Anexos com validação e thumbnail
- ✅ Lixeira com 30 dias de retenção
- ✅ Backup automático ao fechar
- ✅ Banner de alerta de backup desatualizado
- ✅ Expurgo automático ao abrir o app
- ✅ Cobertura de testes nos services e repositórios

### Próximas evoluções (v2, fora do escopo deste plano)

- Empacotamento `.exe` via PyInstaller
- Atalho na área de trabalho
- Opções adicionais de frequência de backup (diário, semanal)
- Exportação CSV
- Acesso pelo celular (rodar como serviço local + ngrok, ou migrar pra hospedagem)
