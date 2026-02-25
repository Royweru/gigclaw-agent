# app/core/models.py

from pydantic import BaseModel, Field ,HttpUrl
from typing import Optional , List
from datetime import datetime
from enum import Enum


#ENUMS
class JobSource(str, Enum):
    """Where did the job come from ?"""
    REMOTE_OK = "remoteok"
    
    #WE_WORK_REMOTELY = "weworkremotely"
    #LINKEDIN = "linkedin"
class ApplicationStatus(str,Enum) :
    """" The lifecycle of a job application"""
    DISCOVERED = "discovered"
    MATCHED = "matched"
    APPROVED = "approved"
    APPLIED = "applied"
    FAILED = "failed"
    SKIPPED = "skipped"
    
#CORE MODELS
class Job(BaseModel) :
    """A single job listing from any job board"""
    id:str = Field(...,description = "Unique ID for deduplication")
    source:JobSource
    url:HttpUrl
    
    title:str
    company:str
    description:str
    location:Optional[str] = "Remote"
    salary:Optional[str] = None
    tags:list[str] = Field(default_factory=list)
    
    posted_date:str
    discovered_at:datetime =Field(default_factory=datetime.now)
    
    match_score:Optional[float] = None
    match_reasoning:Optional[str] = None
    status:ApplicationStatus = ApplicationStatus.DISCOVERED
    
    class Config :
        json_encoders = {
            datetime:lambda v: v.isoformat()
        }


class UserProfile(BaseModel) :
    """The candidate information preferences """
    name:str
    email:str
    phone:Optional[str] = None
    linkedin:Optional[str] = None
    github:Optional[str] = None
    website:Optional[str] = None
    
    cv_text:str 
    cover_letter_template:str
    
    target_roles:List[str] 
    min_salary:Optional[int] = None
    min_match_score:float = 75.0
    
class MatchResult(BaseModel) :
    """What our model returns when evaluating a job match"""
    match_score:float = Field(..., ge = 0,le=100,description = "Score from 0-100")
    reasoning:str =Field(..., description="why was this score given")
    key_requirements:List[str]
    missing_skills:List[str]
    
class TailoredContent(BaseModel):
    """Structured output for content generation"""
    tailored_cv: str
    cover_letter: str
    why_good_fit: List[str]

# ==================== AGENT STATE & RECORDS ====================


class TailoredMaterials(BaseModel):
    """The custom content generated for a specific job"""
    job_id: str
    tailored_cv: str
    tailored_cover_letter: str


class ApplicationRecord(BaseModel):
    """The final log of an application attempt"""
    id: str
    job_id: str
    status: ApplicationStatus
    applied_at: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = None
    notes: Optional[str] = None


class AgentState(BaseModel):
    """
    The global state of our agent workflow.
    Simple. Typed. Effective.
    """
    user_profile: UserProfile

    # The list of all jobs (Inventory)
    jobs: List[Job] = Field(default_factory=list)

    # Counters / Stats for Dashboard
    jobs_scraped_count: int = 0
    jobs_applied_count: int = 0

    # Application Logs (Section 7)
    applications: List[ApplicationRecord] = Field(default_factory=list)
