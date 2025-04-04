from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Configuración adicional para manejar tipos específicos de PostgreSQL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # Evita problemas con ciertos tipos de datos de PostgreSQL
    connect_args={
        "options": "-c client_encoding=utf8"
    },
    # Configura el pool de conexiones para un mejor rendimiento
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()