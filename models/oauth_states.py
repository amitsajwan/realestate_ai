from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class OAuthState(Base):
    __tablename__ = 'oauth_states'
    id = Column(Integer, primary_key=True)
    state = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
