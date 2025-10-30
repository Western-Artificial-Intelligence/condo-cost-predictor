from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

_engine = None
_SessionLocal = None

def _init():
    global _engine, _SessionLocal
    if settings.DATABASE_URL:
        _engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

_init()

def is_db_enabled() -> bool:
    return _SessionLocal is not None

@contextmanager
def get_session():
    if not is_db_enabled():
        yield None
        return
    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
