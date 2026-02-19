#app/scrapers/runners.py

from app.scrapers.remoteok import RemoteOkScrapper
from app.core.storage import save_jobs,load_jobs


def run_scraper():
    """Scrape jobs , deduplicate , and save"""
    #Load existing jobs
    
    existing_jobs = load_jobs()
    existing_ids = {job.id for job in existing_jobs}
    
    print(f"{len(existing_jobs)} existing jobs in storage")
    
    #Scrape new jobs
    scraper = RemoteOkScrapper()
    new_jobs = scraper.scrape()
    
    #Filter out the duplicates
    unique_new = [job for job in new_jobs if job.id not in existing_ids]
    print (f"{len(unique_new)} new unique jobs (filtered {len(new_jobs) - len(unique_new)})")
    
    
    #Merge and save 
    all_jobs= existing_jobs + unique_new
    save_jobs(all_jobs)
    
    return unique_new

if __name__ == "__main__":
    jobs = run_scraper()
    for job in jobs[:5] :
        print (f"\n {'='*60}")
        print(f"{job.title}@{job.company}")
        print (f"{job.salary or 'Not listed'}")
        print(f"{','.join(job.tags[:5])}")
        print(f"{job.url}")
        