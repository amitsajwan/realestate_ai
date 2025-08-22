from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FacebookPost(Base):
    __tablename__ = 'facebook_posts'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    page_id = Column(String, nullable=False)
    post_id = Column(String, nullable=False)
    message = Column(String)
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
