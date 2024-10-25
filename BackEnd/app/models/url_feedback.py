
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from app.config import settings
from sqlalchemy.engine.url import URL
from app.logger import setup_logger

logger = setup_logger(__name__)

# Create database engine
engine = create_engine(settings.DATABASE_URL,pool_pre_ping=True,pool_recycle=3600,echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class URLFeedback(Base):
    __tablename__ = "url_feedback"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), index=True)  # Maximum URL length
    url_hash = Column(String(32), unique=True, index=True)  # MD5 hash length
    normalized_url = Column(String(2048))
    type = Column(String(10))  # 'malicious' or 'benign'
    timestamp = Column(DateTime, default=datetime.utcnow)
    used_in_training = Column(Boolean, default=False)
    confidence = Column(Float)
    feedback_count = Column(Integer, default=1)
    conflicting_feedbacks = Column(Integer, default=0)
    last_feedback_type = Column(String(1024))  # History of feedback types
    consensus_reached = Column(Boolean, default=False)

    class Config:
        orm_mode = True

def init_db():
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()