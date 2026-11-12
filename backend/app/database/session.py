from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from backend.app.config.settings import settings

db_url = settings.DATABASE_URL
if isinstance(db_url, str) and db_url.startswith("sqlite+aiosqlite"):
    sync_db_url = db_url.replace("sqlite+aiosqlite", "sqlite", 1)
    engine = create_engine(
        sync_db_url,
        echo=False,
        connect_args={"check_same_thread": False}
    )
elif db_url.startswith("sqlite"):
    engine = create_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(db_url, echo=False, pool_pre_ping=True)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()