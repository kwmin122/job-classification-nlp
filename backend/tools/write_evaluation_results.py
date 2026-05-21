from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "evaluation-results.md"

COMMANDS = [
    (
        "Backend Tests",
        [sys.executable, "-m", "unittest", "discover", "-s", "backend/tests"],
        ROOT,
    ),
    (
        "Learning Resource DB Audit",
        [sys.executable, "backend/tools/audit_learning_resources.py"],
        ROOT,
    ),
    (
        "Recommendation Metrics",
        [sys.executable, "backend/tools/evaluate_recommendations.py"],
        ROOT,
    ),
    (
        "Frontend Build",
        ["npm", "run", "build"],
        ROOT / "frontend",
    ),
]


def run_command(title: str, command: list[str], cwd: Path) -> tuple[str, int]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "backend"
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    command_text = " ".join(command)
    section = "\n".join(
        [
            f"## {title}",
            "",
            f"Command: `{command_text}`",
            "",
            f"Exit code: `{result.returncode}`",
            "",
            "```text",
            output,
            "```",
            "",
        ]
    )
    return section, result.returncode


def main() -> None:
    sections = [
        "# Evaluation Results",
        "",
        "Generated: 2026-05-21",
        "",
    ]
    failed = False
    for title, command, cwd in COMMANDS:
        section, returncode = run_command(title, command, cwd)
        sections.append(section)
        if returncode != 0:
            failed = True

    OUTPUT.write_text("\n".join(sections), encoding="utf-8")
    print(f"wrote={OUTPUT}")
    if failed:
        raise SystemExit("FAIL: one or more evaluation commands failed")


if __name__ == "__main__":
    main()
