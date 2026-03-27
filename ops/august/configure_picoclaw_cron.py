from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def main() -> int:
    workspace = Path.home() / ".picoclaw" / "workspace"
    cron_dir = workspace / "cron"
    cron_path = cron_dir / "jobs.json"

    job_name = os.getenv("AUGUST_CRON_JOB_NAME", "august-adventure-hourly-playtest").strip() or "august-adventure-hourly-playtest"
    cron_expr = os.getenv("AUGUST_CRON_EXPR", "5 * * * *").strip() or "5 * * * *"
    run_script = os.getenv(
        "AUGUST_PLAYTEST_SCRIPT",
        "~/.picoclaw/workspace/august_adventure/ops/august/run_from_picoclaw.sh",
    ).strip()

    message = (
        "Run the August Adventure autonomous playtest now. "
        f"Execute this command exactly: /usr/bin/bash {run_script}. "
        "After it finishes, provide a brief status summary."
    )

    cron_dir.mkdir(parents=True, exist_ok=True)

    if cron_path.exists():
        data = json.loads(cron_path.read_text(encoding="utf-8"))
    else:
        data = {"version": 1, "jobs": []}

    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        jobs = []

    filtered_jobs = [job for job in jobs if str(job.get("name", "")) != job_name]
    out = {"version": 1, "jobs": filtered_jobs}
    cron_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    os.chmod(cron_path, 0o600)

    cmd = ["picoclaw", "cron", "add", "-n", job_name, "-c", cron_expr, "-m", message]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(f"failed to add cron job via picoclaw CLI: {err}")

    print(f"configured cron job '{job_name}' with expression '{cron_expr}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
