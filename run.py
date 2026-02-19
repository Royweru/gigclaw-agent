# run.py -- GigClaw Entry Point

"""
One-command entry point for GigClaw.

Usage:
    python run.py setup      -- Initialize directories and config
    python run.py run        -- Run the full agent pipeline
    python run.py scrape     -- Refresh job data from RemoteOK
    python run.py status     -- View project stats and configuration
    python run.py report     -- Display the latest session report
    python run.py --help     -- Show all available commands
"""

from app.cli.commands import app

if __name__ == "__main__":
    app()
