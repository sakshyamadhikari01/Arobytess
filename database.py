import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "data", "arobytess.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    """Initialize database tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                credits INTEGER DEFAULT 0,
                tokens INTEGER DEFAULT 5,
                last_token_reset TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, type)
            )
        ''')
        
        # User friends (many-to-many relationship)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                friend_name TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, friend_name)
            )
        ''')
        
        # Disease reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS disease_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disease_name TEXT NOT NULL,
                location TEXT DEFAULT 'Bharatpur',
                crop_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                reporter_phone TEXT,
                reported_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending_verification'
            )
        ''')

        # Alert registrations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farmer_name TEXT NOT NULL,
                phone_number TEXT NOT NULL UNIQUE,
                location TEXT DEFAULT 'Bharatpur',
                crop_types TEXT,
                alert_radius INTEGER DEFAULT 10,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Detection history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                image TEXT NOT NULL,
                prediction TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                seller_name TEXT NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                type TEXT,
                phone TEXT,
                views INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES users(id)
            )
        ''')

# --- User Operations ---

def create_user(name: str, user_type: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        current_month = datetime.now().strftime("%Y-%m")
        cursor.execute(
            'INSERT INTO users (name, type, last_token_reset) VALUES (?, ?, ?)',
            (name, user_type, current_month)
        )
        return get_user_by_id(cursor.lastrowid)

def get_user_by_id(user_id: int) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            user = dict(row)
            user['friends'] = get_user_friends(user_id)
            return user
        return None

def get_user_by_name_type(name: str, user_type: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE LOWER(name) = LOWER(?) AND type = ?',
            (name, user_type)
        )
        row = cursor.fetchone()
        if row:
            user = dict(row)
            user['friends'] = get_user_friends(user['id'])
            return user
        return None

def update_user(user_id: int, credits: int = None, tokens: int = None, last_token_reset: str = None) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        updates = []
        values = []
        
        if credits is not None:
            updates.append('credits = ?')
            values.append(credits)
        if tokens is not None:
            updates.append('tokens = ?')
            values.append(tokens)
        if last_token_reset is not None:
            updates.append('last_token_reset = ?')
            values.append(last_token_reset)
        
        if updates:
            values.append(user_id)
            cursor.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ?', values)
        
        return get_user_by_id(user_id)

def get_user_friends(user_id: int) -> list:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT friend_name FROM user_friends WHERE user_id = ?', (user_id,))
        return [row['friend_name'] for row in cursor.fetchall()]

def add_user_friend(user_id: int, friend_name: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO user_friends (user_id, friend_name) VALUES (?, ?)',
            (user_id, friend_name)
        )
        return get_user_by_id(user_id)


# --- Disease Report Operations ---

def create_disease_report(disease_name: str, crop_type: str, severity: str, 
                          description: str = None, location: str = "Bharatpur") -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO disease_reports (disease_name, location, crop_type, severity, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (disease_name, location, crop_type, severity, description))
        return get_disease_report_by_id(cursor.lastrowid)

def get_disease_report_by_id(report_id: int) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM disease_reports WHERE id = ?', (report_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_recent_disease_reports(location: str = None, limit: int = 10) -> list:
    with get_db() as conn:
        cursor = conn.cursor()
        if location:
            cursor.execute('''
                SELECT * FROM disease_reports 
                WHERE LOWER(location) LIKE LOWER(?)
                ORDER BY reported_at DESC LIMIT ?
            ''', (f'%{location}%', limit))
        else:
            cursor.execute('SELECT * FROM disease_reports ORDER BY reported_at DESC LIMIT ?', (limit,))
        return [dict(row) for row in cursor.fetchall()]

# --- Alert Registration Operations ---

def create_or_update_alert_registration(farmer_name: str, phone_number: str, 
                                        crop_types: str, alert_radius: int,
                                        location: str = "Bharatpur") -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM alert_registrations WHERE phone_number = ?', (phone_number,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE alert_registrations 
                SET farmer_name = ?, crop_types = ?, alert_radius = ?, 
                    location = ?, updated_at = CURRENT_TIMESTAMP
                WHERE phone_number = ?
            ''', (farmer_name, crop_types, alert_radius, location, phone_number))
            return get_alert_registration_by_id(existing['id'])
        else:
            cursor.execute('''
                INSERT INTO alert_registrations (farmer_name, phone_number, location, crop_types, alert_radius)
                VALUES (?, ?, ?, ?, ?)
            ''', (farmer_name, phone_number, location, crop_types, alert_radius))
            return get_alert_registration_by_id(cursor.lastrowid)

def get_alert_registration_by_id(reg_id: int) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM alert_registrations WHERE id = ?', (reg_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# --- Detection History Operations ---

def save_detection_record(user_id: int, image: str, prediction: str, confidence: float) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO detection_history (user_id, image, prediction, confidence)
            VALUES (?, ?, ?, ?)
        ''', (user_id, image, prediction, confidence))
        return get_detection_record_by_id(cursor.lastrowid)

def get_detection_record_by_id(record_id: int) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM detection_history WHERE id = ?', (record_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_detection_history(user_id: int) -> list:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM detection_history 
            WHERE user_id = ? ORDER BY timestamp DESC
        ''', (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_detection_record(record_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM detection_history WHERE id = ?', (record_id,))
        return cursor.rowcount > 0

# --- Product Operations ---

def create_product(seller_id: int, seller_name: str, name: str, price: float,
                   description: str, product_type: str, phone: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (seller_id, seller_name, name, price, description, type, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (seller_id, seller_name, name, price, description, product_type, phone))
        return get_product_by_id(cursor.lastrowid)

def get_product_by_id(product_id: int) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_products() -> list:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products')
        return [dict(row) for row in cursor.fetchall()]

def get_seller_products(seller_id: int) -> list:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE seller_id = ?', (seller_id,))
        return [dict(row) for row in cursor.fetchall()]

def delete_product(product_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        return cursor.rowcount > 0

def increment_product_views(product_id: int) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE products SET views = views + 1 WHERE id = ?', (product_id,))
        return get_product_by_id(product_id)

# Initialize database on import
init_db()
