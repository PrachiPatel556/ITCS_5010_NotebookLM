# Deployment

The application is hosted as a Gradio Space on Hugging Face and is updated from GitHub Actions.

## Required settings

| Location | Type | Name |
| --- | --- | --- |
| Hugging Face Space | Secret | `GROQ_API_KEY` |
| GitHub Actions | Secret | `HF_TOKEN` |
| GitHub Actions | Variable | `HF_SPACE_REPO_ID` |

`HF_SPACE_REPO_ID` should contain the complete Space name:

```text
prachi2712/itcs-5010-notebooklm
```

## Hugging Face setup

1. Create a Gradio Space.
2. Open the Space settings.
3. Add `GROQ_API_KEY` under **Repository secrets**.
4. Create a fine-grained Hugging Face token with write access to this Space.

Never store the Groq key or Hugging Face token in the repository.

## GitHub setup

Open **Settings → Secrets and variables → Actions** in the GitHub repository.

1. Add the Hugging Face token as the secret `HF_TOKEN`.
2. Add the Space name as the variable `HF_SPACE_REPO_ID`.

## Deploy

Push the application to the `main` branch:

```bash
git add .
git commit -m "Update application"
git push origin main
```

The workflow in `.github/workflows/deploy.yml` runs the tests and then uploads the project to the Hugging Face Space. The Space installs `requirements.txt`, creates the local ChromaDB index when sources are added, and starts `app.py`.

## Verify

After the workflow succeeds:

1. Open the Hugging Face Space and confirm it shows **Running**.
2. Create a notebook and upload one of the sample files.
3. Ask a question and confirm the answer shows citations.
4. Generate and download a report or quiz.
5. Open GitHub Actions and confirm the test and deployment jobs passed.

## Common problems

| Problem | Check |
| --- | --- |
| `HF_TOKEN` is missing | Add it under GitHub Actions secrets |
| `HF_SPACE_REPO_ID` is missing | Add the full owner/Space name under GitHub Actions variables |
| Deployment returns 401 or 403 | Check that the Hugging Face token has write access to the Space |
| The app says the Groq key is missing | Add `GROQ_API_KEY` to the Space secrets and restart it |
| The first ingestion is slow | Wait for the embedding model to finish downloading |
| Saved notebooks disappear | Recreate them after a Space restart or rebuild |
