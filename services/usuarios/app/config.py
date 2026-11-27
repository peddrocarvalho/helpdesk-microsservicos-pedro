import os

from dotenv import load_dotenv
from pathlib import Path

_env_local = next(
    (p / ".env" for p in Path(__file__).resolve().parents if (p / ".env").is_file()),
    None,
)
if _env_local:
    load_dotenv(_env_local)

JWT_SEGREDO = os.getenv("JWT_SEGREDO", "")
JWT_ALGORITMO = "HS256"
JWT_EMISSOR = "helpdesk-ti"
TOKEN_MINUTOS = int(os.getenv("TOKEN_MINUTOS", "60"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./usuarios.db"
)

LOGIN_MAX_FALHAS = int(os.getenv("LOGIN_MAX_FALHAS", "5"))
LOGIN_JANELA_SEGUNDOS = int(os.getenv("LOGIN_JANELA_SEGUNDOS", "300"))


def validar_configuracao():
    if len(JWT_SEGREDO) < 32:
        raise RuntimeError(
            "JWT_SEGREDO precisa ter pelo menos 32 caracteres."
        )
