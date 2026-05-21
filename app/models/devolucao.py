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
