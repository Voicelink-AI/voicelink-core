"""
Database connection and table creation for VoiceLink Core
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def create_tables():
    """Create database tables"""
    try:
        # For now, we'll use file-based storage
        # In the future, this would create PostgreSQL/SQLite tables
        
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different data types
        (data_dir / "meetings").mkdir(exist_ok=True)
        (data_dir / "audio").mkdir(exist_ok=True)
        (data_dir / "transcripts").mkdir(exist_ok=True)
        
        logger.info("Database tables/directories created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
