import sqlite3
import os

db_path = "test.db"
shop_domain = "overjoyed-thrush-0955f5.instawp.site" # Aapka InstaWP domain
platform = "woocommerce"

# Note: In a real flow, these keys are sent by WooCommerce. 
# Since the callback failed, we can use the keys you saw in WooCommerce settings 
# OR just placeholders if we want to test the UI (but API calls will fail without real keys).

print(f"Adding {shop_domain} to database...")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if already exists
    cursor.execute("SELECT id FROM shops WHERE shop_domain = ?", (shop_domain,))
    row = cursor.fetchone()
    
    if row:
        cursor.execute("UPDATE shops SET platform = ? WHERE shop_domain = ?", (platform, shop_domain))
        print("Updated existing shop.")
    else:
        # Dummy keys for now, replace with real ones from WooCommerce > Settings > Advanced > REST API if you have them
        cursor.execute("""
            INSERT INTO shops (shop_domain, platform, access_token, api_secret, shop_name)
            VALUES (?, ?, ?, ?, ?)
        """, (shop_domain, platform, "ck_dummy", "cs_dummy", "My Woo Store"))
        print("Inserted new shop.")
        
    conn.commit()
    conn.close()
    print("Done! Now refresh your frontend.")
else:
    print("Database not found! Make sure you are in the backend directory.")
