"""
Migration script to import existing JSON data into SQLite database.
Run this once to migrate your data: python migrate_to_db.py
"""
import json
import os
from database import get_db, init_db

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_json(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return []

def migrate_users():
    users = load_json('users.json')
    with get_db() as conn:
        cursor = conn.cursor()
        for user in users:
            cursor.execute('''
                INSERT OR IGNORE INTO users (id, name, type, credits, tokens, last_token_reset)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user['id'], user['name'], user['type'], 
                  user.get('credits', 0), user.get('tokens', 5), 
                  user.get('lastTokenReset', '')))
            
            for friend in user.get('friends', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO user_friends (user_id, friend_name)
                    VALUES (?, ?)
                ''', (user['id'], friend))
    print(f"Migrated {len(users)} users")

def migrate_disease_reports():
    reports = load_json('disease_reports.json')
    with get_db() as conn:
        cursor = conn.cursor()
        for report in reports:
            cursor.execute('''
                INSERT OR IGNORE INTO disease_reports 
                (id, disease_name, location, crop_type, severity, description, reporter_phone, reported_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (report['id'], report['diseaseName'], report.get('location', 'Bharatpur'),
                  report['cropType'], report['severity'], report.get('description'),
                  report.get('reporterPhone'), report.get('reportedAt'), report.get('status')))
    print(f"Migrated {len(reports)} disease reports")

def migrate_alert_registrations():
    alerts = load_json('alert_registrations.json')
    with get_db() as conn:
        cursor = conn.cursor()
        for alert in alerts:
            cursor.execute('''
                INSERT OR IGNORE INTO alert_registrations 
                (id, farmer_name, phone_number, location, crop_types, alert_radius, registered_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (alert['id'], alert['farmerName'], alert['phoneNumber'],
                  alert.get('location', 'Bharatpur'), alert.get('cropTypes'),
                  alert.get('alertRadius', 10), alert.get('registeredAt'),
                  1 if alert.get('isActive', True) else 0))
    print(f"Migrated {len(alerts)} alert registrations")

def migrate_detection_history():
    history = load_json('detection_history.json')
    with get_db() as conn:
        cursor = conn.cursor()
        for record in history:
            cursor.execute('''
                INSERT OR IGNORE INTO detection_history 
                (id, user_id, image, prediction, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (record['id'], record['userId'], record['image'],
                  record['prediction'], record['confidence'], record.get('timestamp')))
    print(f"Migrated {len(history)} detection records")

def migrate_products():
    products = load_json('products.json')
    with get_db() as conn:
        cursor = conn.cursor()
        for product in products:
            cursor.execute('''
                INSERT OR IGNORE INTO products 
                (id, seller_id, seller_name, name, price, description, type, phone, views)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (product['id'], product['seller_id'], product['seller_name'],
                  product['name'], product['price'], product.get('description'),
                  product.get('type'), product.get('phone'), product.get('views', 0)))
    print(f"Migrated {len(products)} products")

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    
    print("\nMigrating data from JSON files...")
    migrate_users()
    migrate_disease_reports()
    migrate_alert_registrations()
    migrate_detection_history()
    migrate_products()
    
    print("\nMigration complete! Database created at: data/arobytess.db")
