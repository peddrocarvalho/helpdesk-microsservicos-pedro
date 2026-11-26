from sqlalchemy.orm import Session

from app.inventario import repositorio
from app.inventario.esquemas import AtivoCriar
from app.inventario.servico import criar


def carregar(db: Session):
    if repositorio.listar(db):
        return

    ativos = [
        AtivoCriar(
            patrimonio="PAT-0001",
            tipo="computador",
            descricao="Desktop Dell OptiPlex",
            setor="Financeiro",
        ),
        AtivoCriar(
            patrimonio="PAT-0002",
            tipo="impressora",
            descricao="Impressora HP LaserJet",
            setor="RH",
        ),
        AtivoCriar(
            patrimonio="PAT-0003",
            tipo="notebook",
            descricao="Notebook Lenovo ThinkPad",
            setor="TI",
        ),
    ]

    for ativo in ativos:
        criar(db, ativo)
