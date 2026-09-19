---
title: NotebookLM Clone
emoji: 📚
colorFrom: blue
colorTo: purple
sdk: gradio
python_version: "3.12.12"
app_file: app.py
short_description: Notebook-based source chat and study artifacts
preload_from_hub:
  - sentence-transformers/all-MiniLM-L6-v2
  - Qwen/Qwen2.5-0.5B-Instruct
---

# NotebookLM Clone

A Gradio application for collecting sources in separate notebooks, asking source-grounded questions, and generating Markdown reports and quizzes. Sources can be PDF, PPTX, TXT, or a public web page. The app stores notebook contents locally and runs a public Hugging Face language model on local CPU or Space ZeroGPU for chat. Reports and quizzes use cited source statements directly, which avoids unsupported model claims in downloadable artifacts.

## Run locally

Use Python 3.12 locally if possible; the Space uses ZeroGPU-supported Python 3.12.12. From the directory containing `app.py`:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` if you want to change its defaults. No API key is required. Start the app:

```bash
python app.py
```

The example file [.env.example](.env.example) lists supported settings. Shell settings take precedence over `.env`. Restart the app after changing `.env`. If your old `.env` contains `HF_INFERENCE_TOKEN`, you can remove it; local generation ignores it.

Locally, the first embedding run downloads `sentence-transformers/all-MiniLM-L6-v2` and the first chat answer downloads `Qwen/Qwen2.5-0.5B-Instruct` (about 1 GB of model weights). The Space preloads both during its build through the YAML above. Locally, chat runs on CPU. On a ZeroGPU Space, model weights are registered at startup and chat runs inside a `spaces.GPU` function; embeddings, ingestion, and storage remain on CPU. Neither path uses Hugging Face Inference Providers or their credits. Chat retrieves up to three chunks and limits answers to 120 tokens by default. Check model answers against the cited source excerpts. Reports and quizzes are built directly from source statements and do not require a language model download.

| Setting | Purpose | Default |
| --- | --- | --- |
| `LOCAL_LLM_MODEL` | Public chat model loaded locally or on Space ZeroGPU | `Qwen/Qwen2.5-0.5B-Instruct` |
| `LOCAL_LLM_MAX_NEW_TOKENS` | Maximum tokens per chat answer (up to 512); lower values are faster | `120` |
| `NOTEBOOKLM_DATA_DIR` | Local notebook database and Markdown artifacts | `data/` locally; `/data` if that directory exists |
| `NOTEBOOKLM_DB_PATH` | Optional explicit SQLite file location | `NOTEBOOKLM_DATA_DIR/notebooklm.db` |

## Use the app

1. Create a notebook, select it, and optionally rename it. Each notebook keeps its own sources, chat history, and artifacts. Deleting a notebook deletes its stored content.
2. Upload a PDF, PPTX, or TXT file, or add a public web URL. Wait for the ingestion status before asking questions. Scanned PDFs without extractable text require OCR before upload.
   Each upload is limited to 30 MB, and extracted text is limited to 500,000 characters or 400 chunks so ingestion remains practical on a small Space.
3. Ask a question about the active notebook. The app retrieves matching source chunks, runs the configured local model on those chunks, and displays source references with the answer. Switch notebooks to view their previous conversations.
4. Generate a report or quiz. The report lists cited source findings; the quiz makes fill-in-the-blank questions from source statements and includes a cited answer key. View the Markdown in the app or download the `.md` file.

Retrieved source excerpts stay in the running app during generation. Public deployments share one local app storage area; this project has no user authentication or per-person isolation.

## How it works

The app extracts text from each source, splits it into chunks, embeds chunks with `all-MiniLM-L6-v2`, and stores vectors, extracted text, and source metadata in a notebook-scoped SQLite database. Retrieval compares vector similarity; the evaluation also compares a hybrid search approach that adds lexical matching. Relevant excerpts and source labels become the grounded context for the local Qwen model used by chat. Reports and quizzes select cited source sentences and are saved as Markdown.

See [ARCHITECTURE.md](ARCHITECTURE.md) for modules and data flow, [DEPLOYMENT.md](DEPLOYMENT.md) for the exact Hugging Face and GitHub setup, and [EVALUATION.md](EVALUATION.md) and [EVALUATION_RUN.md](EVALUATION_RUN.md) for the measured vector versus hybrid retrieval comparison. Generated answer quality still needs a reviewed run using the local model.

To try a fictional sample corpus, run `python scripts/seed_examples.py`. It prints the new notebook ID. The two source files and five questions are in [examples](examples/).

## Data and deployment

Local data lives under `NOTEBOOKLM_DATA_DIR` (default `data/` locally, or `/data` if available) and survives an ordinary local app restart. The data directory and common SQLite file extensions are ignored by Git. Back it up separately if needed. The app keeps original PDF, PPTX, and TXT uploads under `sources/<notebook-id>/`; SQLite keeps extracted text, chunks, embeddings, chat, and artifact records. Removing a source or notebook removes its saved original files. Web pages are saved as extracted text in SQLite, not as raw HTML.

To deploy on an eligible free personal account, create a **Gradio** Hugging Face Space and choose **ZeroGPU** hardware. Hugging Face currently allows up to two free ZeroGPU Spaces for personal accounts in good standing with a verified email and an account older than 30 days. The ordinary CPU Basic Gradio creation path requires a paid plan. [ZeroGPU eligibility and runtime requirements](https://huggingface.co/docs/hub/spaces-zerogpu) No inference secret is needed. Optionally set `LOCAL_LLM_MODEL`, `LOCAL_LLM_MAX_NEW_TOKENS`, and `NOTEBOOKLM_DATA_DIR` as Space variables. If you change the model, update `preload_from_hub` above too. A default Space has ephemeral disk: notebook data can disappear when the Space restarts, rebuilds, or stops. For durable notebook data, attach a Hugging Face Storage Bucket as a writable volume and set `NOTEBOOKLM_DATA_DIR` to a directory under its mount point. This project does not configure a bucket automatically. The README YAML above identifies `app.py` as the Space entry point; `requirements.txt` supplies its Python dependencies.

The GitHub workflow in [.github/workflows/deploy.yml](.github/workflows/deploy.yml) syncs each push to `main` to a Space. GitHub Actions only publishes the repository; the Space installs dependencies, preloads the model during its build, and runs chat inference on shared ZeroGPU hardware. Model weights and notebook data are not committed to Git. Configure these **GitHub Actions secrets** before running the workflow:

| Secret | Value |
| --- | --- |
| `HF_TOKEN` | Fine-grained Hugging Face token with write access to the target Space |
| `HF_SPACE_REPO_ID` | Target Space ID, such as `account/space-name` |

For the `prachi2712` account, `HF_SPACE_REPO_ID` must include the actual Space name, for example `prachi2712/notebooklm-clone`; the username alone is insufficient. Push the committed project to the GitHub repository's `main` branch to start the workflow. The `HF_TOKEN` deployment secret only publishes files and is not passed to the running Space. GitHub Actions uploads repository files to the Space and excludes `.git/` and `.github/`. Check the Space build logs and perform a live source/chat/artifact smoke test after the first deploy. ZeroGPU requests use a shared GPU queue and daily quota; free logged-in users currently receive five minutes of daily GPU time, while unauthenticated visitors receive two minutes.

GitHub repository: [PrachiPatel556/ITCS_5010_NotebookLM](https://github.com/PrachiPatel556/ITCS_5010_NotebookLM). Add the live Space URL and a 1–2 minute screen recording to the project submission after deployment. [DEMO_SCRIPT.md](DEMO_SCRIPT.md) gives a short recording sequence. These external deliverables require the owner's Hugging Face and GitHub credentials and are not represented as complete here.

## References

- [Hugging Face Spaces configuration](https://huggingface.co/docs/hub/spaces-config-reference)
- [Hugging Face Spaces dependencies](https://huggingface.co/docs/hub/spaces-dependencies)
- [Hugging Face GitHub Actions sync](https://huggingface.co/docs/hub/spaces-github-actions)
- [Hugging Face Spaces disk usage](https://huggingface.co/docs/hub/spaces-storage)
