
import mysql.connector
from app.config import settings
from app.logger import setup_logger

logger = setup_logger(__name__)

def create_database():
    try:
        conn = mysql.connector.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        cursor = conn.cursor()

        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}")
        cursor.execute(f"USE {settings.DB_NAME}")

        logger.info(f"Database '{settings.DB_NAME}' created successfully")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise

if __name__ == "__main__":
    create_database()
