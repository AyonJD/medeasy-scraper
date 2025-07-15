from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config_vps import Config
from loguru import logger

# Create database engine
engine = create_engine(
    Config.DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they are registered
        from database.models import Medicine, ScrapingProgress, ScrapingLog
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("PostgreSQL database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

def check_db_connection():
    """Check database connection"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("PostgreSQL database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 