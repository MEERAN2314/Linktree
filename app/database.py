from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

MONGO_URL = "mongodb+srv://meeran:meeran2314@youtube.z01cb1a.mongodb.net/?retryWrites=true&w=majority&appName=Youtube"
DB_NAME = "linktree"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def check_db_connection():
    try:
        await client.admin.command('ping')
        print("Successfully connected to MongoDB")
    except ConnectionFailure:
        print("MongoDB connection failed")