import sqlite3
import os
import sys

db_path = "test.db"
shop_domain = "overjoyed-thrush-0955f5.instawp.site"

if len(sys.argv) < 3:
    print("Usage: python update_keys.py <ck_...> <cs_...>")
    sys.exit(1)

ck = sys.argv[1]
cs = sys.argv[2]

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE shops 
        SET access_token = ?, api_secret = ?, platform = 'woocommerce'
        WHERE shop_domain = ?
    """, (ck, cs, shop_domain))
    
    if cursor.rowcount > 0:
        print(f"Successfully updated keys for {shop_domain}")
    else:
        # If not exists, insert
        cursor.execute("""
            INSERT INTO shops (shop_domain, platform, access_token, api_secret, shop_name)
            VALUES (?, ?, ?, ?, ?)
        """, (shop_domain, 'woocommerce', ck, cs, "My Woo Store"))
        print(f"Inserted new entry with real keys for {shop_domain}")
        
    conn.commit()
    conn.close()
    print("Refresh your dashboard now!")
else:
    print("Database not found!")
