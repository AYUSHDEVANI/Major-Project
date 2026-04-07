from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.history import Base

# Local SQLite DB for simplicity
DATABASE_URL = "sqlite:///./maintenance.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
