from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import DATABASE_URL

argumentos = {}
if DATABASE_URL.startswith("sqlite"):
    argumentos["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=argumentos)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
