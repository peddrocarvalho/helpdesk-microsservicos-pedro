import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

JWT_SEGREDO = os.getenv("JWT_SEGREDO", "")
USUARIOS_URL = os.getenv("USUARIOS_URL", "http://localhost:8001").rstrip("/")
INVENTARIO_URL = os.getenv("INVENTARIO_URL", "http://localhost:8002").rstrip("/")
