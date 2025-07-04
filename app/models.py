from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class Link(BaseModel):
    title: str = Field(..., max_length=30)
    url: HttpUrl  # This ensures valid URLs
    clicks: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "title": "My Portfolio",
                "url": "https://example.com",
                "clicks": 0
            }
        }

class UserProfile(User):
    links: list[Link] = []