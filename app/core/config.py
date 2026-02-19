from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    """Application configuration loaded from the .env file"""
    #API KEYS
    openai_api_key:str
    
    ai_provider:str = "openai"
    model:str
    #file paths
    data_dir:Path = Path("data")
    user_dir:Path = Path("data/user")
    
    #Agent behavior
    max_jobs_per_run : int = 50
    min_match_score:int = 75
    auto_apply:bool = False
    
    #storage files
    @property
    def jobs_file(self) ->Path:
        "Path to jobs.json"
        return self.data_dir/"jobs.json"
    @property
    def applications_file(self) ->Path:
        "Path to applications.json"
        return self.data_dir/"applications.json"
    
    @property
    def user_profile(self) ->Path:
        "Path to user profile"
        return self.user_dir/"profile.json"
    @property
    def cv_file(self) -> Path:
        """Path to CV text file"""
        return self.user_dir / "cv.txt"
    
    @property
    def cover_letter_file(self) -> Path:
        """Path to cover letter template"""
        return self.user_dir / "cover_letter.txt"
    
    class Config:
        env_file =".env"
        extra = "ignore"
        case_sensitive= False
        env_file_encoding = "utf-8"
        
settings = Settings()


