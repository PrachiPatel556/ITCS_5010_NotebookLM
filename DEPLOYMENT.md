# Deployment to Hugging Face Spaces

## Recommended option

Use a **public Gradio CPU Basic Space** for the application and the **Groq free API** for chat generation.

Why this is the best fit for this project:

- The assignment requires a Hugging Face Space URL.
- CPU Basic has no hourly hardware charge; Hugging Face currently requires an active PRO plan to create a compute-backed Gradio Space.
- The public MiniLM embedding model runs locally on CPU and needs no Hugging Face inference token.
- Groq avoids loading a large chat model in the Space and uses the API key you already have.
- A Static Space is not suitable: its Python runs in the visitor's browser, cannot safely hold a shared Groq secret, and is incompatible with this server-side SQLite/upload design.

The PRO subscription is an account cost rather than an hourly CPU Basic charge. Keep the subscription active through grading so the instructor can access the deployed application.

## Secrets and variables

Three values are used, in two different systems:

| Location | Type | Name | Value |
| --- | --- | --- | --- |
| Hugging Face Space | Secret | `GROQ_API_KEY` | Your `gsk_...` Groq key |
| GitHub Actions | Secret | `HF_TOKEN` | Fine-grained HF token with write access to the Space |
| GitHub Actions | Variable | `HF_SPACE_REPO_ID` | Full Space ID, such as `prachi2712/notebooklm-clone` |

The Groq key belongs only in the Space Secret. Do not put it in GitHub, `.env.example`, a public Space Variable, source code, screenshots, or the screen recording. The Hugging Face token is only for deployment and is not passed to the running app.

## One-time setup

1. Sign in to Hugging Face and verify the account email. Confirm the account is at least 30 days old.
2. Open [Create a new Space](https://huggingface.co/new-space).
3. Choose a name such as `itcs-5010-notebooklm`, select **Gradio**, select **CPU Basic**, and use public visibility so the instructor can open it. Create the Space before running the GitHub workflow.
4. Open the Space's **Settings** page. Under **Repository secrets**, add `GROQ_API_KEY` with your real Groq key. Optionally add `GROQ_MODEL` as a non-secret Variable if you want to override `openai/gpt-oss-20b`.
5. Open [Hugging Face access tokens](https://huggingface.co/settings/tokens). Create a fine-grained token with write access only to the new Space and copy it.
6. In GitHub, open the repository and go to **Settings → Secrets and variables → Actions**.
7. Under **Secrets**, add `HF_TOKEN` with the fine-grained token.
8. Under **Variables**, add `HF_SPACE_REPO_ID` with the complete ID, for example `prachi2712/notebooklm-clone`. The username by itself is not enough. For backward compatibility, the workflow also accepts this value as a secret, but a variable is preferred because the Space ID is not sensitive.

## Deploy

Commit the application files and push the `main` branch:

```bash
git add .
git commit -m "Deploy NotebookLM with Groq generation"
git push origin main
```

Open the GitHub **Actions** tab and select **Deploy to Hugging Face Space**. The workflow:

1. installs lightweight test dependencies;
2. compiles the Python files;
3. runs the unit tests without calling Groq or downloading the embedding model;
4. installs the official Hugging Face CLI and uploads the repository to the target Space only after tests pass.

The Space must already exist because the workflow intentionally uses a fine-grained token with write access only to that Space. It does not request permission to create other repositories. The Space then installs `requirements.txt`, preloads `all-MiniLM-L6-v2` from the README metadata, and starts `app.py`. A code sync does not remove Space Secrets.

## Verify the live application

When the Space shows **Running**:

1. Confirm the page says chat is configured for Groq rather than showing the missing-key warning.
2. Create a notebook named `Campus climate plan`.
3. Upload `examples/campus_climate_plan.txt` and `examples/campus_climate_meeting.txt`.
4. Ask: `What is the emissions target and baseline year?`
5. Confirm the answer contains an `[S1]`-style marker and the UI shows the cited source excerpt.
6. Generate and download a quiz.
7. Compare vector and hybrid retrieval in the evaluation tab.
8. Record the Space and the green GitHub Actions run using [DEMO_SCRIPT.md](DEMO_SCRIPT.md).

## Storage behavior

The free Space disk is ephemeral. Notebook data can disappear after a restart, rebuild, or stop. Keep the sample source files in Git and recreate the demo notebook before recording if necessary.

If durability becomes necessary, attach a Hugging Face Storage Bucket as a read-write volume and set the Space Variable `NOTEBOOKLM_DATA_DIR` to the selected mount path. Do not point it at a read-only mount. The application will create its SQLite database, `sources/`, and `artifacts/` below that path.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Space creation asks for payment | Confirm that the personal account has an active PRO subscription and select **CPU Basic** |
| GitHub test job fails | Open the first failing test log; deployment is intentionally blocked until tests pass |
| Deploy job says `HF_TOKEN` is missing | Add it under GitHub Actions **Secrets**, not Space secrets |
| Deploy job says `HF_SPACE_REPO_ID` is missing | Add the full owner/name value under GitHub Actions **Variables** |
| Sync gets 401/403 | Confirm the token has **Write contents/settings of selected repos** for the exact Space, then replace the `HF_TOKEN` GitHub secret |
| UI says `GROQ_API_KEY` is missing | Add the key under the Space's **Repository secrets**, then restart the Space |
| Chat says Groq rejected the key | Replace/revoke the key in the Groq console, update the Space Secret, and restart |
| Chat reports a rate limit | Wait for the Groq free-plan limit to reset; all public visitors share the owner's allowance |
| Build fails while installing PyTorch | Confirm README uses Python `3.12.12` and inspect the Space build log for the first dependency error |
| Ingestion is slow on first use | The Space is downloading/warming the public embedding model; later requests reuse it |
| Notebooks disappear | Expected on ephemeral disk; use the included samples or attach a Storage Bucket |

## Official references

- [Spaces overview and current free-hosting rules](https://huggingface.co/docs/hub/en/spaces-overview)
- [ZeroGPU eligibility and limits](https://huggingface.co/docs/hub/spaces-zerogpu)
- [Space secrets and variables](https://huggingface.co/docs/hub/en/spaces-overview#managing-secrets-and-environment-variables)
- [Space disk and Storage Buckets](https://huggingface.co/docs/hub/spaces-storage)
- [GitHub Actions Space sync](https://huggingface.co/docs/hub/spaces-github-actions)
- [Groq chat completions](https://console.groq.com/docs/text-chat)
- [Groq free-plan rate limits](https://console.groq.com/docs/rate-limits)
