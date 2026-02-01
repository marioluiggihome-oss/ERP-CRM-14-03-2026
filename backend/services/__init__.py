"""
Services package
"""
from .database import db, get_database, close_database
from .auth_service import hash_password, verify_password
from .email_service import send_email, send_backup_email, send_order_confirmation
