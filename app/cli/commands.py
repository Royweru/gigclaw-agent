# app/cli/commands.py
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from pathlib import Path

app = typer.Typer(
    name="gigclaw",
    help="GigClaw -- AI-Powered Job Application Agent",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


#  COMMAND: SETUP 

@app.command()
def setup():
    """Initialize data directories, placeholder files, and verify configuration."""
    from app.core.setup import initialize_data_directories
    from app.core.config import settings

    console.print(
        Panel(
            "[bold cyan]GigClaw Setup[/bold cyan]\n"
            "Initializing project directories and configuration...",
            border_style="cyan",
        )
    )

    # Create directories and placeholder files
    initialize_data_directories()

    # Build a summary table
    table = Table(title="Setup Summary",
                  show_header=True, border_style="green")
    table.add_column("Item", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Path")

    # Check directories
    data_exists = settings.data_dir.exists()
    user_exists = settings.user_dir.exists()
    table.add_row(
        "Data Directory",
        "[green]OK[/green]" if data_exists else "[red]MISSING[/red]",
        str(settings.data_dir),
    )
    table.add_row(
        "User Directory",
        "[green]OK[/green]" if user_exists else "[red]MISSING[/red]",
        str(settings.user_dir),
    )

    # Check files
    profile_exists = settings.user_profile_file.exists()
    cv_exists = settings.cv_file.exists()
    cl_exists = settings.cover_letter_file.exists()
    table.add_row(
        "User Profile",
        "[green]OK[/green]" if profile_exists else "[yellow]NEEDS SETUP[/yellow]",
        str(settings.user_profile_file),
    )
    table.add_row(
        "CV File",
        "[green]OK[/green]" if cv_exists else "[yellow]PLACEHOLDER[/yellow]",
        str(settings.cv_file),
    )
    table.add_row(
        "Cover Letter",
        "[green]OK[/green]" if cl_exists else "[yellow]PLACEHOLDER[/yellow]",
        str(settings.cover_letter_file),
    )

    # Check API key
    api_key = settings.openai_api_key
    key_status = "[red]MISSING[/red]"
    if api_key and api_key != "sk-your-real-key-here":
        key_status = f"[green]SET[/green] (...{api_key[-4:]})"
    elif api_key == "sk-your-real-key-here":
        key_status = "[yellow]PLACEHOLDER[/yellow]"
    table.add_row("OpenAI API Key", key_status, ".env")

    # Check model
    table.add_row("Model", f"[cyan]{settings.model}[/cyan]", ".env")

    console.print(table)
    console.print("\n[bold green]Setup complete![/bold green]")


#  COMMAND: RUN 

@app.command()
def run():
    """Run the full agent pipeline: Scrape -> Match -> Tailor -> Apply -> Report."""
    from app.graph.workflow import app as workflow_app
    from app.core.storage import load_user_profile

    console.print(
        Panel(
            "[bold cyan]GigClaw Agent[/bold cyan]\n"
            "Running full pipeline: Scrape -> Match -> Tailor -> Apply -> Report",
            border_style="cyan",
        )
    )

    # 1. Load User Profile
    profile = load_user_profile()
    if not profile:
        console.print("[bold red]Error: User profile not found![/bold red]")
        console.print(
            "Create [cyan]data/user/profile.json[/cyan] first.\n"
            "See [cyan]tutorial/section_06_langgraph.md[/cyan] for details."
        )
        raise typer.Exit(code=1)

    console.print(f"[green]Profile loaded:[/green] {profile.name}")
    console.print(
        f"[green]Target roles:[/green] {', '.join(profile.target_roles)}")

    # 2. Inject Profile into State
    inputs = {
        "user_profile": profile,
        "jobs": [],
        "jobs_scraped_count": 0,
        "jobs_applied_count": 0,
        "applications": [],
    }

    # 3. Run the graph
    try:
        if workflow_app:
            for output in workflow_app.stream(inputs):
                for key, value in output.items():
                    console.print(
                        f"[bold cyan]Node '{key}' completed.[/bold cyan]")

            console.print(
                Panel(
                    "[bold green]Workflow finished successfully![/bold green]",
                    border_style="green",
                )
            )
        else:
            console.print("[red]Workflow failed to compile.[/red]")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[bold red]Workflow error: {e}[/bold red]")
        raise typer.Exit(code=1)


#  COMMAND: SCRAPE 

@app.command()
def scrape():
    """Run only the scraper to refresh job data from RemoteOK."""
    from app.scrapers.runners import run_scraper

    console.print(
        Panel(
            "[bold cyan]GigClaw Scraper[/bold cyan]\n"
            "Fetching latest remote jobs from RemoteOK...",
            border_style="cyan",
        )
    )

    runner = run_scraper()
    new_jobs = runner.run()

    if not new_jobs:
        console.print("[yellow]No new jobs found (all duplicates).[/yellow]")
        return

    # Show results in a Rich table
    table = Table(
        title=f"New Jobs Found: {len(new_jobs)}", show_header=True, border_style="green")
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", style="bold")
    table.add_column("Company", style="cyan")
    table.add_column("Salary")
    table.add_column("Tags", style="dim")

    for i, job in enumerate(new_jobs[:15], 1):
        tags_str = ", ".join(job.tags[:3]) if job.tags else "N/A"
        table.add_row(
            str(i),
            job.title[:40],
            job.company[:20],
            job.salary or "Not listed",
            tags_str,
        )

    if len(new_jobs) > 15:
        table.add_row("...", f"and {len(new_jobs) - 15} more", "", "", "")

    console.print(table)
    console.print(
        f"\n[green]Saved {len(new_jobs)} new jobs to storage.[/green]")


#  COMMAND: STATUS 

@app.command()
def status():
    """Show current project status: jobs, reports, and configuration."""
    from app.core.storage import load_jobs
    from app.core.config import settings
    from app.core.models import ApplicationStatus

    console.print(
        Panel(
            "[bold cyan]GigClaw Status Dashboard[/bold cyan]",
            border_style="cyan",
        )
    )

    # --- Jobs Stats ---
    jobs = load_jobs()

    jobs_table = Table(title="Job Inventory",
                       show_header=True, border_style="blue")
    jobs_table.add_column("Status", style="bold")
    jobs_table.add_column("Count", justify="right")

    status_counts = {}
    for job in jobs:
        s = job.status.value if hasattr(
            job.status, 'value') else str(job.status)
        status_counts[s] = status_counts.get(s, 0) + 1

    for s, count in sorted(status_counts.items()):
        color = {
            "discovered": "white",
            "matched": "cyan",
            "applied": "green",
            "failed": "red",
            "skipped": "dim",
            "approved": "yellow",
        }.get(s, "white")
        jobs_table.add_row(f"[{color}]{s}[/{color}]", str(count))

    jobs_table.add_row("[bold]TOTAL[/bold]", f"[bold]{len(jobs)}[/bold]")
    console.print(jobs_table)

    # --- Reports ---
    reports_dir = Path("data/reports")
    if reports_dir.exists():
        reports = sorted(reports_dir.glob("report_*.md"), reverse=True)
        console.print(
            f"\n[bold]Reports:[/bold] {len(reports)} files in data/reports/")
        if reports:
            latest = reports[0]
            console.print(f"[green]Latest:[/green] {latest.name}")
    else:
        console.print("\n[dim]No reports directory found.[/dim]")

    # --- Config ---
    config_table = Table(title="Configuration",
                         show_header=True, border_style="yellow")
    config_table.add_column("Setting", style="bold")
    config_table.add_column("Value")

    config_table.add_row("Model", settings.model)
    config_table.add_row("Provider", settings.ai_provider)
    config_table.add_row("Max Jobs/Run", str(settings.max_jobs_per_run))
    config_table.add_row("Min Match Score", f"{settings.min_match_score}%")

    api_key = settings.openai_api_key
    if api_key and api_key != "sk-your-real-key-here":
        config_table.add_row("API Key", f"...{api_key[-4:]}")
    else:
        config_table.add_row("API Key", "[red]NOT SET[/red]")

    console.print(config_table)


#  COMMAND: REPORT 

@app.command()
def report(
    latest: bool = typer.Option(
        True, "--latest", help="Show the most recent report"),
):
    """Display a session report in the terminal."""
    reports_dir = Path("data/reports")

    if not reports_dir.exists():
        console.print("[red]No reports directory found.[/red]")
        console.print(
            "Run [cyan]python run.py run[/cyan] first to generate a report.")
        raise typer.Exit(code=1)

    reports = sorted(reports_dir.glob("report_*.md"), reverse=True)

    if not reports:
        console.print("[yellow]No reports found in data/reports/[/yellow]")
        console.print(
            "Run [cyan]python run.py run[/cyan] first to generate a report.")
        raise typer.Exit(code=1)

    if latest:
        target = reports[0]
    else:
        # Show list and let user pick
        console.print("[bold]Available Reports:[/bold]")
        for i, r in enumerate(reports[:10], 1):
            console.print(f"  {i}. {r.name}")
        target = reports[0]  # Default to latest

    # Read and render with Rich Markdown
    content = target.read_text(encoding="utf-8")

    console.print(
        Panel(
            Markdown(content),
            title=f"Report: {target.name}",
            border_style="green",
        )
    )
