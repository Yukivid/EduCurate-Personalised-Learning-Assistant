from sqlalchemy import Column, ForeignKey, Integer, String, BigInteger, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User_Info(Base):
    __tablename__ = "user_info"
    
    user_id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String, nullable=False, index=True)
    lastName = Column(String, nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    countryCode = Column(Integer, index=True)
    phoneNo = Column(BigInteger, index=True)
    userName = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)

    logins = relationship("Login_Info", back_populates="user")


class Login_Info(Base):
    __tablename__ = "login_info"

    login_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_info.user_id"), nullable=False)
    login_time = Column(DateTime, default=datetime.utcnow)

    user = relationship("User_Info", back_populates="logins")

class TopicsViewed(Base):
    __tablename__ = "topics_viewed"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userName = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    sub_topics = Column(Text, nullable=True)   
    videos_viewed = Column(Integer, default=0)
    questions_answered = Column(Integer, default=0)
    
class TestAnswer(Base):
    __tablename__ = "test_answers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(100), nullable=False, index=True)
    topic = Column(String(255), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)