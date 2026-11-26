from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.inventario import repositorio
from app.inventario.esquemas import AtivoCriar
from app.inventario.modelos import Ativo


class AtivoDuplicado(Exception):
    pass


class AtivoNaoEncontrado(Exception):
    pass


def criar(db: Session, dados: AtivoCriar) -> Ativo:
    patrimonio = dados.patrimonio

    if repositorio.buscar_por_patrimonio(db, patrimonio):
        raise AtivoDuplicado(
            "J? existe um ativo com este patrim?nio."
        )

    ativo = Ativo(**dados.model_dump())

    try:
        return repositorio.salvar(db, ativo)
    except IntegrityError as erro:
        db.rollback()
        raise AtivoDuplicado(
            "J? existe um ativo com este patrim?nio."
        ) from erro


def obter(db: Session, ativo_id: int) -> Ativo:
    ativo = repositorio.buscar_por_id(db, ativo_id)

    if ativo is None:
        raise AtivoNaoEncontrado(
            f"Ativo {ativo_id} n?o encontrado."
        )

    return ativo


def listar(db: Session, setor: str | None = None) -> list[Ativo]:
    return repositorio.listar(db, setor)
