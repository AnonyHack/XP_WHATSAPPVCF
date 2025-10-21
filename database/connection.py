import logging
from pymongo import MongoClient
from config import MONGO_DB_URI, MONGO_DB_NAME

# Setup logging
logger = logging.getLogger(__name__)

# Initialize MongoDB client and database
client = None
db = None

def connect_to_mongo():
    """Establish connection to MongoDB database."""
    global client, db
    try:
        client = MongoClient(MONGO_DB_URI)
        db = client[MONGO_DB_NAME]
        logger.info("Connected to MongoDB successfully")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

def get_db():
    """Get the MongoDB database instance, connecting if not already connected."""
    global db
    if db is None:
        connect_to_mongo()
    return db