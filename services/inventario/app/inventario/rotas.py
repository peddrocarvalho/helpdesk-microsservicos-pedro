from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.seguranca import exigir_perfil, usuario_atual
from app.database import get_db
from app.inventario import servico
from app.inventario.esquemas import AtivoCriar, AtivoSaida

router = APIRouter(prefix="/ativos", tags=["Invent?rio"])


@router.post(
    "",
    response_model=AtivoSaida,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_perfil("tecnico", "admin"))],
)
def criar_ativo(
    dados: AtivoCriar,
    db: Session = Depends(get_db),
):
    try:
        return servico.criar(db, dados)
    except servico.AtivoDuplicado as erro:
        raise HTTPException(status_code=409, detail=str(erro))


@router.get(
    "",
    response_model=list[AtivoSaida],
    dependencies=[Depends(usuario_atual)],
)
def listar_ativos(
    setor: str | None = Query(None, max_length=80),
    db: Session = Depends(get_db),
):
    return servico.listar(db, setor)


@router.get(
    "/{ativo_id}",
    response_model=AtivoSaida,
    dependencies=[Depends(usuario_atual)],
)
def obter_ativo(
    ativo_id: int,
    db: Session = Depends(get_db),
):
    try:
        return servico.obter(db, ativo_id)
    except servico.AtivoNaoEncontrado as erro:
        raise HTTPException(status_code=404, detail=str(erro))
