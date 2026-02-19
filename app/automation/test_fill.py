# app/automation/test_fill.py


from app.automation.applicator import GenericFormFiller
from app.automation.browser import BrowserManager
from app.core.models import UserProfile

from pathlib import Path
import os

from app.core.config import settings
LIVE_MODE = settings.auto_apply


def test_fill():
    mode_label = "LIVE MODE — will submit" if LIVE_MODE else "DRAFT MODE — fill only"
    print(f"\n🏋️  STARTING THE SIMULATION... [{mode_label}]")

    # 1. Setup the browser and form filler
    bm = BrowserManager()
    filler = GenericFormFiller(bm)

    # 2. A fake profile — matches what a real UserProfile looks like
    profile = UserProfile(
        name="Test User",
        email="test@example.com",
        target_roles=[],
        cv_text="Test CV Content",
        cover_letter_template="Test Letter"
    )

    # 3. Path to Mock HTML (relative to this file's location)
    BASE_DIR = Path(__file__).resolve().parents[1]
    mock_path = BASE_DIR / "tests" / "fixtures" / "mock_job.html"
    mock_url = mock_path.as_uri()
    print(f"   Target: {mock_url}")

    # 4. Create a dummy CV file for the file-upload field
    dummy_cv = "app/tests/fixtures/dummy_cv.txt"
    with open(dummy_cv, "w") as f:
        f.write("This is a dummy CV for testing purposes.")

    # 5. Run the filler
    #    draft_mode=True  → fill fields, skip submit
    #    draft_mode=False → fill fields, click Submit
    try:
        filler.fill(
            job_url=mock_url,
            profile=profile,
            cv_path=dummy_cv,
            draft_mode=not LIVE_MODE   # LIVE_MODE=True → draft_mode=False → submit!
        )

        if LIVE_MODE:
            print(" TEST PASSED: Form SUBMITTED successfully.")
            print(
                "   Check the browser — you should see '🎉 Application Submitted Successfully!'")
        else:
            print(" TEST PASSED: Form FILLED successfully (no submit).")
            print("   Flip LIVE_MODE = True at the top of this file to test submission.")

    except Exception as e:
        print(f" TEST FAILED: {e}")

    finally:
        bm.stop()
        # Clean up the dummy CV
        if os.path.exists(dummy_cv):
            os.remove(dummy_cv)


if __name__ == "__main__":
    test_fill()
