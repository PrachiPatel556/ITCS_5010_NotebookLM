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
---

# NotebookLM Clone

A full-stack, NotebookLM-style RAG application. Users create separate notebooks, add PDF, PPTX, TXT, and public web sources, ask source-grounded questions with citations, compare retrieval strategies, and download reports or quizzes.

The deployment is designed for a student budget:

- **Hugging Face Gradio CPU Basic Space:** hosts the application with no hourly hardware charge; creating compute-backed Gradio Spaces requires an active PRO plan.
- **Local Hugging Face embedding model:** `all-MiniLM-L6-v2` runs on the Space CPU; no Hugging Face inference token or paid endpoint is used.
- **Groq free API:** generates chat answers from retrieved excerpts. The API key stays in a Space Secret.
- **SQLite:** stores notebook metadata, extracted text, vectors, chat, and artifacts without an external database bill.

The default Space filesystem is ephemeral. That is acceptable for a class demonstration, but data can disappear when the Space restarts or rebuilds.

## Features

- Multiple isolated notebooks with create, rename, switch, and delete workflows
- PDF, PPTX, TXT, single-page URL, and URL-hosted PDF ingestion
- Overlapping chunking with source metadata retained for citations
- Semantic vector retrieval and hybrid semantic/lexical retrieval
- Groq-generated answers constrained to retrieved notebook excerpts
- Visible citations with source name, chunk number, excerpt, and score
- Grounded Markdown report and quiz generation with downloads
- SQLite storage abstraction and notebook-scoped raw file/artifact folders
- Reproducible RAG evaluation script and included sample corpus
- GitHub Actions tests plus automatic Hugging Face Space deployment

## Run locally

Use Python 3.12 if possible. From the directory containing `app.py`:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, replace the placeholder with your Groq key, and start the app:

```bash
python app.py
```

Do not commit `.env`; it is already ignored. The first ingestion downloads the public MiniLM embedding model. Chat calls Groq and therefore requires internet access and `GROQ_API_KEY`. Reports and quizzes are assembled directly from cited source statements and do not make another LLM call.

| Setting | Required | Purpose | Default |
| --- | --- | --- | --- |
| `GROQ_API_KEY` | For chat | Private Groq credential | none |
| `GROQ_MODEL` | No | Groq chat model | `openai/gpt-oss-20b` |
| `GROQ_MAX_COMPLETION_TOKENS` | No | Maximum answer tokens | `350` |
| `GROQ_TIMEOUT_SECONDS` | No | Provider request timeout | `30` |
| `NOTEBOOKLM_DATA_DIR` | No | Database, uploads, and artifacts root | `data/`, or `/data` when mounted |
| `NOTEBOOKLM_DB_PATH` | No | Explicit SQLite path override | `<data-dir>/notebooklm.db` |

## Application flow

1. Create and select a notebook.
2. Upload a PDF, PPTX, or TXT file, or add a public URL. Each upload is limited to 30 MB; extracted text is limited to 500,000 characters and 400 chunks.
3. Ask a question. The app embeds the question, retrieves the top three notebook chunks, sends only those excerpts and limited conversation context to Groq, and saves the answer with citations.
4. Generate a report or quiz. The artifact is stored under that notebook, displayed in the app, and downloadable as Markdown.
5. Use the Retrieval comparison tab or `scripts/evaluate.py` to compare vector and hybrid results.

Scanned PDFs need OCR before upload. Public deployments share one app data area and do not authenticate or isolate visitors, so only use demonstration documents.

## Tests and evaluation

Run the fast suite without making model or Groq calls:

```bash
python -m unittest discover -s tests -v
```

Seed a repeatable fictional corpus and run the retrieval evaluation:

```bash
python scripts/seed_examples.py
python scripts/evaluate.py --notebook-id YOUR_ID --questions examples/questions.json --top-k 2 --output evaluation-run.md
```

Add `--generate` to evaluate Groq answers as well. See [EVALUATION.md](EVALUATION.md) and [EVALUATION_RUN.md](EVALUATION_RUN.md) for the method and recorded sample retrieval run.

## Hugging Face deployment

The complete setup is in [DEPLOYMENT.md](DEPLOYMENT.md). In short:

1. Create a public **Gradio** Space using **CPU Basic** hardware. CPU Basic has no hourly hardware charge, but Hugging Face currently requires a PRO plan to create a compute-backed Gradio Space.
2. Add `GROQ_API_KEY` under the Space's **Settings → Secrets**. Never add it as a public Variable or repository file.
3. Create a fine-grained Hugging Face write token scoped to the Space.
4. In GitHub, add `HF_TOKEN` as an Actions secret and `HF_SPACE_REPO_ID` (for example, `prachi2712/notebooklm-clone`) as an Actions variable.
5. Push `main`. [.github/workflows/deploy.yml](.github/workflows/deploy.yml) runs tests and uploads the repository to the existing Space with the official Hugging Face CLI.

GitHub Actions never receives the Groq key. Hugging Face keeps Space secrets outside the repository, so automated code syncs do not overwrite the key. Groq free-plan rate limits apply, and a public Space uses the owner's shared Groq allowance.

## Documentation

- [Architecture and data flow](ARCHITECTURE.md)
- [Deployment checklist and troubleshooting](DEPLOYMENT.md)
- [RAG evaluation method](EVALUATION.md)
- [Deployment demonstration script](DEMO_SCRIPT.md)

## Live deliverables

- GitHub repository: [PrachiPatel556/ITCS_5010_NotebookLM](https://github.com/PrachiPatel556/ITCS_5010_NotebookLM)
- Hugging Face Space: [prachi2712/itcs-5010-notebooklm](https://huggingface.co/spaces/prachi2712/itcs-5010-notebooklm)
- Direct application: [NotebookLM Clone](https://prachi2712-itcs-5010-notebooklm.hf.space/)
- Successful CI/CD deployment: [GitHub Actions run 37138123769](https://github.com/PrachiPatel556/ITCS_5010_NotebookLM/actions/runs/37138123769)
- Completed RAG comparison: [EVALUATION.md](EVALUATION.md) and [EVALUATION_RUN.md](EVALUATION_RUN.md)
- Deployment demonstration: record the 1-2 minute walkthrough in [DEMO_SCRIPT.md](DEMO_SCRIPT.md), upload it, and add the submitted recording URL here.

## References

- [Hugging Face Spaces overview](https://huggingface.co/docs/hub/en/spaces-overview)
- [Hugging Face ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu)
- [Hugging Face Space configuration](https://huggingface.co/docs/hub/spaces-config-reference)
- [Hugging Face Space storage](https://huggingface.co/docs/hub/spaces-storage)
- [Hugging Face GitHub Actions deployment](https://huggingface.co/docs/hub/spaces-github-actions)
- [Groq text generation](https://console.groq.com/docs/text-chat)
- [Groq supported models](https://console.groq.com/docs/models)
- [Groq rate limits](https://console.groq.com/docs/rate-limits)
