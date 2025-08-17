import os
from datetime import datetime
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from pymongo import MongoClient

def get_db_connection(mode="production"):
    if mode == "production":
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
        return client.realestate_crm
    else:
        class InMemoryDB:
            def __init__(self):
                self.users = []
                self.leads = []
                self.properties = []
            # Add stub storage/query functions if needed
        return InMemoryDB()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
