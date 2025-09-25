import hashlib
import secrets
from functools import wraps
from flask import request, jsonify, session
import os

# Default admin credentials (change these!)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "stratus2024!"  # Change this!

def hash_password(password):
    """Hash a password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password, stored_hash):
    """Verify a password against stored hash"""
    try:
        salt, password_hash = stored_hash.split(':')
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    except:
        return False

def require_auth(f):
    """Decorator to require authentication for admin endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for session-based auth
        if session.get('admin_authenticated'):
            return f(*args, **kwargs)
        
        # Check for API key in headers
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # Simple token validation (in production, use proper JWT)
            if token == os.getenv('ADMIN_API_TOKEN', 'stratus-admin-token-2024'):
                return f(*args, **kwargs)
        
        return jsonify({'error': 'Authentication required'}), 401
    
    return decorated_function

def authenticate_admin(username, password):
    """Authenticate admin user"""
    # In production, check against database
    # For now, use environment variables or defaults
    admin_username = os.getenv('ADMIN_USERNAME', DEFAULT_ADMIN_USERNAME)
    admin_password = os.getenv('ADMIN_PASSWORD', DEFAULT_ADMIN_PASSWORD)
    
    if username == admin_username and password == admin_password:
        return True
    return False
