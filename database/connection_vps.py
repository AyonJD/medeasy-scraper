from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config_vps import Config

# Create engine for VPS database (lazy loading to avoid import errors)
_engine = None
_SessionLocal = None

def get_engine():
    """Get VPS database engine with lazy loading"""
    global _engine
    if _engine is None:
        try:
            _engine = create_engine(Config.DATABASE_URL)
        except Exception as e:
            raise Exception(f"Failed to create VPS database engine: {e}. Make sure psycopg2 is installed for PostgreSQL support.")
    return _engine

def get_session_local():
    """Get VPS session factory with lazy loading"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

# For backward compatibility
engine = None  # Will be set when get_engine() is called
SessionLocal = None  # Will be set when get_session_local() is called

def get_db():
    """Get database session for VPS"""
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close() 