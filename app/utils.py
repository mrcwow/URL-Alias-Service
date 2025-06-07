import base64
import hashlib
import random
from sqlalchemy.exc import SQLAlchemyError
from . import db, SERVICE_URL
from .models import URL

def generate_url(url):
    attempt = 0
    max_attempts = 5
    base_url = url

    while attempt < max_attempts:
        hash_object = hashlib.md5(url.encode())
        url = SERVICE_URL + base64.urlsafe_b64encode(hash_object.digest())[:12].decode()
        
        try:
            if not URL.query.filter_by(url=url).first():
                return url
        except SQLAlchemyError as e:
            raise e
        
        url = base_url + str(random.randint(1, 1000))
        attempt += 1
    
    raise ValueError("Unable to convert long URL into short unique URL")