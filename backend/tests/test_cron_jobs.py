"""The daily cron jobs run as `python -m app.cli.<job>` - a fresh process that
imports only what the job itself needs, unlike the web app (or this pytest
run), which has imported every model long before any query. A model missing
from app/models/__init__.py breaks mapper setup only in the fresh process,
so each job is run exactly that way here."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("module", [
    "app.cli.send_occasion_greetings",
    "app.cli.generate_festival_announcements",
])
def test_cron_job_runs_in_a_fresh_process(tmp_path, module):
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{tmp_path / 'cron.db'}", "LOG_LEVEL": "WARNING"}
    create_tables = (
        "from sqlalchemy import create_engine; import app.models; from app.models.base import Base; "
        f"Base.metadata.create_all(create_engine('{env['DATABASE_URL']}'))"
    )
    subprocess.run([sys.executable, "-c", create_tables], env=env, cwd=BACKEND, check=True, capture_output=True)

    result = subprocess.run([sys.executable, "-m", module], env=env, cwd=BACKEND, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-2000:]
