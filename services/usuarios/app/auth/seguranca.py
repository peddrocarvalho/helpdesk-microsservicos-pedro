
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import (
    JWT_ALGORITMO,
    JWT_EMISSOR,
    JWT_SEGREDO,
    TOKEN_MINUTOS,
)
from app.database import get_db
from app.usuarios.modelos import Usuario


esquema = HTTPBearer(auto_error=False)

NAO_AUTENTICADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Faça login para continuar.",
    headers={"WWW-Authenticate": "Bearer"},
)


def criar_token(usuario_id: int, perfil: str):
    agora = datetime.now(timezone.utc)
    expira = agora + timedelta(minutes=TOKEN_MINUTOS)

    dados = {
        "sub": str(usuario_id),
        "perfil": perfil,
        "iat": agora,
        "exp": expira,
        "iss": JWT_EMISSOR,
    }

    token = jwt.encode(
        dados,
        JWT_SEGREDO,
        algorithm=JWT_ALGORITMO,
    )

    return token, expira


def usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(esquema),
    db: Session = Depends(get_db),
):
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise NAO_AUTENTICADO

    try:
        dados = jwt.decode(
            credenciais.credentials,
            JWT_SEGREDO,
            algorithms=[JWT_ALGORITMO],
            issuer=JWT_EMISSOR,
            options={
                "require": ["exp", "iat", "sub", "iss", "perfil"]
            },
        )

        usuario_id = int(dados["sub"])
        perfil_token = dados["perfil"]

        if perfil_token not in ("solicitante", "tecnico", "admin"):
            raise ValueError()

        usuario = db.get(Usuario, usuario_id)

        if (
            usuario is None
            or not usuario.ativo
            or usuario.perfil != perfil_token
        ):
            raise NAO_AUTENTICADO

        return {
            "id": usuario.id,
            "perfil": usuario.perfil,
        }

    except (jwt.PyJWTError, ValueError, KeyError):
        raise NAO_AUTENTICADO


def exigir_perfil(*perfis: str):
    def verificar(usuario=Depends(usuario_atual)):
        if usuario["perfil"] not in perfis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para esta ação.",
            )
        return usuario

    return verificar
