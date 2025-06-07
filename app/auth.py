from flask import request
from flask_restx import abort
from sqlalchemy.exc import SQLAlchemyError
import bcrypt
from functools import wraps
from .models import User

def check_auth(username, password):
    user = None
    try:
        user = User.query.filter_by(username=username).first()
    except SQLAlchemyError as e:
            abort(500, f"Database error: {str(e)}")
            
    if user and bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return True
    
    return False

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            abort(401)
        return f(*args, **kwargs)
    return decorated_function