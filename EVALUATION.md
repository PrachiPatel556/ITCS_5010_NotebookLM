# RAG retrieval evaluation

## Methods

The application supports two notebook-scoped retrieval methods in `notebooklm/retrieval.py`:

| Method | Retrieval signal | Expected strength |
| --- | --- | --- |
| `vector` | Cosine similarity between MiniLM question and chunk embeddings | Semantically similar wording |
| `hybrid` | Reciprocal-rank fusion of vector similarity and lexical term matching | Exact names, acronyms, dates, and uncommon terms |

Both methods use the same ingested chunks, embedding model, notebook corpus, questions, and production `top_k=3`. The generation model receives only those three ranked excerpts. This keeps the comparison focused on retrieval rather than changing multiple variables at once.

## Reproduce the comparison

1. Run `python scripts/seed_examples.py` and copy the printed notebook ID.
2. Run `python scripts/evaluate.py --notebook-id YOUR_ID --questions examples/questions.json --top-k 3 --output evaluation-run.md` to record retrieved chunks and retrieval latency.
3. Add `--generate` to include Groq answers when `GROQ_API_KEY` is available locally.
4. Score every answer against its expected answer and cited excerpts. Treat an unsupported claim or irrelevant citation as an error even when the prose sounds plausible.
5. Repeat on the same machine after the embedding model is cached. Retrieval latency excludes generation; record model or network latency separately.

The checked-in run uses the fictional campus corpus so it is safe to reproduce publicly. It contains a direct fact lookup, an exact acronym, a multi-source question, a causal question, and an unanswerable question.

## Completed evaluation, 2026-10-04

The two fictional source files produced four chunks. Retrieval was timed with a warmed `all-MiniLM-L6-v2` model on Windows using production `top_k=3`. Generated answers were obtained from the deployed Hugging Face Space with Groq `openai/gpt-oss-20b`, temperature zero, and separate but identical vector and hybrid notebooks. Separate notebooks prevented one method's conversation history from affecting the other.

[EVALUATION_RUN.md](EVALUATION_RUN.md) records every question, ranked chunk, score, generated answer, citation assessment, and response time.

| Metric | Vector | Hybrid |
| --- | ---: | ---: |
| Questions with complete supporting evidence in top 3 | 4/5 | 5/5 |
| Human answer-quality total | 21/25 | 24/25 |
| Mean answer-quality score | 4.2/5 | 4.8/5 |
| Median retrieval latency | 19.70 ms | 21.21 ms |
| Median deployed answer round-trip | 1,806.66 ms | 1,747.37 ms |

### Scoring criteria

- **5:** correct and complete; factual claims have relevant citations.
- **4:** correct and grounded but omits a requested supporting detail.
- **3:** partially correct or only partially supported.
- **2:** grounded behavior, such as an appropriate refusal, but does not answer the expected fact because retrieval missed it.
- **1:** incorrect or unsupported.

Vector retrieval missed the target-and-baseline chunk for question 1. The model appropriately refused to invent an answer, which was grounded behavior but not a correct task answer. Hybrid retrieval placed the exact target chunk second and produced the complete cited answer. Both methods answered the other four questions correctly; both LEAF-7 answers omitted the requested metered-versus-estimated and revision details, so those answers scored 4 rather than 5.

## Conclusion and tradeoffs

Hybrid retrieval remains the application's default. It supplied complete top-three evidence for all five questions and improved mean answer quality from 4.2 to 4.8. Its median retrieval time was 1.51 ms slower in this run, which is negligible compared with the approximately 1.7-1.8 second deployed generation round-trip. The end-to-end timing difference favored hybrid slightly, but a five-question single run is too small to claim a generation-speed advantage because network and provider latency dominate.

The result also demonstrates why citations and retrieved excerpts matter: the vector model did not hallucinate when evidence was absent, and the visible context explains why the answer differed. The evaluation is intentionally small and fictional; broader claims would require more documents, repeated trials, and additional question types.
