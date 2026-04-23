import sqlite3
import os

db_path = "test.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT shop_domain, platform, access_token FROM shops")
    rows = cursor.fetchall()
    print("--- Connected Shops ---")
    for row in rows:
        print(f"Domain: {row[0]}, Platform: {row[1]}, Key: {row[2][:5]}...")
    conn.close()
else:
    print("Database not found!")
