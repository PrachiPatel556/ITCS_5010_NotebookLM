"""Fast storage and RAG checks that do not download a model or call an LLM."""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from notebooklm.ingest import _check_public_http_url, chunk_text, ingest_text
from notebooklm.generation import GenerationError, _generate, create_artifact
from notebooklm.retrieval import Retriever
from notebooklm.service import NotebookService
from notebooklm.storage import NotebookStore


class CoreTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parent / ".tmp"
        root.mkdir(exist_ok=True)
        self.workdir = root / uuid4().hex
        self.workdir.mkdir()
        self.addCleanup(shutil.rmtree, self.workdir)
        self.store = NotebookStore(self.workdir / "notebooklm.db")
        self.first = self.store.create_notebook("First")
        self.second = self.store.create_notebook("Second")

    def _add(self, notebook_id: str, name: str, text: str, vector: list[float]) -> dict:
        return ingest_text(
            self.store, notebook_id, name, text,
            embedder=lambda chunks: [vector for _ in chunks],
        )

    def test_storage_survives_restart_and_isolates_notebooks(self) -> None:
        source = self._add(self.first["id"], "schedule.txt", "The deadline is Friday.", [1.0, 0.0])
        self._add(self.second["id"], "private.txt", "The budget is secret.", [0.0, 1.0])
        self.store.add_message(self.first["id"], "user", "When is the deadline?")
        reopened = NotebookStore(self.store.db_path)
        self.assertEqual(len(reopened.list_sources(self.first["id"])), 1)
        self.assertEqual(len(reopened.list_messages(self.first["id"])), 1)
        self.assertEqual(reopened.list_messages(self.second["id"]), [])
        with patch("notebooklm.retrieval.embed_texts", return_value=[[1.0, 0.0]]):
            matches = Retriever(reopened).search(self.first["id"], "deadline", method="vector")
        self.assertEqual([item["source_id"] for item in matches], [source["id"]])
        self.assertEqual(reopened.list_chunks(self.second["id"])[0]["source_name"], "private.txt")

    def test_delete_cascades_and_disabled_sources_are_excluded(self) -> None:
        source = self._add(self.first["id"], "notes.txt", "Relevant notes.", [1.0, 0.0])
        self.store.set_source_enabled(source["id"], False)
        with patch("notebooklm.retrieval.embed_texts") as embed:
            matches = Retriever(self.store).search(self.first["id"], "notes")
        self.assertEqual(matches, [])
        embed.assert_not_called()
        self.store.delete_notebook(self.first["id"])
        with self.assertRaises(KeyError):
            self.store.get_source(source["id"])
        self.assertEqual(len(self.store.list_notebooks()), 1)

    def test_service_persists_citations_and_downloadable_quiz(self) -> None:
        self._add(self.first["id"], "guide.txt", "The answer is 42.", [1.0, 0.0])
        service = NotebookService(self.store, Retriever(self.store))
        with patch("notebooklm.retrieval.embed_texts", return_value=[[1.0, 0.0]]), patch(
            "notebooklm.service.answer_question", return_value="The answer is 42. [S1]"
        ), patch(
            "notebooklm.service.create_artifact", return_value="# Quiz\n\n## Answer Key\n\n1. 42"
        ):
            answer = service.ask(self.first["id"], "What is the answer?")
            artifact = service.generate_artifact(self.first["id"], "quiz")
        self.assertIn("[S1]", answer["answer"])
        self.assertEqual(answer["citations"][0]["source_name"], "guide.txt")
        self.assertEqual(len(service.list_messages(self.first["id"])), 2)
        self.assertEqual(Path(artifact["path"]).read_text(encoding="utf-8"), artifact["content"])
        self.assertEqual(service.list_artifacts(self.first["id"])[0]["path"], artifact["path"])

    def test_uploaded_file_is_kept_per_notebook_and_removed_with_source(self) -> None:
        upload = self.workdir / "notes.txt"
        upload.write_text("A saved source.", encoding="utf-8")
        service = NotebookService(self.store)
        with patch("notebooklm.ingest.embed_texts", return_value=[[1.0, 0.0]]):
            source = service.add_files(self.first["id"], [str(upload)])[0]
        saved = service._source_dir(self.first["id"], create=False) / f"{source['id'].replace('-', '')}.txt"
        self.assertEqual(saved.read_bytes(), upload.read_bytes())
        service.delete_source(self.first["id"], source["id"])
        self.assertFalse(saved.exists())
        with patch("notebooklm.ingest.embed_texts", return_value=[[1.0, 0.0]]):
            service.add_files(self.first["id"], [str(upload)])
        service.delete_notebook(self.first["id"])
        self.assertFalse(service._source_dir(self.first["id"], create=False).exists())

    def test_chunking_progresses_with_overlap(self) -> None:
        chunks = chunk_text(" ".join(f"word{i}" for i in range(100)), chunk_size=100, overlap=20)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(chunks[0].startswith("word0"))
        self.assertIn("word99", chunks[-1])

    def test_ingestion_rejects_oversized_extracted_text_before_embedding(self) -> None:
        with patch("notebooklm.ingest.embed_texts") as embed:
            with self.assertRaisesRegex(ValueError, "500,000 character limit"):
                ingest_text(self.store, self.first["id"], "huge.txt", "A" * 500_001)
        embed.assert_not_called()

    def test_web_url_rejects_local_address(self) -> None:
        with patch("notebooklm.ingest.socket.getaddrinfo", return_value=[
            (2, 1, 6, "", ("127.0.0.1", 80))
        ]):
            with self.assertRaisesRegex(ValueError, "private or local"):
                _check_public_http_url("http://example.com/")

    def test_quiz_contains_answer_key_and_source_map(self) -> None:
        chunks = [{"source_name": "guide.txt", "chunk_index": 0,
                   "text": "The shuttle replacement deadline is June 2027. The budget for the shuttle is 400,000 dollars."}]
        with patch("notebooklm.generation._generate") as generate:
            quiz = create_artifact("quiz", chunks)
        generate.assert_not_called()
        self.assertIn("## Answer Key", quiz)
        self.assertIn("[S1] - guide.txt, chunk 1", quiz)
        self.assertIn("## Questions", quiz)
        with self.assertRaises(GenerationError):
            create_artifact("quiz", [{"source_name": "empty", "text": "Too short."}])

    def test_report_only_uses_source_statements(self) -> None:
        chunks = [{"source_name": "shuttle.txt", "chunk_index": 1,
                   "text": "The campus shuttle deadline is June 2027. The budget is 400,000 dollars."}]
        with patch("notebooklm.generation._generate") as generate:
            report = create_artifact("report", chunks)
        generate.assert_not_called()
        self.assertIn("The campus shuttle deadline is June 2027. [S1]", report)
        self.assertIn("The budget is 400,000 dollars. [S1]", report)
        self.assertIn("[S1] shuttle.txt, chunk 2", report)

    def test_generation_uses_local_model_without_an_api_token(self) -> None:
        tokenizer = MagicMock()
        tokenizer.apply_chat_template.return_value = {"input_ids": MagicMock(shape=(1, 3))}
        tokenizer.decode.return_value = "Answer [S1]"
        model = MagicMock()
        model.generate.return_value = [[1, 2, 3, 42]]
        with patch("notebooklm.generation._local_model", return_value=(tokenizer, model)) as load, patch.dict(
            "os.environ", {"LOCAL_LLM_MODEL": "Qwen/Qwen2.5-0.5B-Instruct", "HF_INFERENCE_TOKEN": "unused"}
        ):
            self.assertEqual(_generate("Question", "Use sources", 128), "Answer [S1]")
        load.assert_called_once_with("Qwen/Qwen2.5-0.5B-Instruct")
        self.assertEqual(model.generate.call_args.kwargs["max_new_tokens"], 120)

    def test_generation_explains_local_model_load_failure(self) -> None:
        with patch("notebooklm.generation._local_model", side_effect=OSError("private details")):
            with self.assertRaisesRegex(GenerationError, "local model") as error:
                _generate("Question", "Use sources", 128)
        self.assertNotIn("private details", str(error.exception))


if __name__ == "__main__":
    unittest.main()
