from fastapi import FastAPI

from app.config import validar_configuracao
from app.database import Base, SessionLocal, engine
from app.usuarios import modelos
from app.usuarios.dados_iniciais import carregar
from app.usuarios.rotas import auth_router, router


validar_configuracao()

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    carregar(db)


app = FastAPI(
    title="Microsserviço de Usuários",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(router)


@app.get("/saude")
def saude():
    return {
        "servico": "usuarios",
        "status": "online",
    }
