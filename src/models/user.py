"""User profile related data models."""

from pydantic import BaseModel, EmailStr
from typing import Optional


class UserProfile(BaseModel):
    """Represents user profile information."""
    name: str
    email: EmailStr
    phone: str
    location: str
    city: str
    state: str
    zip_code: str
    linkedin: str
    github: Optional[str] = None
    portfolio: Optional[str] = None
    years_of_experience: int
    current_title: str
    elevator_pitch: str
    
    class Config:
        json_encoders = {
            EmailStr: lambda v: str(v)
        }
