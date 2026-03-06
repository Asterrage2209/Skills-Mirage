import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "skills_mirage_db")

try:
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    users_collection = db["users"]
    logger.info(f"Connected to MongoDB Atlas: database '{DATABASE_NAME}'")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    users_collection = None
