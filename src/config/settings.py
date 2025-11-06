"""
Configuration settings management with environment variable support.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache

from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class PersonalInfo(BaseModel):
    """Personal information configuration."""
    name: str
    email: str
    phone: str
    location: str
    city: str
    state: str
    first_name: Optional[str] = ""
    middle_name: Optional[str] = ""
    last_name: Optional[str] = ""
    pronouns: Optional[str] = "he/him/his"
    state_abbr: Optional[str] = ""
    country: Optional[str] = "United States"
    zip_code: Optional[str] = ""


class Links(BaseModel):
    """External links configuration."""
    linkedin: str
    github: Optional[str] = ""
    portfolio: Optional[str] = ""
    website: Optional[str] = ""


class WorkAuthorization(BaseModel):
    """Work authorization configuration."""
    authorized_to_work_us: bool = True
    authorized_to_work_canada: bool = False
    needs_visa_sponsorship: bool = False
    has_security_clearance: bool = False


class Demographics(BaseModel):
    """Demographics configuration."""
    gender: str = "Man"
    race: str = "White"
    disability: str = "No"
    veteran_status: str = "No"
    disability_status: Optional[str] = "No"


class Background(BaseModel):
    """Professional background configuration."""
    years_of_experience: int
    current_title: str
    industry: str
    specialization: str
    elevator_pitch: str


class Preferences(BaseModel):
    """Job preferences configuration."""
    job_types: List[str] = Field(default_factory=lambda: ["Remote"])
    employment_types: List[str] = Field(default_factory=lambda: ["Full-time"])
    min_salary: int = 150000
    max_salary: int = 220000
    willing_to_relocate: bool = False
    notice_period_weeks: int = 2


class Files(BaseModel):
    """File paths configuration."""
    original_resume_path: str = "resumes/original/resume.docx"
    cover_letter_template: Optional[str] = None


class ResumePersonalInfo(BaseModel):
    """Personal info specifically for resume generation."""
    full_name: str
    location: str
    phone: str
    email: str
    linkedin: str
    github: str


class WorkExperience(BaseModel):
    """Work experience entry."""
    title: str
    company: str
    location: str
    dates: str


class Education(BaseModel):
    """Education information."""
    degree: str
    university: str
    location: str
    graduated: str
    coursework: Optional[str] = ""
    gpa: Optional[str] = ""


class UserInfo(BaseModel):
    """Complete user information."""
    personal_info: PersonalInfo
    links: Links
    work_authorization: WorkAuthorization
    demographics: Demographics
    background: Optional[Background] = None
    preferences: Preferences
    files: Files
    resume_personal_info: Optional[ResumePersonalInfo] = None
    work_experience: Optional[List[WorkExperience]] = None
    education: Optional[Education] = None


class AISettings(BaseModel):
    """AI model settings configuration."""
    model: str = "llama3.1"
    temperature: float = 0.7
    tone: str = "professional and enthusiastic"
    answer_length: str = "concise"
    emphasize_keywords: bool = True
    available_models: List[str] = Field(default_factory=lambda: ["llama3.1", "deepseek-r1"])


class Prompts(BaseModel):
    """AI prompts configuration."""
    tailor_resume: Optional[str] = None
    answer_question: Optional[str] = None
    select_option: Optional[str] = None


class Settings(BaseSettings):
    """Main application settings."""
    
    # User configuration
    user_info: Optional[UserInfo] = None
    ai_settings: AISettings = Field(default_factory=AISettings)
    prompts: Optional[Prompts] = None
    
    # Application settings from environment
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    max_retries: int = Field(default=3, validation_alias="MAX_RETRIES")
    timeout: int = Field(default=30, validation_alias="TIMEOUT")
    
    # Directories
    resumes_dir: Path = Path("resumes")
    original_resume_dir: Path = Path("resumes/original")
    tailored_resume_dir: Path = Path("resumes/tailored")
    applications_dir: Path = Path("applications")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    @classmethod
    def from_json(cls, config_path: str = "config.json") -> "Settings":
        """
        Load settings from JSON configuration file.
        
        Args:
            config_path: Path to JSON configuration file
            
        Returns:
            Settings instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config is invalid
        """
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Create Settings instance with data from JSON
            settings = cls(**config_data)
            
            # Ensure directories exist
            settings.tailored_resume_dir.mkdir(parents=True, exist_ok=True)
            settings.applications_dir.mkdir(parents=True, exist_ok=True)
            
            return settings
            
        except FileNotFoundError:
            raise FileNotFoundError(
                f"❌ Config file not found: {config_path}\n"
                "   Please create config.json with your information"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"❌ Invalid JSON in config file: {e}")
        except ValidationError as e:
            raise ValueError(f"❌ Invalid configuration: {e}")
    
    def to_dict(self) -> Dict:
        """Convert settings to dictionary."""
        return self.model_dump(exclude_none=True)
    
    def get_user_config(self) -> Dict:
        """Get user configuration as dictionary for backward compatibility."""
        if not self.user_info:
            raise ValueError("User info not configured")
        return self.user_info.model_dump()


@lru_cache()
def get_settings(config_path: str = "config.json") -> Settings:
    """
    Get cached settings instance.
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        Settings instance (cached)
    """
    return Settings.from_json(config_path)
