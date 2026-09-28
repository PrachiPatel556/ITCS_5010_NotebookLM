"""Compare notebook retrieval methods and write a reviewable Markdown record.

Example:
  python scripts/evaluate.py --notebook-id UUID --questions questions.json --generate --output evaluation-run.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from notebooklm.generation import answer_question  # noqa: E402
from notebooklm.service import NotebookService  # noqa: E402


def load_questions(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("The questions JSON file must contain a list.")
        questions = [
            {"question": str(item["question"]), "expected_answer": str(item.get("expected_answer", ""))}
            if isinstance(item, dict)
            else {"question": str(item), "expected_answer": ""}
            for item in data
        ]
    else:
        questions = [
            {"question": line.strip(), "expected_answer": ""}
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    if not questions or any(not entry["question"].strip() for entry in questions):
        raise ValueError("Provide at least one nonempty question.")
    return questions


def evaluate(service: NotebookService, notebook_id: str, questions: list[dict[str, str]], generate: bool,
             top_k: int = 5) -> str:
    try:
        notebook = service.store.get_notebook(notebook_id)
    except KeyError as exc:
        raise ValueError("The notebook ID does not exist.") from exc
    if not service.list_sources(notebook_id):
        raise ValueError("Add sources to the notebook before evaluating retrieval.")

    lines = [
        "# RAG retrieval evaluation",
        "",
        f"Notebook: **{notebook.get('name', notebook.get('title', notebook_id))}** (`{notebook_id}`)",
        "",
        f"Methods: cosine vector similarity; hybrid vector and lexical ranking. Top-k: {top_k}.",
        "The embedding model is warmed before each timed comparison. Timings cover retrieval only.",
        "Answer quality must be scored by a reviewer against the expected answer and cited excerpts.",
        "",
    ]
    for number, entry in enumerate(questions, 1):
        question = entry["question"].strip()
        lines.extend([f"## Question {number}: {question}", ""])
        if entry["expected_answer"]:
            lines.extend([f"Expected answer: {entry['expected_answer']}", ""])
        for result in service.compare_retrieval(notebook_id, question, top_k):
            method = result["method"]
            chunks = result["chunks"]
            lines.extend(
                [
                    f"### {method.title()}",
                    "",
                    f"Retrieval time: **{result['latency_ms']:.2f} ms**; chunks retrieved: **{len(chunks)}**.",
                    "",
                ]
            )
            for rank, chunk in enumerate(chunks, 1):
                excerpt = chunk["text"].strip().replace("\r", " ").replace("\n", " ")[:500]
                lines.extend(
                    [
                        f"{rank}. **{chunk['source_name']}**, chunk {int(chunk['chunk_index']) + 1}, "
                        f"score {chunk['score']:.3f}: {excerpt}",
                        "",
                    ]
                )
            if generate:
                started = time.perf_counter()
                answer = answer_question(question, chunks)
                generation_ms = (time.perf_counter() - started) * 1000
                lines.extend([f"Generation time: **{generation_ms:.2f} ms**.", "", "**Generated answer**", "", answer, ""])
            lines.extend(["Human answer quality (1–5): _____", "", "Notes: _____", ""])
    lines.extend(
        [
            "## Conclusion",
            "",
            "After scoring, summarize which method retrieved more relevant evidence, "
            "whether its answers were better grounded, and the latency tradeoff.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook-id", required=True, help="ID of an existing notebook")
    parser.add_argument("--questions", type=Path, required=True, help="Text lines or JSON question list")
    parser.add_argument("--output", type=Path, help="Write Markdown to this path (default: stdout)")
    parser.add_argument("--generate", action="store_true", help="Include Groq answers (requires GROQ_API_KEY)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieved chunks per method (default: 5)")
    args = parser.parse_args()

    try:
        report = evaluate(
            NotebookService(), args.notebook_id, load_questions(args.questions), args.generate, args.top_k
        )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(report, encoding="utf-8")
            print(f"Wrote {args.output}")
        else:
            print(report)
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"Evaluation failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
