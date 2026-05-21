import os
import subprocess
from pathlib import Path
def test_smoke_script_passes() -> None:
    """
    Интеграционный тест: проверяет, что полный smoke-сценарий проходит.
    Требует, чтобы API был поднят (например, make prod-up).
    """
    project_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.setdefault("API_URL", "http://127.0.0.1")
    proc = subprocess.run(
        ["bash", "./scripts/smoke_prod.sh"],
        cwd=project_root,
        env=env,
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0, (
        "Smoke script failed\n"
        f"STDOUT:\n{proc.stdout}\n\n"
        f"STDERR:\n{proc.stderr}"
    )
    assert "Smoke checks passed" in proc.stdout