import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")

if not MONGODB_URI:
    raise RuntimeError("❌ MONGODB_URI is missing in .env")

if not MONGODB_DB_NAME:
    raise RuntimeError("❌ MONGODB_DB_NAME is missing in .env")

# Tạo client Motor
client = AsyncIOMotorClient(
    MONGODB_URI,
    uuidRepresentation="standard"
)

# Chọn DB
db = client[MONGODB_DB_NAME]

def get_collection(name: str):
    return db[name]
