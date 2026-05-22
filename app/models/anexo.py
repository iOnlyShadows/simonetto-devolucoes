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
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    tamanho_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    devolucao: Mapped["Devolucao"] = relationship(back_populates="anexos")  # type: ignore
