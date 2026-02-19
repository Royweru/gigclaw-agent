#app/scrapers/remoteok.py

from app.scrapers.base import BaseScrapper
from app.core.models import JobSource,ApplicationStatus,Job
from app.core.config import settings

import httpx
import hashlib
import re
import time
from typing import List,Optional

class RemoteOkScrapper(BaseScrapper):
    """Scrapper for RemoteOk's public JSON API"""
    API_URL = "https://remoteok.com/api"
    
    def get_source_name(self)->str:
        return "RemoteOk"
    
    def scrape(self) ->List[Job] :
        """Fetch remote jobs from the RemoteOk API"""
        print(f"Scraping {self.get_source_name()}")
        
        try:
            response = httpx.get(
                self.API_URL,
                headers={"User-Agent":"Gigclaw/1.0"},
                timeout= 30.0
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"Api returned error {e.response.status_code}")
            return []
        except httpx.NetworkError as e:
            print(f"Network error : {e}")
            return []
        
        raw_jobs = response.json()
        raw_jobs = raw_jobs[1:] if raw_jobs else []
        
        #Apply limit
        raw_jobs = raw_jobs[:settings.max_jobs_per_run]
        
        jobs = []
        
        for raw in raw_jobs:
            job= self._normalize(raw)
            if job:
                jobs.append(job)
                
        print(f"Scraped {len(jobs)} jobs from {self.get_source_name()}")
        return jobs            
    
    def _normalize(self, raw: dict) -> Optional[Job]:
        """Convert raw API data into a validated Job model"""
        try:
            # Generate unique ID from slug
            slug = raw.get("slug", "")
            job_id = hashlib.md5(f"remoteok-{slug}".encode()).hexdigest()[:12]

            # Build the URL
            url = f"https://remoteok.com/remote-jobs/{slug}"

            # Clean the description (strip HTML tags)
            description = raw.get("description", "")
            description = re.sub(r"<[^>]+>", "", description)  # Remove HTML
            description = description.strip()[:2000]  # Limit length

            # Format salary
            salary = self._format_salary(
                raw.get("salary_min"), raw.get("salary_max")
            )

            # Extract tags
            tags = raw.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]

            # Build the Job model — Pydantic validates everything
            return Job(
                id=job_id,
                source=JobSource.REMOTE_OK,
                url=url,
                title=raw.get("position", "Unknown Title"),
                company=raw.get("company", "Unknown Company"),
                description=description or "No description available",
                location=raw.get("location", "Remote"),
                salary=salary,
                tags=tags,
                posted_date=raw.get("date", ""),
                status=ApplicationStatus.DISCOVERED,
            )

        except Exception as e:
            # If one job fails, don't crash the whole scrape
            print(f"Skipping malformed job: {e}")
            return None

    def _format_salary(self, min_sal, max_sal) -> Optional[str]:
        """Format salary range into a readable string"""
        try:
            if min_sal and max_sal:
                return f"${int(min_sal):,} - ${int(max_sal):,}"
            elif min_sal:
                return f"${int(min_sal):,}+"
            elif max_sal:
                return f"Up to ${int(max_sal):,}"
        except (ValueError, TypeError):
            pass
        return None