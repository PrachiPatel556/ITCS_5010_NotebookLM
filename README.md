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

A full-stack Retrieval-Augmented Generation (RAG) application inspired by NotebookLM. It lets users organize sources into notebooks, ask source-grounded questions with citations, and generate study materials.

## Features

- Create and manage multiple notebooks
- Add PDF, PPTX, TXT, webpage, and URL-hosted PDF sources
- Ask questions with visible source citations
- Compare vector and hybrid retrieval
- Generate downloadable reports and quizzes with answer keys
- Store notebook sources, chats, vectors, and artifacts separately

## Setup

Python 3.12 is recommended.

```bash
git clone https://github.com/PrachiPatel556/ITCS_5010_NotebookLM.git
cd ITCS_5010_NotebookLM
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies, create a `.env` file from `.env.example`, and add your `GROQ_API_KEY`.

```bash
python -m pip install -r requirements.txt
python app.py
```

Do not commit the `.env` file.

## Usage

1. Create and select a notebook.
2. Upload a supported file or add a public webpage URL.
3. Ask questions and review the cited excerpts.
4. Generate and download a report or quiz.
5. Use the retrieval comparison tab to compare vector and hybrid results.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Deployment

The application is deployed on Hugging Face Spaces. Pushes to `main` run the tests and deploy through GitHub Actions. See [DEPLOYMENT.md](DEPLOYMENT.md) for configuration details.

## Documentation

- [Architecture](ARCHITECTURE.md)
- [RAG evaluation](EVALUATION.md)
- [Deployment guide](DEPLOYMENT.md)

## Links

- [Live application](https://prachi2712-itcs-5010-notebooklm.hf.space/)
- [Hugging Face Space](https://huggingface.co/spaces/prachi2712/itcs-5010-notebooklm)
- [GitHub repository](https://github.com/PrachiPatel556/ITCS_5010_NotebookLM)
