"""Gradio interface for the NotebookLM-style RAG application."""

from __future__ import annotations

import html
import inspect
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import gradio as gr


def _load_local_env() -> None:
    """Load simple KEY=value settings from the local, Git-ignored .env file."""
    path = Path(__file__).with_name(".env")
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and (key[0].isalpha() or key[0] == "_") and all(
            character.isalnum() or character == "_" for character in key
        ):
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            os.environ.setdefault(key, value)


_load_local_env()

from notebooklm.service import NotebookService


FILE_TYPES = [".pdf", ".pptx", ".txt"]
SOURCE_HEADERS = ["Source", "Type", "Chunks"]


@lru_cache(maxsize=1)
def _service() -> NotebookService:
    return NotebookService()


def _call(action: str, method: str, *args: Any) -> Any:
    try:
        return getattr(_service(), method)(*args)
    except gr.Error:
        raise
    except Exception as exc:
        message = str(exc).strip() or type(exc).__name__
        raise gr.Error(f"{action}: {message}") from exc


def _require_notebook(notebook_id: str | None) -> str:
    if not notebook_id:
        raise gr.Error("Create or select a notebook first.")
    return notebook_id


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _citation_text(citations: Any) -> str:
    if not citations:
        return ""
    entries = []
    for number, citation in enumerate(citations, 1):
        if isinstance(citation, str):
            entries.append(f"- **[S{number}]** {html.escape(_clean_text(citation))}")
            continue
        if not isinstance(citation, dict):
            continue
        source = html.escape(_clean_text(citation.get("source_name") or "Source"))
        index = citation.get("chunk_index")
        try:
            chunk_number = f", chunk {int(index) + 1}" if index is not None else ""
        except (TypeError, ValueError):
            chunk_number = ""
        excerpt = html.escape(_clean_text(citation.get("text")))
        if len(excerpt) > 260:
            excerpt = excerpt[:257].rstrip() + "..."
        entry = f"- **[S{number}] {source}{chunk_number}**"
        if excerpt:
            entry += f": {excerpt}"
        entries.append(entry)
    return "\n\n**Sources**\n" + "\n".join(entries) if entries else ""


def _chat_messages(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    history = []
    for message in messages:
        role = message.get("role", "assistant")
        if role not in ("user", "assistant"):
            continue
        content = str(message.get("content") or "")
        if role == "assistant":
            content += _citation_text(message.get("citations"))
        history.append({"role": role, "content": content})
    return history


def _source_payload(notebook_id: str) -> tuple[list[list[Any]], Any]:
    sources = _call("Could not load sources", "list_sources", notebook_id)
    rows = [
        [source.get("name", "Untitled"), source.get("kind", ""), source.get("chunk_count", 0)]
        for source in sources
    ]
    choices = [(source.get("name", "Untitled"), source["id"]) for source in sources]
    return rows, gr.update(choices=choices, value=None)


def _artifact_detail(artifact: dict[str, Any] | None) -> tuple[str, str | None]:
    if not artifact:
        return "Select an artifact to view it here.", None
    content = str(artifact.get("content") or "")
    path = artifact.get("path")
    download = str(path) if path and Path(path).is_file() else None
    return content or "This artifact has no saved content.", download


def _artifact_payload(notebook_id: str, selected_id: str | None = None) -> tuple[Any, str, str | None]:
    artifacts = _call("Could not load artifacts", "list_artifacts", notebook_id)
    choices = [
        (f"{artifact.get('title') or artifact.get('kind', 'Artifact')}", artifact["id"])
        for artifact in artifacts
    ]
    selected = next((artifact for artifact in artifacts if artifact.get("id") == selected_id), None)
    if selected is None and artifacts:
        selected = artifacts[0]
    content, download = _artifact_detail(selected)
    return gr.update(choices=choices, value=selected.get("id") if selected else None), content, download


def _notebook_payload(notebook_id: str | None) -> tuple[Any, Any, Any, Any, Any, Any]:
    if not notebook_id:
        return (
            [],
            gr.update(choices=[], value=None),
            [],
            gr.update(choices=[], value=None),
            "Select or create a notebook to get started.",
            None,
        )
    source_rows, source_choice = _source_payload(notebook_id)
    messages = _call("Could not load conversation", "list_messages", notebook_id)
    artifact_choice, artifact_content, artifact_file = _artifact_payload(notebook_id)
    return source_rows, source_choice, _chat_messages(messages), artifact_choice, artifact_content, artifact_file


def _workspace_payload(selected_id: str | None = None, status: str = "") -> tuple[Any, ...]:
    notebooks = _call("Could not load notebooks", "list_notebooks")
    choices = [(notebook.get("name", "Untitled"), notebook["id"]) for notebook in notebooks]
    notebook_ids = {notebook["id"] for notebook in notebooks}
    selected = selected_id if selected_id in notebook_ids else (notebooks[0]["id"] if notebooks else None)
    notebook_choice = gr.update(choices=choices, value=selected)
    return (notebook_choice, *_notebook_payload(selected), status)


def _load_workspace() -> tuple[Any, ...]:
    return _workspace_payload()


def _switch_notebook(notebook_id: str | None) -> tuple[Any, ...]:
    return (*_notebook_payload(notebook_id), "Notebook loaded." if notebook_id else "Select a notebook.")


def _create_notebook(name: str) -> tuple[Any, ...]:
    name = _clean_text(name)
    if not name:
        raise gr.Error("Enter a notebook name.")
    notebook = _call("Could not create notebook", "create_notebook", name)
    return (*_workspace_payload(notebook["id"], f"Created notebook: {name}"), "")


def _rename_notebook(notebook_id: str | None, name: str) -> tuple[Any, ...]:
    notebook_id = _require_notebook(notebook_id)
    name = _clean_text(name)
    if not name:
        raise gr.Error("Enter a new notebook name.")
    _call("Could not rename notebook", "rename_notebook", notebook_id, name)
    return (*_workspace_payload(notebook_id, f"Renamed notebook to: {name}"), "")


def _delete_notebook(notebook_id: str | None) -> tuple[Any, ...]:
    notebook_id = _require_notebook(notebook_id)
    _call("Could not delete notebook", "delete_notebook", notebook_id)
    return _workspace_payload(None, "Notebook deleted.")


def _upload_files(notebook_id: str | None, files: Any) -> tuple[Any, ...]:
    notebook_id = _require_notebook(notebook_id)
    if not files:
        raise gr.Error("Choose one or more PDF, PPTX, or TXT files.")
    if not isinstance(files, list):
        files = [files]
    paths = [os.fspath(getattr(file, "name", file)) for file in files]
    invalid = [Path(path).name for path in paths if Path(path).suffix.lower() not in FILE_TYPES]
    if invalid:
        raise gr.Error("Supported file types are PDF, PPTX, and TXT.")
    added = _call("Could not add files", "add_files", notebook_id, paths)
    return (*_source_payload(notebook_id), None, f"Added {len(added)} source(s).")


def _add_url(notebook_id: str | None, url: str) -> tuple[Any, ...]:
    notebook_id = _require_notebook(notebook_id)
    url = (url or "").strip()
    if not url:
        raise gr.Error("Enter a web URL.")
    _call("Could not add URL", "add_url", notebook_id, url)
    return (*_source_payload(notebook_id), "", "Web source added.")


def _delete_source(notebook_id: str | None, source_id: str | None) -> tuple[Any, ...]:
    notebook_id = _require_notebook(notebook_id)
    if not source_id:
        raise gr.Error("Select a source to delete.")
    _call("Could not delete source", "delete_source", notebook_id, source_id)
    return (*_source_payload(notebook_id), "Source deleted.")


def _ask(notebook_id: str | None, question: str, method: str) -> tuple[Any, ...]:
    notebook_id = _require_notebook(notebook_id)
    question = (question or "").strip()
    if not question:
        raise gr.Error("Enter a question.")
    _call("Could not answer question", "ask", notebook_id, question, method)
    messages = _call("Could not load conversation", "list_messages", notebook_id)
    return _chat_messages(messages), "", "Answer saved to this notebook."


def _generate_artifact(notebook_id: str | None, kind: str) -> tuple[Any, ...]:
    notebook_id = _require_notebook(notebook_id)
    artifact = _call(f"Could not generate {kind}", "generate_artifact", notebook_id, kind)
    return (*_artifact_payload(notebook_id, artifact.get("id")), f"{kind.title()} generated and saved.")


def _select_artifact(notebook_id: str | None, artifact_id: str | None) -> tuple[str, str | None]:
    if not notebook_id or not artifact_id:
        return _artifact_detail(None)
    artifacts = _call("Could not load artifact", "list_artifacts", notebook_id)
    artifact = next((item for item in artifacts if item.get("id") == artifact_id), None)
    if artifact is None:
        raise gr.Error("Artifact not found. Refresh the notebook and try again.")
    return _artifact_detail(artifact)


def _comparison_markdown(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No retrieval results were returned."
    sections = []
    for result in results:
        method = html.escape(_clean_text(result.get("method") or "Unknown method"))
        latency = result.get("latency_ms")
        try:
            latency_label = f"{float(latency):.1f} ms"
        except (TypeError, ValueError):
            latency_label = "Time unavailable"
        chunks = result.get("chunks") or []
        lines = [f"### {method}", f"{len(chunks)} chunks · {latency_label}"]
        for index, chunk in enumerate(chunks, start=1):
            if not isinstance(chunk, dict):
                lines.append(f"{index}. {html.escape(_clean_text(chunk))}")
                continue
            source = html.escape(_clean_text(chunk.get("source_name") or "Source"))
            chunk_index = chunk.get("chunk_index")
            try:
                number = f", chunk {int(chunk_index) + 1}" if chunk_index is not None else ""
            except (TypeError, ValueError):
                number = ""
            excerpt = html.escape(_clean_text(chunk.get("text") or chunk.get("content")))
            if len(excerpt) > 500:
                excerpt = excerpt[:497].rstrip() + "..."
            lines.append(f"{index}. **{source}{number}:** {excerpt}")
        sections.append("\n\n".join(lines))
    return "\n\n---\n\n".join(sections)


def _compare_retrieval(notebook_id: str | None, question: str) -> tuple[str, str]:
    notebook_id = _require_notebook(notebook_id)
    question = (question or "").strip()
    if not question:
        raise gr.Error("Enter an evaluation question.")
    results = _call("Could not compare retrieval methods", "compare_retrieval", notebook_id, question)
    return _comparison_markdown(results), "Retrieval comparison complete."


def build_app() -> gr.Blocks:
    with gr.Blocks(title="NotebookLM Clone") as demo:
        gr.Markdown("# NotebookLM Clone\nOrganize sources by notebook, ask grounded questions, and create study materials.")
        status = gr.Markdown("")

        with gr.Row():
            notebook = gr.Dropdown(label="Notebook", choices=[], interactive=True, scale=5)
            refresh = gr.Button("Refresh", scale=1)
        with gr.Row():
            new_name = gr.Textbox(label="New notebook name", placeholder="e.g. Research project", scale=4)
            create = gr.Button("Create notebook", variant="primary", scale=1)
        with gr.Row():
            rename_name = gr.Textbox(label="Rename selected notebook", scale=4)
            rename = gr.Button("Rename", scale=1)
            delete_notebook = gr.Button("Delete notebook", variant="stop", scale=1)

        with gr.Tabs():
            with gr.Tab("Sources"):
                gr.Markdown("Add PDF, PPTX, or TXT files, or a public web page. Sources are stored in the selected notebook.")
                source_table = gr.Dataframe(headers=SOURCE_HEADERS, datatype=["str", "str", "number"], interactive=False, label="Notebook sources")
                with gr.Row():
                    files = gr.File(label="Upload files", file_count="multiple", file_types=FILE_TYPES, type="filepath", scale=4)
                    upload = gr.Button("Add files", variant="primary", scale=1)
                with gr.Row():
                    url = gr.Textbox(label="Web URL", placeholder="https://example.com/article", scale=4)
                    add_url = gr.Button("Add URL", scale=1)
                with gr.Row():
                    source = gr.Dropdown(label="Remove source", choices=[], scale=4)
                    delete_source = gr.Button("Delete source", variant="stop", scale=1)

            with gr.Tab("Chat"):
                gr.Markdown("Answers use the selected notebook's sources. Source citations appear below each answer.")
                chatbot_options: dict[str, Any] = {"label": "Conversation", "height": 460}
                if "type" in inspect.signature(gr.Chatbot).parameters:
                    chatbot_options["type"] = "messages"
                chat = gr.Chatbot(**chatbot_options)
                method = gr.Dropdown(label="Retrieval method", choices=[("Hybrid (recommended)", "hybrid"), ("Vector", "vector")], value="hybrid")
                with gr.Row():
                    question = gr.Textbox(label="Question", placeholder="What do my sources say about ...?", lines=2, scale=5)
                    ask = gr.Button("Ask", variant="primary", scale=1)

            with gr.Tab("Artifacts"):
                gr.Markdown("Reports and quizzes are saved as Markdown files in the selected notebook.")
                with gr.Row():
                    report = gr.Button("Generate report", variant="primary")
                    quiz = gr.Button("Generate quiz with answer key")
                artifact = gr.Dropdown(label="Saved artifacts", choices=[])
                artifact_content = gr.Markdown("Select or create a notebook to get started.")
                artifact_file = gr.File(label="Download Markdown file", interactive=False)

            with gr.Tab("Retrieval comparison"):
                gr.Markdown("Compare the chunks and response times returned by the two retrieval approaches for the same question.")
                evaluation_question = gr.Textbox(label="Evaluation question", placeholder="Enter a question answerable from your sources")
                compare = gr.Button("Compare methods", variant="primary")
                comparison = gr.Markdown("")

        workspace_outputs = [notebook, source_table, source, chat, artifact, artifact_content, artifact_file, status]
        notebook_outputs = [source_table, source, chat, artifact, artifact_content, artifact_file, status]
        demo.load(_load_workspace, outputs=workspace_outputs)
        refresh.click(lambda selected: _workspace_payload(selected, "Refreshed."), inputs=notebook, outputs=workspace_outputs)
        notebook.input(_switch_notebook, inputs=notebook, outputs=notebook_outputs)
        create.click(_create_notebook, inputs=new_name, outputs=[*workspace_outputs, new_name])
        new_name.submit(_create_notebook, inputs=new_name, outputs=[*workspace_outputs, new_name])
        rename.click(_rename_notebook, inputs=[notebook, rename_name], outputs=[*workspace_outputs, rename_name])
        delete_notebook.click(_delete_notebook, inputs=notebook, outputs=workspace_outputs)
        upload.click(_upload_files, inputs=[notebook, files], outputs=[source_table, source, files, status])
        add_url.click(_add_url, inputs=[notebook, url], outputs=[source_table, source, url, status])
        url.submit(_add_url, inputs=[notebook, url], outputs=[source_table, source, url, status])
        delete_source.click(_delete_source, inputs=[notebook, source], outputs=[source_table, source, status])
        ask.click(_ask, inputs=[notebook, question, method], outputs=[chat, question, status])
        question.submit(_ask, inputs=[notebook, question, method], outputs=[chat, question, status])
        report.click(lambda selected: _generate_artifact(selected, "report"), inputs=notebook, outputs=[artifact, artifact_content, artifact_file, status])
        quiz.click(lambda selected: _generate_artifact(selected, "quiz"), inputs=notebook, outputs=[artifact, artifact_content, artifact_file, status])
        artifact.input(_select_artifact, inputs=[notebook, artifact], outputs=[artifact_content, artifact_file])
        compare.click(_compare_retrieval, inputs=[notebook, evaluation_question], outputs=[comparison, status])
        evaluation_question.submit(_compare_retrieval, inputs=[notebook, evaluation_question], outputs=[comparison, status])
    return demo


demo = build_app()


if __name__ == "__main__":
    artifact_root = (_service().store.db_path.parent / "artifacts").resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        allowed_paths=[str(artifact_root)],
        blocked_paths=[str(_service().store.db_path.resolve())],
        max_file_size="30mb",
    )
