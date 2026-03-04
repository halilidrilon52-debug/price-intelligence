import psycopg2
import psycopg2.extras
from psycopg2 import pool
import os
import logging
from dotenv import load_dotenv
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime

load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Connection Pool
try:
    connection_pool = pool.SimpleConnectionPool(
        minconn=2,
        maxconn=20,
        dsn=DATABASE_URL,
        connect_timeout=5
    )
    logger.info("✅ Connection pool created successfully!")
except Exception as e:
    logger.error(f"❌ Failed to create connection pool: {e}")
    raise


# Context Manager për Database Connections
@contextmanager
def get_db_connection():
    """Get a database connection from the pool"""
    conn = None
    try:
        conn = connection_pool.getconn()
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            connection_pool.putconn(conn)


class DatabaseManager:
    """Advanced Database Manager Class"""
    
    @staticmethod
    def init_db() -> bool:
        """Initialize database tables"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT,
                        google_id TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Users table created/exists")
                
                # Products table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        url TEXT NOT NULL,
                        title TEXT,
                        description TEXT,
                        image_url TEXT,
                        original_price DECIMAL(10, 2),
                        current_price DECIMAL(10, 2),
                        discount_percentage DECIMAL(5, 2),
                        last_checked TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, url)
                    )
                """)
                logger.info("✅ Products table created/exists")
                
                # Price history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS price_history (
                        id SERIAL PRIMARY KEY,
                        product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                        price DECIMAL(10, 2) NOT NULL,
                        discount_percentage DECIMAL(5, 2),
                        checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Price history table created/exists")
                
                # Notifications table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                        message TEXT NOT NULL,
                        notification_type VARCHAR(50),
                        is_read BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Notifications table created/exists")
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_user_id ON products(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)")
                
                conn.commit()
                cursor.close()
                logger.info("✅ Database initialized successfully!")
                return True
                
        except psycopg2.Error as e:
            logger.error(f"❌ Database initialization error: {e}")
            return False
    
    # ==================== USER OPERATIONS ====================
    
    @staticmethod
    def create_user(email: str, password_hash: str, google_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("""
                    INSERT INTO users (email, password_hash, google_id, created_at, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id, email, created_at
                """, (email, password_hash, google_id))
                user = cursor.fetchone()
                conn.commit()
                logger.info(f"✅ User created: {email}")
                return dict(user) if user else None
        except psycopg2.IntegrityError as e:
            logger.error(f"❌ User already exists: {email}")
            return None
        except psycopg2.Error as e:
            logger.error(f"❌ Error creating user: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("SELECT * FROM users WHERE id = %s AND is_active = TRUE", (user_id,))
                user = cursor.fetchone()
                cursor.close()
                return dict(user) if user else None
        except psycopg2.Error as e:
            logger.error(f"❌ Error fetching user by ID: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("SELECT * FROM users WHERE email = %s AND is_active = TRUE", (email,))
                user = cursor.fetchone()
                cursor.close()
                return dict(user) if user else None
        except psycopg2.Error as e:
            logger.error(f"❌ Error fetching user by email: {e}")
            return None
    
    @staticmethod
    def get_user_by_google_id(google_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Google ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("SELECT * FROM users WHERE google_id = %s AND is_active = TRUE", (google_id,))
                user = cursor.fetchone()
                cursor.close()
                return dict(user) if user else None
        except psycopg2.Error as e:
            logger.error(f"❌ Error fetching user by Google ID: {e}")
            return None
    
    @staticmethod
    def update_user(user_id: int, **kwargs) -> bool:
        """Update user information"""
        try:
            allowed_fields = ['email', 'password_hash', 'is_active']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not updates:
                return False
            
            updates['updated_at'] = datetime.utcnow()
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [user_id]
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE users SET {set_clause} WHERE id = %s", values)
                conn.commit()
                logger.info(f"✅ User {user_id} updated")
                return True
        except psycopg2.Error as e:
            logger.error(f"❌ Error updating user: {e}")
            return False
    
    @staticmethod
    def delete_user(user_id: int) -> bool:
        """Soft delete user (mark as inactive)"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = %s", (user_id,))
                conn.commit()
                logger.info(f"✅ User {user_id} deleted")
                return True
        except psycopg2.Error as e:
            logger.error(f"❌ Error deleting user: {e}")
            return False
    
    @staticmethod
    def get_all_users(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all active users with pagination"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("""
                    SELECT * FROM users 
                    WHERE is_active = TRUE 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                users = cursor.fetchall()
                cursor.close()
                return [dict(user) for user in users]
        except psycopg2.Error as e:
            logger.error(f"❌ Error fetching all users: {e}")
            return []
    
    # ==================== PRODUCT OPERATIONS ====================
    
    @staticmethod
    def add_product(user_id: int, url: str, title: str, image_url: Optional[str] = None, 
                   original_price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Add a new product for tracking"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("""
                    INSERT INTO products (user_id, url, title, image_url, original_price, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id, user_id, url, title, created_at
                """, (user_id, url, title, image_url, original_price))
                product = cursor.fetchone()
                conn.commit()
                logger.info(f"✅ Product added for user {user_id}: {title}")
                return dict(product) if product else None
        except psycopg2.IntegrityError:
            logger.error(f"❌ Product already exists for this user: {url}")
            return None
        except psycopg2.Error as e:
            logger.error(f"❌ Error adding product: {e}")
            return None
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("SELECT * FROM products WHERE id = %s AND is_active = TRUE", (product_id,))
                product = cursor.fetchone()
                cursor.close()
                return dict(product) if product else None
        except psycopg2.Error as e:
            logger.error(f"❌ Error fetching product: {e}")
            return None
    
    @staticmethod
    def get_user_products(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all products for a user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE user_id = %s AND is_active = TRUE 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (user_id, limit))
                products = cursor.fetchall()
                cursor.close()
                return [dict(product) for product in products]
        except psycopg2.Error as e:
            logger.error(f"❌ Error fetching user products: {e}")
            return []

    @staticmethod
    def get_all_active_products() -> List[Dict[str, Any]]:
        """Return all active products along with the owner email.

        Used for scheduled price checks.
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("""
                    SELECT p.*, u.email
                    FROM products p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.is_active = TRUE
                """ )
                products = cursor.fetchall()
                cursor.close()
                return [dict(product) for product in products]
        except psycopg2.Error as e:
            logger.error(f"❌ Error fetching all active products: {e}")
            return []
    
    @staticmethod
    def update_product_price(product_id: int, current_price: float) -> bool:
        """Update product current price"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE products 
                    SET current_price = %s, 
                        last_checked = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (current_price, product_id))
                conn.commit()
                logger.info(f"✅ Product {product_id} price updated to {current_price}")
                return True
        except psycopg2.Error as e:
            logger.error(f"❌ Error updating product price: {e}")
            return False
    
    @staticmethod
    def delete_product(product_id: int) -> bool:
        """Soft delete product"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE products 
                    SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (product_id,))
                conn.commit()
                logger.info(f"✅ Product {product_id} deleted")
                return True
        except psycopg2.Error as e:
            logger.error(f"❌ Error deleting product: {e}")
            return False
    
    # ==================== PRICE HISTORY OPERATIONS ====================
    
    @staticmethod
    def add_price_history(product_id: int, price: float, discount_percentage: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Record price history for a product"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("""
                    INSERT INTO price_history (product_id, price, discount_percentage, checked_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING id, product_id, price, checked_at
                """, (product_id, price, discount_percentage))
                history = cursor.fetchone()
                conn.commit()
                logger.info(f"✅ Price history recorded for product {product_id}: {price}")
                return dict(history) if history else None
        except psycopg2.Error as e:
            logger.error(f"❌ Error adding price history: {e}")
            return None
    
    @staticmethod
    def get_product_price_history(product_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get price history for a product"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("""
                    SELECT * FROM price_history 
                    WHERE product_id = %s 
                    ORDER BY checked_at DESC 
                    LIMIT %s
                """, (product_id, limit))
                history = cursor.fetchall()
                cursor.close()
                return [dict(h) for h in history]
        except psycopg2.Error as e:
            logger.error(f"❌ Error fetching price history: {e}")
            return []
    
    @staticmethod
    def get_price_drop_percentage(product_id: int) -> Optional[float]:
        """Calculate price drop percentage"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        (SELECT price FROM price_history 
                         WHERE product_id = %s 
                         ORDER BY checked_at DESC LIMIT 1) as current,
                        (SELECT price FROM price_history 
                         WHERE product_id = %s 
                         ORDER BY checked_at ASC LIMIT 1) as original
                """, (product_id, product_id))
                result = cursor.fetchone()
                cursor.close()
                
                if result[0] and result[1]:
                    return ((result[1] - result[0]) / result[1]) * 100
                return None
        except psycopg2.Error as e:
            logger.error(f"❌ Error calculating price drop: {e}")
            return None
    
    # ==================== NOTIFICATION OPERATIONS ====================
    
    @staticmethod
    def create_notification(user_id: int, product_id: int, message: str, 
                          notification_type: str = "price_drop") -> Optional[Dict[str, Any]]:
        """Create a notification for user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("""
                    INSERT INTO notifications (user_id, product_id, message, notification_type)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, user_id, message, created_at
                """, (user_id, product_id, message, notification_type))
                notification = cursor.fetchone()
                conn.commit()
                return dict(notification) if notification else None
        except psycopg2.Error as e:
            logger.error(f"❌ Error creating notification: {e}")
            return None
    
    @staticmethod
    def get_user_notifications(user_id: int, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                query = "SELECT * FROM notifications WHERE user_id = %s"
                
                if unread_only:
                    query += " AND is_read = FALSE"
                
                query += " ORDER BY created_at DESC"
                cursor.execute(query, (user_id,))
                notifications = cursor.fetchall()
                cursor.close()
                return [dict(n) for n in notifications]
        except psycopg2.Error as e:
            logger.error(f"❌ Error fetching notifications: {e}")
            return []
    
    @staticmethod
    def mark_notification_as_read(notification_id: int) -> bool:
        """Mark notification as read"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s", (notification_id,))
                conn.commit()
                return True
        except psycopg2.Error as e:
            logger.error(f"❌ Error marking notification as read: {e}")
            return False
    
    # ==================== UTILITY OPERATIONS ====================
    
    @staticmethod
    def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute custom SQL query"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(query, params)
                results = cursor.fetchall()
                cursor.close()
                return [dict(row) for row in results]
        except psycopg2.Error as e:
            logger.error(f"❌ Error executing custom query: {e}")
            return []
    
    @staticmethod
    def get_database_stats() -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                stats = {}
                
                cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = TRUE")
                stats['total_users'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM products WHERE is_active = TRUE")
                stats['total_products'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM price_history")
                stats['total_price_records'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE is_read = FALSE")
                stats['unread_notifications'] = cursor.fetchone()['count']
                
                cursor.execute("""
                    SELECT AVG(discount_percentage) as avg_discount 
                    FROM price_history 
                    WHERE discount_percentage IS NOT NULL
                """)
                result = cursor.fetchone()
                stats['average_discount'] = result['avg_discount'] if result['avg_discount'] else 0
                
                cursor.close()
                return stats
        except psycopg2.Error as e:
            logger.error(f"❌ Error getting database stats: {e}")
            return {}
    
    @staticmethod
    def close_connection_pool() -> None:
        """Close all connections in the pool"""
        try:
            connection_pool.closeall()
            logger.info("✅ Connection pool closed")
        except Exception as e:
            logger.error(f"❌ Error closing connection pool: {e}")


# Example usage
if __name__ == "__main__":
    # Initialize database
    DatabaseManager.init_db()
    
    # Get database stats
    stats = DatabaseManager.get_database_stats()
    print("\n📊 Database Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Close connection pool on exit
    DatabaseManager.close_connection_pool()
