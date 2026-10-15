"""Test end-to-end initialization and component rendering of app.py using Streamlit AppTest."""

from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_app_initialization_and_render():
    """Verify that app.py initializes, renders sidebar, tabs, and components without throwing exceptions."""
    app_path = Path(__file__).parent.parent / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=15)
    at.run()
    # Ensure no unhandled exceptions occurred during execution
    assert len(at.exception) == 0, f"AppTest encountered exceptions: {[e.value for e in at.exception]}"
    # Verify tabs rendered
    assert len(at.tabs) >= 5
