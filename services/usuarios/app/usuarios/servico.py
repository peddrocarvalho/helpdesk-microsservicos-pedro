
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import senhas
from app.usuarios.modelos import Usuario
from app.usuarios.esquemas import UsuarioCriar


def buscar_por_email(db: Session, email: str):
    return db.scalar(
        select(Usuario).where(Usuario.email == email.lower())
    )


def buscar_por_id(db: Session, usuario_id: int):
    return db.get(Usuario, usuario_id)


def criar(db: Session, dados: UsuarioCriar):
    email = dados.email.lower()

    if buscar_por_email(db, email):
        return None

    usuario = Usuario(
        nome=dados.nome,
        email=email,
        perfil=dados.perfil,
        senha_hash=senhas.gerar_hash(dados.senha),
    )

    db.add(usuario)

    try:
        db.commit()
        db.refresh(usuario)
        return usuario
    except IntegrityError:
        db.rollback()
        return None


def listar(db: Session, perfil: str | None = None):
    consulta = select(Usuario).order_by(Usuario.id)

    if perfil:
        consulta = consulta.where(Usuario.perfil == perfil)

    return list(db.scalars(consulta))
