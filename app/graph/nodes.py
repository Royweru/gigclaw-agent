# app/graph/nodes.py

""" 
Gigclaw graph nodes - The "workers" of our state machine
Nodes read references (roles,salary,thresholds) dynamically from the state
"""

from typing import Dict, Any
from app.core.models import ApplicationRecord, ApplicationStatus,AgentState
from app.scrapers.runners import run_scraper
from app.ai.providers import LangChainAIEngine
from app.automation.applicator import GenericFormFiller
from app.automation.browser  import BrowserManager
from app.core.config import settings

#Initialize the universal AI Engine
ai_engine = LangChainAIEngine(provider=settings.ai_provider)
browser_manager = BrowserManager()
form_filler= GenericFormFiller(browser_manager)
def scrape_jobs(state:AgentState) -> Dict[str,Any]:
    """ Node 1: Hunter node
        Runs the scraper , guided by the user reference
    """
    profile= state.user_profile
    print("\nNODE: Scrape Jobs")
    print(f" Target Roles: {', '.join(profile.target_roles)}")
    print(f" Location Preferences : Remote (Hardcoded for now)")
    
    #Future : Pass profile.target_roles to the accept scraper runner !
    new_jobs = run_scraper()
    if new_jobs:
        print(f" Found {len(new_jobs)} new jobs to process")
        return {"jobs":new_jobs,"jobs_scraped_count":len(new_jobs)}
    
    #FALLBACK: grab existing unprocessed jobs from storage
    from app.core.storage import load_jobs
    all_jobs = load_jobs()
    unprocessed = [j for j in all_jobs if j.status == ApplicationStatus.DISCOVERED]
    if unprocessed:
        print(f"No new jobs , but found {len(unprocessed)} unprocessed jobs in storage")
    else:
        print("No new unprocessed jobs in the storage.Pipeline will be empty")
    return {"jobs":unprocessed,"jobs_scraped_count":len(unprocessed)}
    

def filter_jobs(state:AgentState) ->Dict[str, Any]:
    """Node 2 : The filter
        Uses AI to analyze fit based on the user's preferences and profile
    """
    print("\nNODE: Filter jobs (AI matching)")
    jobs = state.jobs
    profile = state.user_profile
    
    if not jobs:
        print("No jobs to analyze, Skipping")
        return {"jobs":[]}
    
    threshold = profile.min_match_score
    print(f"User threshold :{threshold}")
    
    #We use langchain engine to process the batch
    analysis_results = ai_engine.analyze_batch(
        jobs= jobs,
        cv_text= profile.cv_text,
        cover_letter_template = profile.cover_letter_template,
        min_score = threshold
    )
    
    #Update state with scored jobs
    scored_jobs =[]
    
    for result in analysis_results:
        job = result["job"]
        scored_jobs.append(job)
        
    return {"jobs":scored_jobs}

def tailor_application(state:AgentState) ->Dict[str,Any] :
    """ Node 3: The tailor
        Generates custom content for approved matches 
    """
    print("\nNODE: Tailor Application")
    
    jobs = state.jobs
    profile = state.user_profile
    
    updated_jobs = []
    #filter for high value targets based on the user preferences
    threshold = profile.min_match_score
    
    for job in jobs:
        if job.match_score and job.match_score >= threshold:
            print(f"Tailoring for : {job.title} {job.company}")
            
            from app.core.models import MatchResult
            match_res = MatchResult(
                match_score=job.match_score,
                reasoning=job.match_reasoning,
                key_requirements = [],
                missing_skills=[]
            )
            #Generate custom content using user specific data
            tailored= ai_engine.tailor_content(
                job,
                profile.cv_text,
                profile.cover_letter_template,
                match_res
            )
            print(f"Tailored CV and cover letter")
            job.status = ApplicationStatus.MATCHED
        
        updated_jobs.append(job)
        
    return {"jobs":updated_jobs}



def apply_to_job(state: AgentState) -> Dict[str, Any]:
    """
    Node 4: The Hand
    Uses Playwright to fill the application form.
    """
    draft_mode = not settings.auto_apply
    print("\nNODE: Apply to Job (The Hand)")

    jobs = state.jobs
    profile = state.user_profile

    # We find the ONE job that is 'MATCHED' and ready to apply
    # (In a real loop, we might process one by one)

    apps_log = []
    jobs_applied = 0

    form_filler_instance = GenericFormFiller(browser_manager)

    for job in jobs:
        if job.status == ApplicationStatus.MATCHED:
            print(f"   Applying to: {job.title} ({job.url})")

            cv_path = "data/user/cv.txt"

            try:
                form_filler_instance.fill(
                    job.url, profile, cv_path, draft_mode=True)

                job.status = ApplicationStatus.APPLIED
                jobs_applied += 1

                # Log it
                note = "Application was submitted" if not draft_mode else "Draft - Form filled only"
                apps_log.append(ApplicationRecord(
                    id=job.id if job.id else "unknown",
                    job_id=job.id if job.id else "unknown",
                    status=ApplicationStatus.APPLIED,
                    notes=note
                ))
            except Exception as e:
                print(f"   Failed to apply: {e}")
                job.status = ApplicationStatus.FAILED

    return {
        "jobs": jobs,
        "jobs_applied_count": state.jobs_applied_count + jobs_applied,
        "applications": state.applications + apps_log
    }
def generate_report(state: AgentState) -> Dict[str, Any]:
    """
    Node 5: The Mouth
    Generates a simple markdown report of the session.
    """
    print("\nNODE: Generate Report")

    # Stats
    total_found = state.jobs_scrapped_count
    total_applied = state.jobs_applied_count

    import datetime
    import os

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Simple Markdown Report
    report_lines = [
        f"# GigClaw Session Report",
        f"**Date**: {timestamp}",
        f"",
        f"## Summary",
        f"- **Jobs Found**: {total_found}",
        f"- **Jobs Applied**: {total_applied}",
        f"",
        f"## Applications",
    ]

    if not state.jobs:
        report_lines.append("_No jobs processed._")
    else:
        # Group by status
        applied_jobs = [j for j in state.jobs if j.status ==
                        ApplicationStatus.APPLIED]

        if applied_jobs:
            for job in applied_jobs:
                report_lines.append(
                    f"### [APPLIED] {job.title} @ {job.company}")
                report_lines.append(f"- **URL**: {job.url}")
                report_lines.append(f"- **Salary**: {job.salary}")
                report_lines.append(
                    f"- **Match Score**: {job.match_score}/100")
                report_lines.append(f"")
        else:
            report_lines.append("_No applications sent this session._")

        # List failures if any
        failed = [j for j in state.jobs if j.status ==
                  ApplicationStatus.FAILED]
        if failed:
            report_lines.append(f"## Failed ({len(failed)})")
            for job in failed:
                report_lines.append(f"- {job.title}: {job.url}")

    content = "\n".join(report_lines)

    # Save to file
    os.makedirs("data/reports", exist_ok=True)
    report_path = f"data/reports/report_{filename_ts}.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"   Report saved to: {report_path}")
    print(f"   Summary: Found {total_found}, Applied {total_applied}")

    return {}

