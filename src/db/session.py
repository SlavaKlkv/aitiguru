from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.settings import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
)
