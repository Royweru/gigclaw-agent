#app/ai/providers.py

from typing import Optional,List

from app.core.config import settings
from app.core.models import MatchResult,TailoredContent,Job
from app.ai.prompts import (
    MATCH_SYSTEM_PROMPT,
    build_tailor_prompt,
    build_match_prompt,
    TAILOR_SYSTEM_PROMPT
)

def get_chat_model(provider=settings.ai_provider,model=None):
    """
     Create a LangChain chat model for any provider 
     supported: openai, anthropic , groq, gemini
    """ 
    if provider =="openai" :
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model= model or settings.model,
                           api_key=settings.openai_api_key,
                           temperature =1.0
                          )
    elif provider =="anthropic" :
        #from langchain_anthropic import ChatAnthropic
        #return ChatAnthropic(model= model or  "claude-sonnet-4-20250514",api_key= settings.anthropic_api_key)
        pass
        
    elif provider =="groq":
        #from langchain_groq import ChatGroq
        #return ChatGroq(model= model or  "llama-3.37..",api_key= settings.groq_api_key)
        pass
    
    elif provider =="gemini":
        #from langchain_google_genai import ChatGoogleGenerativeAI
        #return ChatGoogleGenerativeAI(model= model or  "gemini-2.0-flash",api_key= settings.google_api_key)
        pass  

class LangChainAIEngine:
    """Alternative AI engine using LangChain for multi-provider support.

    The magic: .with_structured_output(PydanticModel) works across ALL
    providers. Switch from GPT to Claude to Llama with ONE line change.

    Usage:
        engine = LangChainAIEngine(provider="groq", model="llama-3.3-70b-versatile")
        result = engine.match_job(job, cv_text)
    """

    def __init__(self, provider: str = settings.ai_provider, model: Optional[str] = None):
        self.llm = get_chat_model(provider, model)
        self.provider = provider
        model_name = model or self.llm.model_name if hasattr(
            self.llm, 'model_name') else "default"
        print(f"LangChain AI Engine initialized ({provider}: {model_name})")

    def match_job(self, job: Job, cv_text: str) -> MatchResult:
        """Analyze job match using the configured LLM provider."""
        # with_structured_output wraps the LLM to return Pydantic models
        structured_llm = self.llm.with_structured_output(MatchResult)

        user_prompt = build_match_prompt(
            job_title=job.title,
            job_company=job.company,
            job_description=job.description,
            cv_text=cv_text,
        )

        try:
            messages = [
                ("system", MATCH_SYSTEM_PROMPT),
                ("human", user_prompt),
            ]
            result = structured_llm.invoke(messages)
            return result

        except Exception as e:
            print(f" Match failed ({self.provider}): {e}")
            return MatchResult(
                match_score=0.0,
                reasoning=f"Analysis failed: {str(e)}",
                key_requirements=[],
                missing_skills=[],
            )

    def tailor_content(
        self,
        job: Job,
        cv_text: str,
        cover_letter_template: str,
        match_result: MatchResult,
    ) -> TailoredContent:
        """Generate tailored content using the configured LLM provider."""
        structured_llm = self.llm.with_structured_output(TailoredContent)

        user_prompt = build_tailor_prompt(
            job_title=job.title,
            job_company=job.company,
            job_description=job.description,
            cv_text=cv_text,
            cover_letter_template=cover_letter_template,
            match_reasoning=match_result.reasoning,
        )

        try:
            messages = [
                ("system", TAILOR_SYSTEM_PROMPT),
                ("human", user_prompt),
            ]
            result = structured_llm.invoke(messages)
            return result

        except Exception as e:
            print(f" Tailoring failed ({self.provider}): {e}")
            return TailoredContent(
                tailored_cv=cv_text,
                cover_letter=cover_letter_template,
                why_good_fit=[f"Tailoring failed: {str(e)}"],
            )

    def analyze_batch(
        self,
        jobs: List[Job],
        cv_text: str,
        cover_letter_template: str,
        min_score: Optional[float] = None,
    ) -> List[dict]:
        """Process multiple jobs with the configured provider."""
        threshold = min_score or settings.min_match_score
        results = []

        print(
            f"\nAnalyzing {len(jobs)} jobs via {self.provider} (threshold: {threshold}%)...\n")

        for i, job in enumerate(jobs, 1):
            print(f"[{i}/{len(jobs)}] {job.title} @ {job.company}...", end=" ")

            match_result = self.match_job(job, cv_text)
            score = match_result.match_score

            job.match_score = score
            job.match_reasoning = match_result.reasoning

            entry = {
                "job": job,
                "match_result": match_result,
                "tailored_content": None,
            }

            if score >= threshold:
                print(f" {score}% — MATCH! Tailoring...")
                job.status = "matched"
                tailored = self.tailor_content(
                    job, cv_text, cover_letter_template, match_result
                )
                entry["tailored_content"] = tailored
            else:
                print(f" {score}% — Below threshold.")
                job.status = "skipped"

            results.append(entry)

        matched = sum(1 for r in results if r["tailored_content"] is not None)
        print(f"\n Results: {matched}/{len(jobs)} matched (≥{threshold}%)")
        return results