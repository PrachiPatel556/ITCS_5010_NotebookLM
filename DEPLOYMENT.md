# Deploy to Hugging Face Spaces from GitHub

This repository has the two YAML pieces needed for automatic deployment:

- `.github/workflows/deploy.yml` is the GitHub Actions workflow. It syncs each push to `main` to a Hugging Face Space.
- The YAML header at the top of `README.md` is the Space configuration. Hugging Face uses it to select Gradio, run `app.py`, and preload the embedding and chat models during the build. Hugging Face does not need a separate `space.yaml` file.

The model files are downloaded by the Space during its build. GitHub Actions only uploads this repository's code and configuration. Answers are generated on the Space's CPU, without an Inference Providers API token or per-request inference credits.

## One-time setup

1. Sign in to Hugging Face as `prachi2712`. Open [Create a new Space](https://huggingface.co/new-space), choose a name such as `notebooklm-clone`, select **Gradio**, select **CPU Basic**, and create the Space. Use public visibility if your class needs to open the demonstration URL. The resulting Space ID is `prachi2712/notebooklm-clone` if you used that name. Use the actual name in all later steps. Hugging Face currently requires a paid plan to create a new Gradio Space, although CPU Basic has no hourly charge. If your account already has a Gradio Space, you can use that Space ID instead. [Space creation and hardware terms](https://huggingface.co/docs/hub/spaces-overview)
2. In [Hugging Face access tokens](https://huggingface.co/settings/tokens), create a fine-grained token with **write access to that Space**. Copy it once. This is a deployment token; the running app does not need an inference token. [Token guidance](https://huggingface.co/docs/hub/security-tokens)
3. Open your GitHub repository, `PrachiPatel556/ITCS_5010_NotebookLM`. Go to **Settings → Secrets and variables → Actions → New repository secret**. Add `HF_TOKEN` with the token from step 2. Add `HF_SPACE_REPO_ID` with the full Space ID, for example `prachi2712/notebooklm-clone`. The username alone will not work. [GitHub secret instructions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
4. From this project directory, push the committed `main` branch: `git push origin main`. Open the repository's **Actions** tab and watch **Deploy to Hugging Face Space**. The workflow in `.github/workflows/deploy.yml` runs on every push to `main`; you can also start it with **Run workflow** after the secrets exist. [Hugging Face GitHub Actions guide](https://huggingface.co/docs/hub/spaces-github-actions)
5. Open `https://huggingface.co/spaces/prachi2712/<actual-space-name>` and watch the **Build** logs. The first build installs `requirements.txt` and preloads both public models listed in `README.md`. When the Space says **Running**, use its **App** tab to create a notebook, upload a sample TXT file, ask a question, and generate a quiz. Check the source references below the answer.

## Runtime and data

CPU Basic provides two vCPUs and 16 GB RAM. Preloading removes model downloads from the first user request, but the process still loads weights into memory when it starts, and CPU answer generation can remain slow. In a local warm check with the sample notebook, generation took about 11 seconds; a fresh Python process took much longer. This is a local measurement, not a promise for CPU Basic. The Space can sleep when idle and will then need to start again. [Hardware details](https://huggingface.co/docs/hub/spaces-gpus)

Notebook data on the default Space disk is ephemeral. Uploads, chat history, and saved artifacts can disappear after a restart or rebuild. For a durable deployment, mount a Hugging Face Storage Bucket and point `NOTEBOOKLM_DATA_DIR` to its mount path. The app has no visitor authentication, so use public demonstration documents on a public Space. [Space storage](https://huggingface.co/docs/hub/spaces-storage)

If the GitHub Action fails, check that both secret names match exactly and that the token can write to the target Space. If the Space build fails, inspect its Build logs. If chat is slow after the Space is running, check the Run logs and test again after the models have loaded. The local `.env` file is ignored by Git and is not deployed.
