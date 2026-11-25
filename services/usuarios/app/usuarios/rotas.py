import time
from collections import defaultdict
from threading import Lock

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app.auth import senhas
from app.auth.seguranca import (
    criar_token,
    exigir_perfil,
    usuario_atual,
)
from app.config import LOGIN_JANELA_SEGUNDOS, LOGIN_MAX_FALHAS
from app.database import get_db
from app.usuarios import servico
from app.usuarios.esquemas import (
    Login,
    Perfil,
    TokenSaida,
    UsuarioCriar,
    UsuarioPublico,
    UsuarioSaida,
)

auth_router = APIRouter(prefix="/auth", tags=["Autenticação"])
router = APIRouter(prefix="/usuarios", tags=["Usuários"])

_falhas: dict[str, list[float]] = defaultdict(list)
_trava = Lock()


def _recentes(chave: str, agora: float):
    _falhas[chave] = [
        instante
        for instante in _falhas[chave]
        if agora - instante < LOGIN_JANELA_SEGUNDOS
    ]
    return _falhas[chave]


def _bloqueado(chave: str):
    with _trava:
        return len(_recentes(chave, time.monotonic())) >= LOGIN_MAX_FALHAS


def _registrar_falha(chave: str):
    with _trava:
        _recentes(chave, time.monotonic()).append(time.monotonic())


def _limpar_falhas(chave: str):
    with _trava:
        _falhas.pop(chave, None)


@auth_router.post("/login", response_model=TokenSaida)
def login(
    dados: Login,
    request: Request,
    db: Session = Depends(get_db),
):
    email = dados.email.lower()
    host = request.client.host if request.client else "-"
    chave = f"{email}|{host}"

    if _bloqueado(chave):
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas. Tente de novo em alguns minutos.",
        )

    usuario = servico.buscar_por_email(db, email)

    senha_ok = senhas.conferir(
        dados.senha,
        usuario.senha_hash if usuario else senhas.HASH_FALSO,
    )

    if not usuario or not senha_ok or not usuario.ativo:
        _registrar_falha(chave)
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha inválidos.",
        )

    _limpar_falhas(chave)

    token, expira = criar_token(usuario.id, usuario.perfil)

    return TokenSaida(
        access_token=token,
        expira_em=expira,
        usuario=UsuarioSaida.model_validate(usuario),
    )


@auth_router.get("/eu", response_model=UsuarioSaida)
def quem_sou_eu(
    identidade=Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    usuario = servico.buscar_por_id(db, identidade["id"])

    if usuario is None or not usuario.ativo:
        raise HTTPException(status_code=401, detail="Usuário não autenticado.")

    return usuario


@router.post(
    "",
    response_model=UsuarioSaida,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_perfil("admin"))],
)
def criar_usuario(
    dados: UsuarioCriar,
    db: Session = Depends(get_db),
):
    usuario = servico.criar(db, dados)

    if usuario is None:
        raise HTTPException(
            status_code=409,
            detail="Já existe um usuário com este e-mail.",
        )

    return usuario


@router.get(
    "",
    response_model=list[UsuarioPublico],
)
def listar_usuarios(
    perfil: Perfil | None = None,
    identidade=Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    return servico.listar(db, perfil)


@router.get(
    "/{usuario_id}",
    response_model=UsuarioPublico,
)
def obter_usuario(
    usuario_id: int,
    identidade=Depends(usuario_atual),
    db: Session = Depends(get_db),
):
    usuario = servico.buscar_por_id(db, usuario_id)

    if usuario is None or not usuario.ativo:
        raise HTTPException(
            status_code=404,
            detail=f"Usuário {usuario_id} não encontrado.",
        )

    return usuario
