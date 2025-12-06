from motor.motor_asyncio import AsyncIOMotorClient
from settings import MONGODB_URI, MONGODB_DB_NAME

client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB_NAME]

def get_collection(name: str):
    return db[name]
