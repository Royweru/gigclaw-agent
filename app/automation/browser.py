from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
from typing import Optional


class BrowserManager:
    """
    Singleton to manage the Playwright instance.
    Prevents spinning up 1000 Chrome instances.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
            cls._instance.playwright = None
            cls._instance.browser = None
        return cls._instance

    def start(self, headless: bool = False):
        """Launches the browser (Headed by default for debugging)"""
        if not self.playwright:
            print("Launching Playwright...")
            self.playwright = sync_playwright().start()

        if not self.browser:
            print(f"Launching Browser (Headless={headless})...")
            # We use stealth args to avoid basic bot detection
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )

    def new_context(self) -> tuple[BrowserContext, Page]:
        """Creates a fresh Incognito session"""
        if not self.browser:
            self.start()

        context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            # Spoof specific User Agent to look human
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        return context, page

    def stop(self):
        """Cleanup resources"""
        if self.browser:
            print("Closing Browser...")
            self.browser.close()
            self.browser = None

        if self.playwright:
            self.playwright.stop()
            self.playwright = None
