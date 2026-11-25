import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.senhas import gerar_hash
from app.usuarios.modelos import Usuario


DADOS_EXEMPLO = os.getenv("DADOS_EXEMPLO", "0") == "1"
SENHA_EXEMPLO = os.getenv("SENHA_EXEMPLO", "")


USUARIOS_INICIAIS = [
    ("Admin TI", "admin@empresa.com", "admin"),
    ("Ana Souza", "ana@empresa.com", "solicitante"),
    ("Bruno Lima", "bruno@empresa.com", "solicitante"),
    ("Carla Dias", "carla@empresa.com", "tecnico"),
    ("Diego Rocha", "diego@empresa.com", "tecnico"),
]


def carregar(db: Session):
    if not DADOS_EXEMPLO:
        return

    if not SENHA_EXEMPLO:
        raise RuntimeError(
            "SENHA_EXEMPLO precisa ser configurada para carregar os dados de exemplo."
        )

    usuario_existente = db.scalar(
        select(Usuario.id).limit(1)
    )

    if usuario_existente is not None:
        return

    for nome, email, perfil in USUARIOS_INICIAIS:
        usuario = Usuario(
            nome=nome,
            email=email,
            perfil=perfil,
            senha_hash=gerar_hash(SENHA_EXEMPLO),
            ativo=True,
        )
        db.add(usuario)

    db.commit()