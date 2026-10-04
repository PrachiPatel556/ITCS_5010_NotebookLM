# Deployment demonstration script (about 90 seconds)

Record the browser and keep the Hugging Face Space URL visible. Use the fictional files in `examples/` so no private data appears in the recording.

- Live Space: [prachi2712/itcs-5010-notebooklm](https://huggingface.co/spaces/prachi2712/itcs-5010-notebooklm)
- Successful deployment run: [GitHub Actions run 37138123769](https://github.com/PrachiPatel556/ITCS_5010_NotebookLM/actions/runs/37138123769)

| Time | Show | Narration cue |
| --- | --- | --- |
| 0–15 s | Open the live Space and create a notebook called `Campus climate plan`. | “The app is running on Hugging Face Spaces.” |
| 15–35 s | Upload `examples/campus_climate_plan.txt` and `examples/campus_climate_meeting.txt`. | “Each source is extracted, chunked, embedded, and stored in this notebook.” |
| 35–55 s | Ask “What is the emissions target and baseline year?” and point to `[S1]` and the source list below the answer. | “The answer uses retrieved notebook excerpts and cites its sources.” |
| 55–70 s | Generate a quiz, open its answer key, and click the Markdown download. | “Artifacts are saved per notebook and can be downloaded.” |
| 70–90 s | Open the GitHub Actions `Deploy to Hugging Face Space` run with a green success status; return to the Space URL. | “A push to `main` deployed this version through GitHub Actions.” |

The recording must show an actual successful deployment and generated answer. After uploading the video, add its URL to the README and the course submission.
