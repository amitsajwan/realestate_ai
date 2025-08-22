from services.mongo_client import db
from cryptography.fernet import Fernet
import os

FERNET_KEY = os.getenv('FERNET_KEY', Fernet.generate_key())
fernet = Fernet(FERNET_KEY)

class FacebookAuthService:
    @staticmethod
    def save_auth(user_id: str, access_token: str, refresh_token: str = None, expires_at = None):
        encrypted_token = fernet.encrypt(access_token.encode()).decode()
        doc = {
            'user_id': user_id,
            'access_token': encrypted_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at
        }
        db.facebook_auth.insert_one(doc)
        return doc

    @staticmethod
    def get_auth(user_id: str):
        doc = db.facebook_auth.find_one({'user_id': user_id})
        if doc:
            doc['access_token'] = fernet.decrypt(doc['access_token'].encode()).decode()
        return doc

    @staticmethod
    def save_state(state: str):
        doc = {'state': state}
        db.oauth_states.insert_one(doc)
        return doc

    @staticmethod
    def validate_state(state: str):
        return db.oauth_states.find_one({'state': state}) is not None
