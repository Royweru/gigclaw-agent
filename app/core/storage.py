# app/core/storage.py
import json
from pathlib import Path
from typing import List, Optional
from app.core.models import Job, UserProfile, ApplicationRecord
from app.core.config import settings

# ==================== JOBS ====================

def save_jobs(jobs: List[Job]) -> None:
    """Save jobs list to JSON file"""
    # Ensure directory exists
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert Pydantic models to dicts
    jobs_data = [job.model_dump() for job in jobs]
    
    # Write to file with pretty-printing
    with open(settings.jobs_file, 'w', encoding='utf-8') as f:
        json.dump(jobs_data, f, indent=2, default=str)
    
    print(f" Saved {len(jobs)} jobs to {settings.jobs_file}")


def load_jobs() -> List[Job]:
    """Load and validate jobs from JSON file"""
    if not settings.jobs_file.exists():
        print(f"  No jobs file found at {settings.jobs_file}")
        return []
    
    try:
        with open(settings.jobs_file, 'r', encoding='utf-8') as f:
            jobs_data = json.load(f)
        
        # Validate each job with Pydantic
        jobs = [Job(**job_dict) for job_dict in jobs_data]
        print(f" Loaded {len(jobs)} jobs from {settings.jobs_file}")
        return jobs
    
    except json.JSONDecodeError as e:
        print(f" Corrupt JSON in {settings.jobs_file}: {e}")
        return []
    except Exception as e:
        print(f" Error loading jobs: {e}")
        return []


# ==================== USER PROFILE ====================

def save_user_profile(profile: UserProfile) -> None:
    """Save user profile to JSON file"""
    settings.user_dir.mkdir(parents=True, exist_ok=True)
    
    profile_data = profile.model_dump()
    
    with open(settings.user_profile, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, indent=2)
    
    print(f" Saved user profile to {settings.user_profile}")


def load_user_profile() -> Optional[UserProfile]:
    """Load user profile from JSON file"""
    if not settings.user_profile.exists():
        print(f"No profile found at {settings.user_profile}")
        return None
    
    try:
        with open(settings.user_profile, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        profile = UserProfile(**profile_data)
        print(f"Loaded user profile for {profile.name}")
        return profile
    
    except Exception as e:
        print(f" Error loading profile: {e}")
        return None


# ==================== APPLICATIONS ====================

def save_applications(applications: List[ApplicationRecord]) -> None:
    """Save application history to JSON file"""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    
    apps_data = [app.model_dump() for app in applications]
    
    with open(settings.applications_file, 'w', encoding='utf-8') as f:
        json.dump(apps_data, f, indent=2, default=str)
    
    print(f"Saved {len(applications)} applications to {settings.applications_file}")


def load_applications() -> List[ApplicationRecord]:
    """Load application history from JSON file"""
    if not settings.applications_file.exists():
        print(f"No applications file found")
        return []
    
    try:
        with open(settings.applications_file, 'r', encoding='utf-8') as f:
            apps_data = json.load(f)
        
        applications = [ApplicationRecord(**app_dict) for app_dict in apps_data]
        print(f"Loaded {len(applications)} applications")
        return applications
    
    except Exception as e:
        print(f" Error loading applications: {e}")
        return []


# ==================== CV & COVER LETTER (TEXT FILES) ====================

def load_cv() -> str:
    """Load CV from text file"""
    if not settings.cv_file.exists():
        raise FileNotFoundError(f"CV not found at {settings.cv_file}")
    
    with open(settings.cv_file, 'r', encoding='utf-8') as f:
        return f.read()


def load_cover_letter() -> str:
    """Load cover letter template from text file"""
    if not settings.cover_letter_file.exists():
        raise FileNotFoundError(f"Cover letter not found at {settings.cover_letter_file}")
    
    with open(settings.cover_letter_file, 'r', encoding='utf-8') as f:
        return f.read()