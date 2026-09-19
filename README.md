---
title: NotebookLM Clone
emoji: 📚
colorFrom: blue
colorTo: purple
sdk: gradio
python_version: "3.11"
app_file: app.py
short_description: Notebook-based source chat and study artifacts
---

# NotebookLM Clone

A Gradio application for collecting sources in separate notebooks, asking source-grounded questions, and generating Markdown reports and quizzes. Sources can be PDF, PPTX, TXT, or a public web page. The app stores notebook contents locally and uses Hugging Face Inference Providers for answer and artifact generation.

## Run locally

Use Python 3.11. From the directory containing `app.py`:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, create a Hugging Face user access token with permission to call Inference Providers, and set `HF_INFERENCE_TOKEN` in `.env`. Then start the app:

```bash
python app.py
```

You can instead set `HF_INFERENCE_TOKEN` in your shell (PowerShell: `$env:HF_INFERENCE_TOKEN = "your-token"`; macOS/Linux: `export HF_INFERENCE_TOKEN="your-token"`). Shell settings take precedence over `.env`. The example file [.env.example](.env.example) lists supported settings; keep real tokens only in the Git-ignored `.env` file or a secret manager. Restart the app after changing `.env`.

The first embedding run downloads `sentence-transformers/all-MiniLM-L6-v2`, so first ingestion may take longer and needs network access. Generation also needs network access and Hugging Face inference credits. Notebook and source storage works without an inference token. Hugging Face currently includes a small monthly free credit allowance; check its [current pricing](https://huggingface.co/docs/inference-providers/pricing) before a live demo.

| Setting | Purpose | Default |
| --- | --- | --- |
| `HF_INFERENCE_TOKEN` | Hugging Face user access token for answers, reports, and quizzes | Required for generation |
| `HF_MODEL` | Chat model served by Hugging Face Inference Providers | `Qwen/Qwen3-4B-Instruct-2507` |
| `HF_PROVIDER` | Provider selection; `auto` lets Hugging Face choose | `auto` |
| `NOTEBOOKLM_DATA_DIR` | Local notebook database and Markdown artifacts | `data/` locally; `/data` if that directory exists |
| `NOTEBOOKLM_DB_PATH` | Optional explicit SQLite file location | `NOTEBOOKLM_DATA_DIR/notebooklm.db` |

## Use the app

1. Create a notebook, select it, and optionally rename it. Each notebook keeps its own sources, chat history, and artifacts. Deleting a notebook deletes its stored content.
2. Upload a PDF, PPTX, or TXT file, or add a public web URL. Wait for the ingestion status before asking questions. Scanned PDFs without extractable text require OCR before upload.
   Each upload is limited to 30 MB, and extracted text is limited to 500,000 characters or 400 chunks so ingestion remains practical on a small Space.
3. Ask a question about the active notebook. The app retrieves matching source chunks, asks the configured Hugging Face model to answer from those chunks, and displays source references with the answer. Switch notebooks to view their previous conversations.
4. Generate a report or quiz. The quiz includes an answer key. View the Markdown in the app or download the `.md` file.

Only upload material you are comfortable sending through Hugging Face Inference Providers to the selected provider. Retrieved source excerpts are included in generation requests. Public deployments share one local app storage area; this project has no user authentication or per-person isolation.

## How it works

The app extracts text from each source, splits it into chunks, embeds chunks with `all-MiniLM-L6-v2`, and stores vectors, extracted text, and source metadata in a notebook-scoped SQLite database. Retrieval compares vector similarity; the evaluation also compares a hybrid search approach that adds lexical matching. Relevant excerpts and source labels become the grounded context for the Hugging Face chat model. Reports and quizzes use notebook source content and are saved as Markdown.

See [ARCHITECTURE.md](ARCHITECTURE.md) for modules, data flow, and deployment design. See [EVALUATION.md](EVALUATION.md) and [EVALUATION_RUN.md](EVALUATION_RUN.md) for the measured vector versus hybrid retrieval comparison. Generated answer quality still needs a run with a Hugging Face inference token.

To try a fictional sample corpus, run `python scripts/seed_examples.py`. It prints the new notebook ID. The two source files and five questions are in [examples](examples/).

## Data and deployment

Local data lives under `NOTEBOOKLM_DATA_DIR` (default `data/` locally, or `/data` if available) and survives an ordinary local app restart. The data directory and common SQLite file extensions are ignored by Git. Back it up separately if needed. The app keeps original PDF, PPTX, and TXT uploads under `sources/<notebook-id>/`; SQLite keeps extracted text, chunks, embeddings, chat, and artifact records. Removing a source or notebook removes its saved original files. Web pages are saved as extracted text in SQLite, not as raw HTML.

To deploy, create a **Gradio** Hugging Face Space and set `HF_INFERENCE_TOKEN` as a Space secret. Optionally set `HF_MODEL`, `HF_PROVIDER`, and `NOTEBOOKLM_DATA_DIR` as Space variables. A default Space has ephemeral disk: notebook data can disappear when the Space restarts, rebuilds, or stops. For durable deployment, attach a Hugging Face Storage Bucket as a writable volume and set `NOTEBOOKLM_DATA_DIR` to a directory under its mount point. This project does not configure a bucket automatically. The README YAML above identifies `app.py` as the Space entry point; `requirements.txt` supplies its Python dependencies.

The GitHub workflow in [.github/workflows/deploy.yml](.github/workflows/deploy.yml) syncs each push to `main` to a Space. Configure these **GitHub Actions secrets** before running it:

| Secret | Value |
| --- | --- |
| `HF_TOKEN` | Fine-grained Hugging Face token with write access to the target Space |
| `HF_SPACE_REPO_ID` | Target Space ID, such as `account/space-name` |

The Space needs its **own** `HF_INFERENCE_TOKEN` secret; GitHub's `HF_TOKEN` deploy secret only publishes files and is not passed to the running Space. GitHub Actions uploads repository files to the Space and excludes `.git/` and `.github/`. Check the Space build logs and perform a live source/chat/artifact smoke test after the first deploy.

GitHub repository: [PrachiPatel556/ITCS_5010_NotebookLM](https://github.com/PrachiPatel556/ITCS_5010_NotebookLM). Add the live Space URL and a 1–2 minute screen recording to the project submission after deployment. [DEMO_SCRIPT.md](DEMO_SCRIPT.md) gives a short recording sequence. These external deliverables require the owner's Hugging Face and GitHub credentials and are not represented as complete here.

## References

- [Hugging Face Spaces configuration](https://huggingface.co/docs/hub/spaces-config-reference)
- [Hugging Face Spaces dependencies](https://huggingface.co/docs/hub/spaces-dependencies)
- [Hugging Face GitHub Actions sync](https://huggingface.co/docs/hub/spaces-github-actions)
- [Hugging Face Spaces disk usage](https://huggingface.co/docs/hub/spaces-storage)
