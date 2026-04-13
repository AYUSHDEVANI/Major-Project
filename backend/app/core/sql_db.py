from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.history import Base
from app.core.config import settings

# Import models so their tables are registered with Base.metadata
import app.models.user  # noqa: F401
import app.models.chat  # noqa: F401

# Database engine initialization
# check_same_thread is only required for SQLite
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
db_type = "SQLITE" if is_sqlite else "POSTGRESQL"
print(f"--- INITIALIZING DATABASE (Type: {db_type}) ---")

connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args=connect_args
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
