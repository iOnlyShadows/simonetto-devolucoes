from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HistoricoStatus(Base):
    __tablename__ = "historico_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    devolucao_id: Mapped[int] = mapped_column(ForeignKey("devolucoes.id"), nullable=False)
    campo: Mapped[str] = mapped_column(String(40), nullable=False)
    valor_anterior: Mapped[Optional[str]] = mapped_column(String(60))
    valor_novo: Mapped[str] = mapped_column(String(60), nullable=False)
    observacao: Mapped[Optional[str]] = mapped_column(Text)
    data: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    devolucao: Mapped["Devolucao"] = relationship(back_populates="historicos")  # type: ignore
