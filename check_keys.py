import sqlite3
import os
db_path = r'd:\Projects\shopify-meta-ads-analytics-engine\test.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT shop_domain, access_token, api_secret FROM shops WHERE shop_domain LIKE '%overjoyed%'")
    row = cursor.fetchone()
    if row:
        print(f"Domain: {row[0]}")
        print(f"Key: {row[1]}")
        print(f"Secret: {row[2]}")
    else:
        print("Shop not found in DB")
    conn.close()
else:
    print("DB not found")
