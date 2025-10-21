import logging
from pymongo.errors import PyMongoError
from datetime import datetime
from database.connection import get_db

# Setup logging
logger = logging.getLogger(__name__)

def register_user(user_id: int) -> bool:
    """Register a user in the database when they send /start."""
    db = get_db()
    try:
        # Check if user already exists
        existing_user = db.users.find_one({"user_id": user_id})
        if existing_user:
            logger.info(f"User {user_id} already registered")
            return True

        user = {
            "user_id": user_id,
            "subscribed": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        result = db.users.insert_one(user)
        logger.info(f"Registered user {user_id}")
        return result.inserted_id is not None
    except PyMongoError as e:
        logger.error(f"Failed to register user {user_id}: {e}")
        return False

def update_user_subscription_status(user_id: int, subscribed: bool) -> bool:
    """Update the user's subscription status."""
    db = get_db()
    try:
        result = db.users.update_one(
            {"user_id": user_id},
            {"$set": {"subscribed": subscribed, "updated_at": datetime.now()}}
        )
        if result.modified_count > 0 or result.matched_count > 0:
            logger.info(f"Updated subscription status for user {user_id} to {subscribed}")
            return True
        logger.warning(f"No user found with user_id {user_id} for subscription update")
        return False
    except PyMongoError as e:
        logger.error(f"Failed to update subscription status for user {user_id}: {e}")
        return False

def add_user(user_id: int, name: str, number: str, group_id: str) -> bool:
    """Add or update a user's submission to a group."""
    db = get_db()
    try:
        result = db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "name": name,
                    "number": number,
                    "group_id": group_id,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )
        if result.modified_count > 0 or result.upserted_id:
            logger.info(f"Added/updated submission for user {user_id} to group {group_id}")
            return True
        logger.warning(f"Failed to add/update submission for user {user_id} to group {group_id}")
        return False
    except PyMongoError as e:
        logger.error(f"Failed to add submission for user {user_id} to group {group_id}: {e}")
        return False

def get_user_submissions(user_id: int):
    """Fetch all groups a user has submitted to, including group details."""
    db = get_db()
    try:
        # Find user submissions
        user = db.users.find_one({"user_id": user_id, "name": {"$exists": True}})
        if not user:
            logger.info(f"No submissions found for user {user_id}")
            return []
        group = db.groups.find_one({"group_id": user["group_id"]})
        if not group:
            logger.info(f"No group found for user {user_id}'s submission")
            return []
        submission_groups = [{
            "group_id": group["group_id"],
            "limit": group["limit"],
            "status": group["status"],
            "current_users": group["current_users"]
        }]
        logger.info(f"Fetched {len(submission_groups)} submissions for user {user_id}")
        return submission_groups
    except PyMongoError as e:
        logger.error(f"Failed to fetch submissions for user {user_id}: {e}")
        return []

def get_all_users():
    """Fetch all users from the database for broadcasting."""
    db = get_db()
    try:
        users = db.users.find()
        logger.info("Fetched all users for broadcast")
        return users
    except PyMongoError as e:
        logger.error(f"Failed to fetch all users: {e}")
        return []

def total_users_count() -> int:
    """Count the total number of users in the database."""
    db = get_db()
    try:
        count = db.users.count_documents({})
        logger.info(f"Total users count: {count}")
        return count
    except PyMongoError as e:
        logger.error(f"Failed to count users: {e}")
        return 0