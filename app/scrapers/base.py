#app/scrapers/base.py

from abc import ABC, abstractmethod
from typing import List

from app.core.models import Job


class BaseScrapper(ABC):
    """Blueprint for all the job scrappers"""
    
    @abstractmethod
    def scrape(self) -> List[Job]:
        """Fetch and return a list of validated job models"""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of the job source"""
        pass
    