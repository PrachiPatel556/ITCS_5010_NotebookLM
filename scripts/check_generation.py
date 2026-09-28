"""Run one small Groq generation without printing credentials or source text."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from notebooklm.generation import GenerationError, _generate  # noqa: E402


def main() -> int:
    try:
        result = _generate("Reply with OK.", "Reply with exactly OK.", 16)
    except GenerationError as exc:
        print(f"Generation failed: {exc}")
        print(f"Cause: {type(exc.__cause__).__name__ if exc.__cause__ else 'none'}")
        return 1
    print(f"Generation succeeded: {bool(result)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
