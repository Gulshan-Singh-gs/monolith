import sys
import shutil
import tempfile
import pytest
from pathlib import Path

# Add project root to sys.path so tests can import server, core, etc.
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.mkdtemp(prefix="sov_test_ws_")
    ws_path = Path(temp_dir).resolve()
    # Create sample files
    (ws_path / "main.py").write_text("print('Hello Sovereign\n')", encoding="utf-8")
    (ws_path / "README.md").write_text("# Test Project", encoding="utf-8")
    yield ws_path
    shutil.rmtree(temp_dir, ignore_errors=True)

