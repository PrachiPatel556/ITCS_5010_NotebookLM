# Deploy to Hugging Face Spaces from GitHub

This repository has the two YAML pieces needed for automatic deployment:

- `.github/workflows/deploy.yml` is the GitHub Actions workflow. It syncs each push to `main` to a Hugging Face Space.
- The YAML header at the top of `README.md` is the Space configuration. Hugging Face uses it to select Gradio, run `app.py`, and preload the embedding and chat models during the build. Hugging Face does not need a separate `space.yaml` file.

The model files are downloaded by the Space during its build. GitHub Actions only uploads this repository's code and configuration. On ZeroGPU, answers use the Space's shared GPU through `spaces.GPU`, without an Inference Providers API token or per-request inference credits.

## One-time setup

1. Sign in to Hugging Face as `prachi2712`. Check that your email is verified and the account is more than 30 days old. Hugging Face currently allows accounts meeting those conditions to host up to **two ZeroGPU Spaces for free**. [ZeroGPU eligibility](https://huggingface.co/docs/hub/spaces-zerogpu)
2. Open [Create a new Space](https://huggingface.co/new-space), choose a name such as `notebooklm-clone`, select **Gradio** as the SDK and **ZeroGPU** as the hardware, and create the Space. Use public visibility if your class needs to open the demonstration URL. The resulting Space ID is `prachi2712/notebooklm-clone` if you used that name. Use the actual name in all later steps. CPU Basic Gradio creation requires a paid plan; selecting ZeroGPU is the free eligible path. [Space creation rules](https://huggingface.co/docs/hub/spaces-overview)
3. In [Hugging Face access tokens](https://huggingface.co/settings/tokens), create a fine-grained token with **write access to that Space**. Copy it once. This is a deployment token; the running app does not need an inference token. [Token guidance](https://huggingface.co/docs/hub/security-tokens)
4. Open your GitHub repository, `PrachiPatel556/ITCS_5010_NotebookLM`. Go to **Settings → Secrets and variables → Actions → New repository secret**. Add `HF_TOKEN` with the token from step 3. Add `HF_SPACE_REPO_ID` with the full Space ID, for example `prachi2712/notebooklm-clone`. The username alone will not work. [GitHub secret instructions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
5. From this project directory, push the committed `main` branch: `git push origin main`. Open the repository's **Actions** tab and watch **Deploy to Hugging Face Space**. The workflow in `.github/workflows/deploy.yml` runs on every push to `main`; you can also start it with **Run workflow** after the secrets exist. [Hugging Face GitHub Actions guide](https://huggingface.co/docs/hub/spaces-github-actions)
6. Open `https://huggingface.co/spaces/prachi2712/<actual-space-name>` and watch the **Build** logs. The first build installs `requirements.txt` and preloads both public models listed in `README.md`. When the Space says **Running**, use its **App** tab to create a notebook, upload a sample TXT file, ask a question, and generate a quiz. Check the source references below the answer.

## Runtime and data

ZeroGPU uses a shared GPU queue and daily usage limits. Hugging Face currently lists five minutes of daily GPU time for a logged-in free user and two minutes for an unauthenticated visitor. Model weights are registered when the Space starts; the first GPU request can still need queue and worker startup time. The local CPU check took about 11 seconds after models were warm, which is not a ZeroGPU benchmark. [ZeroGPU limits](https://huggingface.co/docs/hub/spaces-zerogpu)

Gradio Lite can run in a free **Static** Space, but it executes Python in each visitor's browser through Pyodide. This repository's server-side PyTorch models, SQLite notebook storage, and ingestion pipeline are not a drop-in Gradio Lite app. Selecting Static without rewriting those parts would break the application. [Gradio Lite runtime](https://gradio.app/4.44.1/guides/gradio-lite), [Static Spaces](https://huggingface.co/docs/hub/spaces-sdks-static)

Notebook data on the default Space disk is ephemeral. Uploads, chat history, and saved artifacts can disappear after a restart or rebuild. For a durable deployment, mount a Hugging Face Storage Bucket and point `NOTEBOOKLM_DATA_DIR` to its mount path. The app has no visitor authentication, so use public demonstration documents on a public Space. [Space storage](https://huggingface.co/docs/hub/spaces-storage)

If the GitHub Action fails, check that both secret names match exactly and that the token can write to the target Space. If the Space build fails, inspect its Build logs. If chat is slow after the Space is running, check the Run logs and test again after the models have loaded. The local `.env` file is ignored by Git and is not deployed.
