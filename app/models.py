from datetime import datetime, timezone, timedelta
from . import db

class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(50), unique=True, nullable=False)
    orig_url = db.Column(db.String(2048), nullable=False)
    create_time = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expire_time = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc) + timedelta(days=1))
    is_active = db.Column(db.Boolean, default=True)
    clicks = db.relationship("Click", backref="url", lazy="select")

class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey("url.id"), nullable=False)
    click_time = db.Column(db.DateTime, default=datetime.now(timezone.utc), index=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)