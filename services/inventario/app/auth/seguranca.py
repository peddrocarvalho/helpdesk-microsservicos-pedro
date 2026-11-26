import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO

esquema = HTTPBearer(auto_error=False)

NAO_AUTENTICADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Fa?a login para continuar.",
    headers={"WWW-Authenticate": "Bearer"},
)

PERFIS = {"solicitante", "tecnico", "admin"}


def usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(esquema),
):
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise NAO_AUTENTICADO

    try:
        dados = jwt.decode(
            credenciais.credentials,
            JWT_SEGREDO,
            algorithms=[JWT_ALGORITMO],
            issuer=JWT_EMISSOR,
            options={"require": ["exp", "iat", "sub", "iss", "perfil"]},
        )

        usuario_id = int(dados["sub"])
        perfil = dados["perfil"]

        if usuario_id <= 0 or perfil not in PERFIS:
            raise ValueError("Claims inv?lidas.")

        return {"id": usuario_id, "perfil": perfil}

    except (jwt.PyJWTError, ValueError, TypeError):
        raise NAO_AUTENTICADO


def exigir_perfil(*perfis_permitidos: str):
    def verificar(usuario: dict = Depends(usuario_atual)):
        if usuario["perfil"] not in perfis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Voc? n?o tem permiss?o para esta a??o.",
            )
        return usuario

    return verificar
