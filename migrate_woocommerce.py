import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
db_path = db_url.replace("sqlite:///", "").replace("./", "")

print(f"TARGET DATABASE: {db_path}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(shops)")
    columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = [
        ("platform", "TEXT DEFAULT 'shopify'"),
        ("api_secret", "TEXT")
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            print(f"Adding column {col_name}...")
            cursor.execute(f"ALTER TABLE shops ADD COLUMN {col_name} {col_type}")
        else:
            print(f"Column {col_name} already exists.")
    
    conn.commit()
    conn.close()
    print("WooCommerce migration successful.")
else:
    print(f"Error: {db_path} not found.")
