import logging
from pymongo.errors import PyMongoError
from datetime import datetime
from database.connection import get_db

# Setup logging
logger = logging.getLogger(__name__)

def add_group(limit: int) -> bool:
    """Add a new VCF group with a fixed group ID."""
    db = get_db()
    try:
        group_id = f"ID-XP{limit}GROUP"
        existing_group = db.groups.find_one({"group_id": group_id})
        if existing_group:
            logger.warning(f"Group {group_id} already exists")
            return False
        group = {
            "group_id": group_id,
            "limit": limit,
            "current_users": 0,
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        result = db.groups.insert_one(group)
        logger.info(f"Added group {group_id} with limit {limit}")
        return result.inserted_id is not None
    except PyMongoError as e:
        logger.error(f"Failed to add group with limit {limit}: {e}")
        return False

def get_active_groups_by_limit(limit: int):
    """Fetch or create a single active group for a given limit."""
    db = get_db()
    try:
        group_id = f"ID-XP{limit}GROUP"
        group = db.groups.find_one({"group_id": group_id, "status": "active"})
        if not group:
            logger.info(f"No active group for limit {limit}, creating a new one")
            if add_group(limit):
                group = db.groups.find_one({"group_id": group_id, "status": "active"})
            else:
                return []
        return [group]
    except PyMongoError as e:
        logger.error(f"Failed to fetch active groups with limit {limit}: {e}")
        return []

def get_group(group_id: str):
    """Fetch group details by group_id."""
    db = get_db()
    try:
        group = db.groups.find_one({"group_id": group_id})
        return group
    except PyMongoError as e:
        logger.error(f"Failed to fetch group {group_id}: {e}")
        return None

def get_all_groups():
    """Fetch all groups from the database."""
    db = get_db()
    try:
        groups = db.groups.find()
        logger.info("Fetched all groups for stats")
        return groups
    except PyMongoError as e:
        logger.error(f"Failed to fetch all groups: {e}")
        return []

def update_group_status(group_id: str, status: str):
    """Update the status of a group (e.g., active, full, approved)."""
    db = get_db()
    try:
        result = db.groups.update_one(
            {"group_id": group_id},
            {"$set": {"status": status, "updated_at": datetime.now()}}
        )
        if result.modified_count > 0:
            logger.info(f"Updated group {group_id} status to {status}")
        else:
            logger.warning(f"No group found with group_id {group_id} for status update")
        return result.modified_count > 0
    except PyMongoError as e:
        logger.error(f"Failed to update group {group_id} status to {status}: {e}")
        return False

def increment_group_users(group_id: str):
    """Increment the current_users count for a group and check if it's full."""
    db = get_db()
    try:
        group = db.groups.find_one({"group_id": group_id})
        if not group:
            logger.warning(f"Group {group_id} not found for increment")
            return False

        new_count = group["current_users"] + 1
        update_data = {
            "current_users": new_count,
            "updated_at": datetime.now()
        }
        if new_count >= group["limit"]:
            update_data["status"] = "full"

        result = db.groups.update_one(
            {"group_id": group_id},
            {"$set": update_data}
        )
        if result.modified_count > 0:
            logger.info(f"Incremented users for group {group_id} to {new_count}")
            return True
        return False
    except PyMongoError as e:
        logger.error(f"Failed to increment users for group {group_id}: {e}")
        return False