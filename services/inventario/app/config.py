import os

from dotenv import load_dotenv
from pathlib import Path

_env_local = next(
    (p / ".env" for p in Path(__file__).resolve().parents if (p / ".env").is_file()),
    None,
)
if _env_local:
    load_dotenv(_env_local)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventario.db")
JWT_SEGREDO = os.getenv("JWT_SEGREDO", "")
JWT_ALGORITMO = "HS256"
JWT_EMISSOR = "helpdesk-ti"
DOCS_ATIVA = os.getenv("DOCS", "1") == "1"
DADOS_EXEMPLO = os.getenv("DADOS_EXEMPLO", "1") == "1"


def validar_configuracao():
    if len(JWT_SEGREDO) < 32:
        raise RuntimeError("JWT_SEGREDO precisa ter pelo menos 32 caracteres.")

