"""Resume related data models."""

from typing import List, Optional, Dict
from pydantic import BaseModel


class WorkExperience(BaseModel):
    """Represents a work experience entry."""
    company: str
    title: str
    location: Optional[str] = None
    dates: str
    bullets: List[str]
    start_para: int
    end_para: int


class ResumeSection(BaseModel):
    """Represents a section in the resume."""
    name: str
    text: str
    start: int
    end: int


class Resume(BaseModel):
    """Represents a resume document."""
    content: str
    sections: Dict[str, ResumeSection] = {}
    work_experiences: List[WorkExperience] = []
    file_path: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
