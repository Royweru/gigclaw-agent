# GigClaw -- AI-Powered Job Application Agent

An educational project that teaches you how to build an AI-powered job application agent from scratch using **LangGraph** orchestration, **OpenAI** for intelligent matching, and **Playwright** for browser automation.

## What It Does

GigClaw automates the job hunting workflow:

1. **Scrapes** remote job listings from RemoteOK
2. **Matches** jobs to your profile using AI (GPT-5 nano)
3. **Tailors** your CV and cover letter for each match
4. **Applies** to jobs via browser automation (Playwright)
5. **Reports** everything in timestamped Markdown files

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/Royweru/gigclaw.git
cd gigclaw
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` with your real API key:

```
OPENAI_API_KEY=sk-proj-your-real-key-here
MODEL=gpt-5-nano
```

### 3. Setup

```bash
python run.py setup
```

### 4. Run

```bash
python run.py run
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `python run.py setup` | Initialize directories and verify config |
| `python run.py run` | Run the full 5-node agent pipeline |
| `python run.py scrape` | Refresh job data from RemoteOK |
| `python run.py status` | View job stats and configuration |
| `python run.py report` | Display the latest session report |
| `python run.py --help` | Show all available commands |

## Architecture

```
Scrape --> Match --> Tailor --> Apply --> Report --> END
  |          |         |         |          |
  v          v         v         v          v
RemoteOK   GPT-5    GPT-5   Playwright   Markdown
  API      nano     nano    (Browser)     Report
```

### Project Structure

```
gigaclaw/
├── run.py                    # Entry point
├── run.bat                   # Windows shortcut
├── .env                      # Your config (git-ignored)
├── .env.example              # Config template
├── requirements.txt          # Python dependencies
├── app/
│   ├── ai/                   # AI engine (LangChain multi-provider)
│   │   ├── engine.py         # Direct OpenAI integration
│   │   ├── providers.py      # LangChain multi-provider factory
│   │   └── prompts.py        # System prompts for matching/tailoring
│   ├── automation/           # Browser automation
│   │   ├── browser.py        # BrowserManager (Playwright singleton)
│   │   └── applicator.py     # GenericFormFiller (heuristic form filling)
│   ├── cli/                  # Command-line interface
│   │   └── commands.py       # All CLI commands (Typer + Rich)
│   ├── core/                 # Core business logic
│   │   ├── config.py         # Settings (Pydantic + .env)
│   │   ├── models.py         # Data models (Job, UserProfile, AgentState)
│   │   ├── setup.py          # Directory initialization
│   │   └── storage.py        # JSON persistence layer
│   ├── graph/                # LangGraph orchestration
│   │   ├── nodes.py          # 5 pipeline nodes
│   │   └── workflow.py       # StateGraph definition
│   └── scrapers/             # Job board scrapers
│       ├── base.py           # Abstract base class
│       ├── remoteok.py       # RemoteOK implementation
│       └── runner.py         # Scraper orchestrator
├── data/                     # Runtime data (git-ignored)
│   ├── jobs.json             # Scraped job listings
│   ├── reports/              # Session reports
│   ├── screenshots/          # Playwright screenshots
│   └── user/                 # User profile + CV
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | -- | Your OpenAI API key |
| `MODEL` | No | `gpt-5-nano` | OpenAI model to use |
| `MAX_JOBS_PER_RUN` | No | `50` | Max jobs to process per run |
| `MIN_MATCH_SCORE` | No | `75.0` | Minimum AI match score (0-100) |
| `AUTO_APPLY` | No | `false` | Skip human approval |

## Adding New Scrapers

The scraper architecture uses abstract base classes, making it easy to add new job boards:

```python
# app/scrapers/my_new_scraper.py
from app.scrapers.base import BaseScraper

class MyNewScraper(BaseScraper):
    def get_source_name(self) -> str:
        return "mysite"

    def scrape(self) -> list:
        # Your scraping logic here
        pass

    def _normalize(self, raw_data) -> list:
        # Convert to Job models
        pass
```

## Tech Stack

- **Python 3.10+**
- **LangGraph** -- Workflow orchestration
- **LangChain** -- Multi-provider AI abstraction
- **OpenAI** -- Job matching and content generation
- **Playwright** -- Browser automation
- **Typer** -- CLI framework
- **Rich** -- Terminal UI (tables, panels, colors)
- **Pydantic** -- Data validation
- **httpx** -- HTTP client for API scraping

## License

MIT
