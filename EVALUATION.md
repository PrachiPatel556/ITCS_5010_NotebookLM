# RAG retrieval evaluation

## Methods

The application supports two notebook-scoped methods in `notebooklm/retrieval.py`:

| Method | Retrieval signal | Expected strength to test |
| --- | --- | --- |
| `vector` | Cosine similarity of question and chunk embeddings | Semantically related wording |
| `hybrid` | Vector similarity combined with lexical term matching | Exact names, acronyms, and uncommon terms |

Both methods use the same ingested chunks, embedding model, notebook, question set, and top-k value. This isolates the retrieval method as the changed variable. A broader evaluation would also test chunk sizes and different corpora.

## Reproduce the comparison

1. In the app, make one notebook and add at least two representative sources. Get its ID with `python -c "from notebooklm.storage import NotebookStore; print([(n['id'], n['title']) for n in NotebookStore().list_notebooks()])"`. Use documents whose content you can inspect to judge whether each retrieval is relevant. Do not use private documents in a public Space. For a repeatable fictional corpus, run `python scripts/seed_examples.py` and use the printed notebook ID.
2. Write 5–10 questions in a UTF-8 text file, one question per line, or use `examples/questions.json` with the sample corpus. Include a direct fact lookup, a paraphrase, an exact term or acronym, a question requiring information from more than one source, and a question the sources cannot answer.
3. With the same Python environment as the app, run `python scripts/evaluate.py --notebook-id YOUR_ID --questions examples/questions.json --top-k 2 --output evaluation-run.md`. The script writes per-question retrieved excerpts and retrieval time for `vector` and `hybrid`. Add `--generate` to include Groq answers; this requires `GROQ_API_KEY` and uses the account's API allowance. The script warms the embedding model before each timed comparison; rerun once after the model is cached to compare steady-state timing.
4. Inspect the retrieved chunk text/source references. For each method and question, record how many of the top-k chunks actually support an answer. Ask the app the question with the same notebook and assess answer correctness, groundedness, and citation relevance. Record unsupported claims as failures even if the answer sounds plausible.
5. Summarize the median retrieval time for each method and the number of questions with relevant top-k context. State which method you selected for the app and why, based on observed results.

Use the same machine and corpus for the timing comparison. Retrieval latency excludes model generation time. With `--generate`, the report separately records generation time for each method. Answer quality depends on both retrieval and generation, so record retrieved evidence alongside any answer judgment.

## Observed sample run, 2026-09-19

The two fictional campus climate documents in `examples/` produced four chunks. I compared five questions from `examples/questions.json` at top-k = 2, using the real `all-MiniLM-L6-v2` embedding model on Windows. [EVALUATION_RUN.md](EVALUATION_RUN.md) records each retrieved excerpt, source, rank, and measured retrieval time. In the table below, `meeting 1` means chunk 1 of `campus_climate_meeting.txt`; `plan 1` means chunk 1 of `campus_climate_plan.txt`.

| Question | Vector top 2; time | Hybrid top 2; time | Does the context support the full expected answer? |
| --- | --- | --- | --- |
| 1. Target and baseline | meeting 1, meeting 2; 61.98 ms | meeting 1, plan 1; 50.34 ms | Vector: no (35% target missing). Hybrid: yes. |
| 2. LEAF-7 progress | plan 2, meeting 1; 56.26 ms | plan 2, meeting 1; 53.78 ms | Both: yes. |
| 3. Shuttle deadline and budget | meeting 2, plan 1; 51.44 ms | meeting 2, plan 1; 63.47 ms | Both: no (budget is in meeting 1). |
| 4. Offset decision | meeting 2, meeting 1; 53.30 ms | meeting 2, meeting 1; 39.13 ms | Both: yes. |
| 5. Dean's name | meeting 2, plan 1; 50.44 ms | meeting 2, plan 1; 52.11 ms | Both: yes, by stating the sources do not name a dean. |

The median retrieval time in this single run was 53.30 ms for vector and 52.11 ms for hybrid. The difference is too small and variable to infer a speed advantage. Hybrid supplied complete evidence for four of five questions, compared with three for vector, so it is the default chat method. The app retrieves up to three chunks to keep local CPU generation practical; the two-chunk evaluation deliberately tests ranking pressure. On question 3, increasing top-k to at least three would include the budget chunk.

**Answer quality limit:** These are human judgments of whether the retrieved context contains the expected facts, not scores of generated answers. This run did not include generation, so correctness, citation placement, and generated-answer latency remain unmeasured. To complete that part of the assignment, rerun with `--generate`, review each answer against the expected answer and citations, and fill the quality fields in the run output. The five-question fictional corpus is a small smoke test, so repeat on representative project sources before making a broader quality claim.
