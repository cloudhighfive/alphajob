"""Job and application related data models."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class FieldType(str, Enum):
    """Form field types."""
    TEXT = "Text"
    LONGTEXT = "LongText"
    EMAIL = "Email"
    PHONE = "Phone"
    FILE = "File"
    URL = "URL"
    VALUESELECT = "ValueSelect"
    MULTIVALUESELECT = "MultiValueSelect"
    DATE = "Date"


class FormField(BaseModel):
    """Represents a form field in a job application."""
    title: str
    type: FieldType
    path: str
    required: bool = False
    description: Optional[str] = None
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None


class Job(BaseModel):
    """Represents a job posting."""
    title: str
    company: str
    url: HttpUrl
    description: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    posted_date: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: lambda v: str(v)
        }


class JobApplication(BaseModel):
    """Represents a job application submission."""
    job: Job
    fields: Dict[str, Any] = Field(default_factory=dict)
    tailored_resume_path: Optional[str] = None
    status: str = "pending"  # pending, submitted, rejected, accepted
    submitted_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for backward compatibility."""
        return self.model_dump(mode='json')
