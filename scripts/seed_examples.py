"""Create a notebook with the fictional evaluation sources; prints its ID."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from notebooklm.ingest import ingest_file  # noqa: E402
from notebooklm.storage import NotebookStore  # noqa: E402


def main() -> None:
    store = NotebookStore()
    notebook = store.create_notebook("Campus climate plan (example)")
    for filename in ("campus_climate_plan.txt", "campus_climate_meeting.txt"):
        ingest_file(store, notebook["id"], ROOT / "examples" / filename)
    print(notebook["id"])


if __name__ == "__main__":
    main()
