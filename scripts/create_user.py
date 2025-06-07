import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import bcrypt
from sqlalchemy.exc import SQLAlchemyError
from app import create_app, db
from app.models import User

def create_user(username, password):
    app = create_app()
    with app.app_context():
        user = User(
            username=username,
            password_hash=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        )
        try:
            db.session.add(user)
            db.session.commit()
            print(f"\nUser {username} created successfully")
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"\n500 Database error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Right command: python create_user.py <username> <password>")
        sys.exit(1)
    create_user(sys.argv[1], sys.argv[2])