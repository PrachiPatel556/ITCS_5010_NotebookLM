"""Create a notebook with the fictional evaluation sources; prints its ID."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from notebooklm.service import NotebookService  # noqa: E402


def main() -> None:
    service = NotebookService()
    notebook = service.create_notebook("Campus climate plan (example)")
    service.add_files(
        notebook["id"],
        [str(ROOT / "examples" / filename) for filename in (
            "campus_climate_plan.txt", "campus_climate_meeting.txt"
        )],
    )
    print(notebook["id"])


if __name__ == "__main__":
    main()
