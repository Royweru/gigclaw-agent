# app/core/setup.py

from pathlib import Path
from app.core.config import settings

def initialize_data_directories():
    """Create the data directory structure if it doesn't exist"""
    
    # Create directories
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.user_dir.mkdir(parents=True, exist_ok=True)
    
    print(f" Data directories created:")
    print(f"   - {settings.data_dir}")
    print(f"   - {settings.user_dir}")
    
    # Create placeholder CV if missing
    if not settings.cv_file.exists():
        placeholder_cv = """John Doe
Senior Python Developer

EXPERIENCE:
- 5 years building web applications with Django and FastAPI
- Expert in Python, PostgreSQL, Docker, AWS
- Built production AI agents using LangChain and GPT-4

SKILLS:
Python, JavaScript, React, Docker, PostgreSQL, AWS, LangChain, OpenAI API

EDUCATION:
B.S. Computer Science, 2018
"""
        settings.cv_file.write_text(placeholder_cv, encoding='utf-8')
        print(f" Created placeholder CV at {settings.cv_file}")
    
    # Create placeholder cover letter if missing
    if not settings.cover_letter_file.exists():
        placeholder_cover = """Dear Hiring Manager,

I am excited to apply for the [ROLE] position at [COMPANY]. With 5 years of experience in Python development 
and a proven track record of building scalable applications, I believe I would be a strong fit for your team.

[CUSTOM_CONTENT]

I look forward to discussing how my skills align with your needs.

Best regards,
John Doe
"""
        settings.cover_letter_file.write_text(placeholder_cover, encoding='utf-8')
        print(f" Created placeholder cover letter at {settings.cover_letter_file}")