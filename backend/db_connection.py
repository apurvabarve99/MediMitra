import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Lightweight database connection pool"""
    _pool = None
    
    @classmethod
    def initialize_pool(cls, minconn=1, maxconn=10):
        """Initialize connection pool"""
        if cls._pool is None:
            try:
                cls._pool = SimpleConnectionPool(
                    minconn, maxconn,
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    database=settings.DB_NAME,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD
                )
                logger.info("Database connection pool initialized")
            except Exception as e:
                logger.error(f"Failed to initialize connection pool: {e}")
                raise
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get connection from pool"""
        if cls._pool is None:
            cls.initialize_pool()
        
        conn = cls._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cls._pool.putconn(conn)
    
    @classmethod
    @contextmanager
    def get_cursor(cls, cursor_factory=RealDictCursor):
        """Get cursor with automatic cleanup"""
        with cls.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()

# Initialize pool on import
DatabaseConnection.initialize_pool()
