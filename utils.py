"""Utility functions for the bot."""

import os
from dotenv import load_dotenv

load_dotenv()


def is_admin(user_id: int) -> bool:
    """Check if a user ID is in the admin list from .env file.
    
    Admin IDs should be comma-separated in the ADMIN_IDS environment variable.
    Example: ADMIN_IDS=123456789,987654321,555555555
    """
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str.strip():
        return False
    
    try:
        admin_ids = [int(id_.strip()) for id_ in admin_ids_str.split(",") if id_.strip()]
        return user_id in admin_ids
    except ValueError:
        # Invalid format in .env
        return False
