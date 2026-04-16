from database.db import engine
from models.shop_model import Shop

def init():
    print("🚀 Creating database tables...")
    Shop.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

if __name__ == "__main__":
    init()