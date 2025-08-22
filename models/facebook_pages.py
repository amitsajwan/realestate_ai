from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FacebookPage(Base):
    __tablename__ = 'facebook_pages'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    page_id = Column(String, nullable=False)
    page_name = Column(String)
    access_token = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
