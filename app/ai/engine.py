#app/ai/engine.py

from openai import OpenAI
from typing import List, Optional

from app.core.config import settings
from app.core.models import Job, MatchResult, TailoredContent
from app.ai.prompts import (
    MATCH_SYSTEM_PROMPT,
    TAILOR_SYSTEM_PROMPT,
    build_match_prompt,
    build_tailor_prompt,
)


class AIEngine:
    def __init__(self):
        """Initialize the openAI's client from the settings"""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.model
        print(f"The AI engine has being initialized (model:{self.model})")
        
    #Job matching
    def match_job(self, job: Job, cv_text: str) -> MatchResult:
        """Analyze how well a job matches the candidate's CV.

        Uses OpenAI Structured Outputs to guarantee the response
        follows our MatchResult schema exactly.

        Args:
            job: The job listing to analyze
            cv_text: The candidate's CV as plain text

        Returns:
            MatchResult with score, reasoning, requirements, and missing skills
        """
        user_prompt = build_match_prompt(
            job_title=job.title,
            job_company=job.company,
            job_description=job.description,
            cv_text=cv_text,
        )

        try:
            # The magic: parse() returns a Pydantic model directly
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": MATCH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=MatchResult,
            )

            result = completion.choices[0].message.parsed

            # Safety check: handle refusal
            if result is None:
                refusal = completion.choices[0].message.refusal
                print(f"Model refused to analyze: {refusal}")
                return MatchResult(
                    match_score=0.0,
                    reasoning=f"Model refused: {refusal}",
                    key_requirements=[],
                    missing_skills=[],
                )

            return result

        except Exception as e:
            print(f"Match analysis failed for '{job.title}': {e}")
            return MatchResult(
                match_score=0.0,
                reasoning=f"Analysis failed: {str(e)}",
                key_requirements=[],
                missing_skills=[],
            )
            
    # Content tailoring
    def tailor_content(
        self,
        job: Job,
        cv_text: str,
        cover_letter_template: str,
        match_result: MatchResult,
    ) -> TailoredContent:
        """Generate a tailored CV and cover letter for a specific job.

        Args:
            job: The target job listing
            cv_text: Original CV text
            cover_letter_template: Base cover letter template
            match_result: The match analysis (used to inform tailoring)

        Returns:
            TailoredContent with tailored_cv, cover_letter, and why_good_fit
        """
        user_prompt = build_tailor_prompt(
            job_title=job.title,
            job_company=job.company,
            job_description=job.description,
            cv_text=cv_text,
            cover_letter_template=cover_letter_template,
            match_reasoning=match_result.reasoning,
        )

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": TAILOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=TailoredContent,
            )

            result = completion.choices[0].message.parsed

            if result is None:
                refusal = completion.choices[0].message.refusal
                print(f"  Model refused to tailor: {refusal}")
                return TailoredContent(
                    tailored_cv=cv_text,
                    cover_letter=cover_letter_template,
                    why_good_fit=["Tailoring failed — using originals"],
                )

            return result

        except Exception as e:
            print(f"Content tailoring failed for '{job.title}': {e}")
            return TailoredContent(
                tailored_cv=cv_text,
                cover_letter=cover_letter_template,
                why_good_fit=[f"Tailoring failed: {str(e)}"],
            )
    
    #Batch processing
    def analyze_batch(
        self,
        jobs: List[Job],
        cv_text: str,
        cover_letter_template: str,
        min_score: Optional[float] = None,
    ) -> List[dict]:
        """Process multiple jobs: match → filter → tailor top matches.

        Args:
            jobs: List of jobs to analyze
            cv_text: Candidate's CV
            cover_letter_template: Base cover letter
            min_score: Minimum match score to tailor (defaults to settings)

        Returns:
            List of dicts with job, match_result, and tailored_content (if matched)
        """
        threshold = min_score or settings.min_match_score
        results = []

        print(f"\n🔍 Analyzing {len(jobs)} jobs (threshold: {threshold}%)...\n")

        for i, job in enumerate(jobs, 1):
            print(f"[{i}/{len(jobs)}] {job.title} @ {job.company}...", end=" ")

            # Step 1: Match
            match_result = self.match_job(job, cv_text)
            score = match_result.match_score

            # Update the job model with AI analysis
            job.match_score = score
            job.match_reasoning = match_result.reasoning

            entry = {
                "job": job,
                "match_result": match_result,
                "tailored_content": None,
            }

            if score >= threshold:
                print(f" {score}% — MATCH! Tailoring content...")

                # Step 2: Tailor (only for good matches)
                job.status = "matched"
                tailored = self.tailor_content(
                    job, cv_text, cover_letter_template, match_result
                )
                entry["tailored_content"] = tailored
            else:
                print(f" {score}% — Below threshold, skipping.")
                job.status = "skipped"

            results.append(entry)

        # Summary
        matched = sum(1 for r in results if r["tailored_content"] is not None)
        print(
            f"\n Results: {matched}/{len(jobs)} jobs matched (≥{threshold}%)")

        return results


        
