import os
from pathlib import Path
from dotenv import load_dotenv

_env_local = next(
    (p / ".env" for p in Path(__file__).resolve().parents if (p / ".env").is_file()),
    None,
)
if _env_local:
    load_dotenv(_env_local)

JWT_SEGREDO = os.getenv("JWT_SEGREDO", "")
USUARIOS_URL = os.getenv("USUARIOS_URL", "http://localhost:8001").rstrip("/")
INVENTARIO_URL = os.getenv("INVENTARIO_URL", "http://localhost:8002").rstrip("/")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chamados.db")

