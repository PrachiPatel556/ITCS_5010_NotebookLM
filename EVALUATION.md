# RAG Evaluation

## Goal

The project compares two retrieval methods using the same documents and five questions:

- **Vector retrieval** uses ChromaDB to rank MiniLM embeddings by cosine similarity.
- **Hybrid retrieval** combines the ChromaDB results with keyword matching.

Both methods return the top three chunks. Groq receives only those chunks when generating an answer.

## Test setup

The evaluation used two fictional campus climate documents containing four chunks. The embeddings were created with `all-MiniLM-L6-v2`, and answers were generated with Groq `openai/gpt-oss-20b`.

Retrieval was rerun after moving the vector index to ChromaDB. The ranked chunks and scores stayed the same, so the previously reviewed Groq answers and answer-quality scores remain applicable. The retrieval times below are from the ChromaDB run; answer response times are from the recorded live Groq run.

Answers were scored from 1 to 5:

- **5:** complete, correct, and supported by citations
- **4:** correct but missing a requested detail
- **3:** partly correct
- **2:** grounded response but missing the expected answer
- **1:** incorrect or unsupported

### Source chunks

| ID | Source | Main information |
| --- | --- | --- |
| P1 | `campus_climate_plan.txt`, chunk 1 | 35% emissions target, 2030 deadline, 2022 baseline |
| P2 | `campus_climate_plan.txt`, chunk 2 | Projects, audit, and LEAF-7 public record |
| M1 | `campus_climate_meeting.txt`, chunk 1 | Budget and LEAF-7 update details |
| M2 | `campus_climate_meeting.txt`, chunk 2 | Shuttle deadline, offsets, and no named dean |

## Results

### Question 1

**Question:** What is the emissions reduction target and baseline year?

**Expected:** A 35% reduction by 2030 compared with the 2022 baseline.

| Method | Retrieved chunks and scores | Retrieval | Answer response | Quality |
| --- | --- | ---: | ---: | ---: |
| Vector | M1 (0.503), M2 (0.456), P2 (0.455) | 69.09 ms | 1,806.66 ms | 2/5 |
| Hybrid | M1 (0.088), P1 (0.078), P2 (0.077) | 28.20 ms | 1,619.85 ms | 5/5 |

Vector did not retrieve P1 and answered that the information was unavailable. Hybrid retrieved P1 and answered that the target is a 35% reduction by 2030 using 2022 as the baseline, citing `[S2]`.

### Question 2

**Question:** How will people check progress on LEAF-7?

**Expected:** The dashboard publishes quarterly updates, the 2022 baseline, metered and estimated values, and revision explanations.

| Method | Retrieved chunks and scores | Retrieval | Answer response | Quality |
| --- | --- | ---: | ---: | ---: |
| Vector | P2 (0.475), M1 (0.386), P1 (0.250) | 21.99 ms | 1,564.91 ms | 4/5 |
| Hybrid | P2 (0.091), M1 (0.081), P1 (0.079) | 21.81 ms | 1,747.37 ms | 4/5 |

Both answers correctly described the quarterly dashboard and cited the sources. Both left out the metered-versus-estimated and revision details.

### Question 3

**Question:** When must the diesel shuttles be replaced, and how much money was reserved?

**Expected:** June 2027 and $400,000.

| Method | Retrieved chunks and scores | Retrieval | Answer response | Quality |
| --- | --- | ---: | ---: | ---: |
| Vector | M2 (0.532), P1 (0.376), M1 (0.343) | 39.23 ms | 2,592.11 ms | 5/5 |
| Hybrid | M2 (0.091), P1 (0.081), M1 (0.079) | 42.33 ms | 2,683.85 ms | 5/5 |

Both methods returned the correct date and amount with citations to M2 and M1.

### Question 4

**Question:** Why did the committee reject carbon offsets?

**Expected:** Offsets would not reduce the energy used by campus buildings or vehicles.

| Method | Retrieved chunks and scores | Retrieval | Answer response | Quality |
| --- | --- | ---: | ---: | ---: |
| Vector | M2 (0.627), M1 (0.618), P2 (0.365) | 36.00 ms | 1,557.20 ms | 5/5 |
| Hybrid | M2 (0.088), M1 (0.086), P2 (0.077) | 32.20 ms | 1,732.51 ms | 5/5 |

Both methods gave the correct supported answer and cited M2.

### Question 5

**Question:** What is the dean's name?

**Expected:** The sources do not name a dean.

| Method | Retrieved chunks and scores | Retrieval | Answer response | Quality |
| --- | --- | ---: | ---: | ---: |
| Vector | M2 (0.161), P1 (0.067), P2 (-0.002) | 35.50 ms | 1,866.39 ms | 5/5 |
| Hybrid | M2 (0.091), P1 (0.054), P2 (0.050) | 40.85 ms | 1,875.23 ms | 5/5 |

Both methods correctly said that no dean was named and did not invent an answer.

## Summary

| Metric | Vector | Hybrid |
| --- | ---: | ---: |
| Complete evidence in the top 3 | 4/5 | 5/5 |
| Total quality score | 21/25 | 24/25 |
| Average quality | 4.2/5 | 4.8/5 |
| Median retrieval time | 36.00 ms | 32.20 ms |
| Median response time | 1,806.66 ms | 1,747.37 ms |

## Conclusion

Hybrid retrieval is the default because it found all required evidence and produced the higher answer-quality score. It was 3.8 ms faster at the median in this run, but this small difference is not important compared with the roughly 1.8-second answer response time.

This is a small evaluation, so it describes the results for this sample corpus rather than proving that one method is always better.

## Reproducing the test

```bash
python scripts/seed_examples.py
python scripts/evaluate.py --notebook-id YOUR_ID --questions examples/questions.json --top-k 3 --output evaluation-run.md
```

Add `--generate` to include generated answers when `GROQ_API_KEY` is available.
