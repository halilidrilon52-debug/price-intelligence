import sqlite3
from typing import Optional


DB_PATH = "instance/price_intel.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class DatabaseManager:
    @staticmethod
    def get_connection():
        return get_db_connection()

    @staticmethod
    def init_db():
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            google_id TEXT UNIQUE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            image_url TEXT,
            original_price REAL NOT NULL,
            current_price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        """)

        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def row_to_dict(row):
        return dict(row) if row else None

    @staticmethod
    def rows_to_dicts(rows):
        return [dict(row) for row in rows]

    # ─────────────────────────────────────────────
    # Users
    # ─────────────────────────────────────────────
    @staticmethod
    def create_user(email: str, password_hash: Optional[str] = None, google_id: Optional[str] = None):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, google_id)
                VALUES (?, ?, ?)
                """,
                (email, password_hash, google_id),
            )
            conn.commit()

            user_id = cursor.lastrowid
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()

            return DatabaseManager.row_to_dict(user)

        except sqlite3.IntegrityError:
            return None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_by_email(email: str):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        return DatabaseManager.row_to_dict(user)

    @staticmethod
    def get_user_by_id(user_id: int):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        return DatabaseManager.row_to_dict(user)

    # ─────────────────────────────────────────────
    # Products
    # ─────────────────────────────────────────────
    @staticmethod
    def add_product(user_id: int, url: str, title: str, image_url: str, original_price: float):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO products (
                user_id, url, title, image_url, original_price, current_price
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, url, title, image_url, original_price, original_price),
        )

        conn.commit()
        product_id = cursor.lastrowid

        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        cursor.close()
        conn.close()

        return DatabaseManager.row_to_dict(product)

    @staticmethod
    def get_user_products(user_id: int):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM products
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        products = cursor.fetchall()

        cursor.close()
        conn.close()

        return DatabaseManager.rows_to_dicts(products)

    @staticmethod
    def get_product_by_id(product_id: int):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        cursor.close()
        conn.close()

        return DatabaseManager.row_to_dict(product)

    @staticmethod
    def update_product_price(product_id: int, new_price: float):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE products
            SET current_price = ?
            WHERE id = ?
            """,
            (new_price, product_id),
        )

        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def delete_product(product_id: int, user_id: int):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM products WHERE id = ? AND user_id = ?",
            (product_id, user_id),
        )

        deleted = cursor.rowcount > 0

        conn.commit()
        cursor.close()
        conn.close()

        return deleted

    @staticmethod
    def get_all_active_products():
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                products.*,
                users.email
            FROM products
            JOIN users ON products.user_id = users.id
            ORDER BY products.created_at DESC
            """
        )
        products = cursor.fetchall()

        cursor.close()
        conn.close()

        return DatabaseManager.rows_to_dicts(products)

    # ─────────────────────────────────────────────
    # Price History
    # ─────────────────────────────────────────────
    @staticmethod
    def add_price_history(product_id: int, price: float):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO price_history (product_id, price)
            VALUES (?, ?)
            """,
            (product_id, price),
        )

        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def get_price_history(product_id: int):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM price_history
            WHERE product_id = ?
            ORDER BY checked_at DESC
            """,
            (product_id,),
        )
        history = cursor.fetchall()

        cursor.close()
        conn.close()

        return DatabaseManager.rows_to_dicts(history)