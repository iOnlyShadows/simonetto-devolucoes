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
