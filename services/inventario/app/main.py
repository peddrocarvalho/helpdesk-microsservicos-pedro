from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import DOCS_ATIVA, DADOS_EXEMPLO, validar_configuracao
from app.database import Base, SessionLocal, engine
from app.inventario import modelos
from app.inventario.dados_iniciais import carregar
from app.inventario.rotas import router as inventario_router


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    validar_configuracao()
    Base.metadata.create_all(bind=engine)

    if DADOS_EXEMPLO:
        with SessionLocal() as db:
            carregar(db)

    yield


app = FastAPI(
    title="HelpDesk TI - Microsservi?o de Invent?rio",
    version="1.0.0",
    lifespan=ciclo_de_vida,
    docs_url="/docs" if DOCS_ATIVA else None,
    redoc_url=None,
    openapi_url="/openapi.json" if DOCS_ATIVA else None,
)


app.include_router(inventario_router)


@app.get("/saude", tags=["Sa?de"])
def saude():
    return {"status": "ok", "servico": "inventario"}
