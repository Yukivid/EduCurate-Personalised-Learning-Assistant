from pydantic import BaseModel, Field
from datetime import datetime

class User(BaseModel):
    firstName: str
    lastName: str
    email: str
    phoneNo: int
    countryCode: int
    userName: str
    password: str

class LoginRequest(BaseModel):
    userName: str
    password: str
    LoginTime: datetime = Field(default_factory=datetime.utcnow)
    
class ForgotPasswordRequest(BaseModel):
    userName: str

class ResetPasswordRequest(BaseModel):
    userName: str
    newPassword: str

class TopicsViewedCreate(BaseModel):
    userName: str
    topic: str
    sub_topics: str
    videos_viewed: int = 0
    questions_answered: int = 0

class TopicsViewedOut(TopicsViewedCreate):
    id: int
    class Config:
        orm_mode = True
        

class SubmitAnswerCreate(BaseModel):
    user_name: str
    topic: str
    question: str
    answer: str

class SubmitAnswerOut(BaseModel):
    id: int
    user_name: str
    topic: str
    question: str
    answer: str
    created_at: datetime

    class Config:
        orm_mode = True