from motor.motor_asyncio import AsyncIOMotorClient
from core.config import Config

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db = MongoDB()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(Config.MONGODB_URI)
    db.db = db.client[Config.MONGODB_DB_NAME]
    print(f"Connected to MongoDB: {Config.MONGODB_DB_NAME}")

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("MongoDB connection closed")

def get_database():
    return db.db
