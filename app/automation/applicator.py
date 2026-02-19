from .browser import BrowserManager
from app.core.models import UserProfile
from typing import Optional
import time
import os


class GenericFormFiller:
    """
    The 'Hand' of the agent.
    Fills standard job application forms using heuristics,
    then either submits (live mode) or holds (draft mode).
    """

    def __init__(self, browser_manager: BrowserManager):
        self.manager = browser_manager

    def _try_fill(self, page, label: str, value: str) -> bool:
        """
        Attempt to fill a field by label. Returns True if successful.
        Uses Playwright's get_by_label for accessible, human-like selection.
        """
        try:
            field = page.get_by_label(label, exact=False).first
            if field.is_visible():
                field.fill(value)
                print(f"   Filled '{label}': {value}")
                return True
        except Exception:
            pass

        # Fallback: try placeholder text
        try:
            field = page.get_by_placeholder(label, exact=False).first
            if field.is_visible():
                field.fill(value)
                print(f"   Filled '{label}' (via placeholder): {value}")
                return True
        except Exception:
            pass

        print(f"   '{label}' field not found.")
        return False

    def _try_upload_file(self, page, file_path: str) -> bool:
        """Attempt to upload a file via input[type='file']."""
        try:
            file_input = page.locator("input[type='file']").first
            if file_input.count() > 0:
                file_input.set_input_files(file_path)
                print(f"   Uploaded file: {file_path}")
                return True
        except Exception:
            pass

        print("   File upload input not found.")
        return False

    def _try_submit(self, page) -> bool:
        """
        Attempt to click a submit/apply button using heuristics.
        Searches for common button text patterns found on job application forms.
        """
        submit_patterns = [
            "Submit Application",
            "Submit",
            "Apply Now",
            "Apply",
            "Send Application",
            "Send",
        ]

        # Strategy 1: Find by button role + text
        for pattern in submit_patterns:
            try:
                btn = page.get_by_role(
                    "button", name=pattern, exact=False).first
                if btn.is_visible():
                    print(f"   Found submit button: '{pattern}'")
                    btn.click()
                    print(f"   CLICKED '{pattern}' button.")
                    return True
            except Exception:
                continue

        # Strategy 2: Find by button type="submit"
        try:
            btn = page.locator("button[type='submit']").first
            if btn.is_visible():
                text = btn.inner_text() or "submit"
                print(f"   Found type='submit' button: '{text}'")
                btn.click()
                print(f"   CLICKED submit button.")
                return True
        except Exception:
            pass

        # Strategy 3: Find by input type="submit"
        try:
            btn = page.locator("input[type='submit']").first
            if btn.is_visible():
                print(f"   Found input[type='submit']")
                btn.click()
                print(f"   CLICKED submit input.")
                return True
        except Exception:
            pass

        print("   No submit button found.")
        return False

    def fill(self, job_url: str, profile: UserProfile, cv_path: str, draft_mode: bool = True):
        """
        Navigates to URL and attempts to fill the application form.

        Args:
            job_url: The application page URL
            profile: User profile with name, email, phone, etc.
            cv_path: Path to the CV/resume file
            draft_mode: If True, fills form but does NOT submit.
                        If False, fills form AND clicks submit.
        """
        # Ensure screenshots directory exists
        os.makedirs("data/screenshots", exist_ok=True)

        # Start a fresh context (Incognito)
        context, page = self.manager.new_context()

        try:
            print(f"   Navigating to {job_url}")
            page.goto(str(job_url), timeout=30000)

            # Allow time for hydration (SPA sites)
            page.wait_for_load_state("networkidle")

            # --- FILL FIELDS USING HEURISTICS ---
            # Each _try_fill call attempts label match, then placeholder fallback

            # 1. Name
            self._try_fill(page, "Name", profile.name)

            # 2. Email
            self._try_fill(page, "Email", profile.email)

            # 3. Phone (if profile has it)
            if hasattr(profile, "phone") and profile.phone:
                self._try_fill(page, "Phone", profile.phone)

            # 4. LinkedIn (if profile has it)
            if hasattr(profile, "linkedin") and profile.linkedin:
                self._try_fill(page, "LinkedIn", profile.linkedin)

            # 5. Cover Letter text (try to paste into a textarea)
            if hasattr(profile, "cover_letter_template") and profile.cover_letter_template:
                self._try_fill(page, "Cover Letter",
                               profile.cover_letter_template[:500])

            # 6. Upload CV
            if cv_path and os.path.exists(cv_path):
                self._try_upload_file(page, cv_path)

            # --- SUBMIT OR HOLD ---
            if draft_mode:
                print("   DRAFT MODE: Form filled but NOT submitted.")
                print("   Holding browser open for 5 seconds to verify...")
                page.wait_for_timeout(5000)
            else:
                print("   LIVE MODE: Attempting to submit application...")
                submitted = self._try_submit(page)
                if submitted:
                    # Wait for confirmation page to load
                    page.wait_for_timeout(3000)
                    print("   Application submitted!")
                else:
                    print(
                        "   WARNING: Could not find submit button. Form filled but not submitted.")

            # Take a screenshot for evidence/audit
            timestamp = int(time.time())
            mode_tag = "draft" if draft_mode else "applied"
            screenshot_path = f"data/screenshots/{mode_tag}_{timestamp}.png"
            page.screenshot(path=screenshot_path)
            print(f"   Screenshot saved: {screenshot_path}")

        except Exception as e:
            print(f"   Automation Error: {e}")
            try:
                page.screenshot(
                    path=f"data/screenshots/error_{int(time.time())}.png")
            except Exception:
                pass
            raise e

        finally:
            context.close()
