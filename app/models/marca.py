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

    if False:  # pragma: no cover – forward-ref guard until Devolucao is defined
        devolucoes: Mapped[list["Devolucao"]] = relationship(  # type: ignore
            back_populates="marca", cascade="all"
        )
