# RAG retrieval and answer evaluation

Run date: **2026-10-04**

Corpus: `campus_climate_plan.txt` and `campus_climate_meeting.txt` (four chunks).

Configuration:

- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`, normalized on CPU
- Retrieval: cosine vector search versus hybrid vector/lexical rank fusion
- Production top-k: 3 chunks
- Generation: Groq `openai/gpt-oss-20b`, temperature 0
- Retrieval timing: warmed local model; generation timing: live Space round-trip
- Isolation: identical vector and hybrid notebooks with separate chat histories

Scoring uses the 1-5 criteria defined in [EVALUATION.md](EVALUATION.md).

## Question 1: What is the emissions reduction target and baseline year?

Expected answer: Northbridge College targets a 35 percent reduction in operational greenhouse-gas emissions by 2030 compared with 2022.

### Vector

Retrieval time: **19.70 ms**.

1. `campus_climate_meeting.txt`, chunk 1, score 0.503 - budget allocations and the October audit
2. `campus_climate_meeting.txt`, chunk 2, score 0.456 - offsets, shuttle deadline, and no named dean
3. `campus_climate_plan.txt`, chunk 2, score 0.455 - projects, audit, and quarterly public record

Generated answer (live round-trip **1,806.66 ms**):

> I couldn't find any mention of an emissions-reduction target or a baseline year in the provided excerpts.

Human answer quality: **2/5**.

Assessment: the target chunk was ranked fourth and excluded from the production context. The refusal was properly grounded and contained no unsupported claim, but it did not provide the expected fact.

### Hybrid

Retrieval time: **19.41 ms**.

1. `campus_climate_meeting.txt`, chunk 1, score 0.088 - budget allocations and the October audit
2. `campus_climate_plan.txt`, chunk 1, score 0.078 - 35 percent target, 2030 deadline, and 2022 baseline
3. `campus_climate_plan.txt`, chunk 2, score 0.077 - projects, audit, and quarterly public record

Generated answer (live round-trip **1,619.85 ms**):

> The target is a 35% reduction in operational greenhouse-gas emissions by 2030, using the 2022 baseline year as the reference point [S2].

Human answer quality: **5/5**.

Assessment: complete and correct; `[S2]` directly supports every factual element.

## Question 2: How will people check progress on LEAF-7?

Expected answer: The LEAF-7 dashboard publishes quarterly energy and emissions updates with the 2022 baseline, metered versus estimated figures, and explained revisions.

### Vector

Retrieval time: **17.38 ms**.

1. `campus_climate_plan.txt`, chunk 2, score 0.475 - LEAF-7 as the public quarterly record
2. `campus_climate_meeting.txt`, chunk 1, score 0.386 - quarterly updates, baseline, measurement type, and revisions
3. `campus_climate_plan.txt`, chunk 1, score 0.250 - quarterly dashboard progress table

Generated answer (live round-trip **1,564.91 ms**):

> People can view the quarterly progress on the LEAF-7 dashboard, which publishes energy and emissions updates (starting with a 2022 baseline table) each quarter. [S1][S2]

Human answer quality: **4/5**.

Assessment: correct and cited, but it omits that the dashboard distinguishes metered values from estimates and explains revisions.

### Hybrid

Retrieval time: **18.58 ms**.

1. `campus_climate_plan.txt`, chunk 2, score 0.091 - LEAF-7 as the public quarterly record
2. `campus_climate_meeting.txt`, chunk 1, score 0.081 - quarterly updates, baseline, measurement type, and revisions
3. `campus_climate_plan.txt`, chunk 1, score 0.079 - quarterly dashboard progress table

Generated answer (live round-trip **1,747.37 ms**):

> People can view the quarterly progress tables on the public LEAF-7 dashboard, which publishes energy use, estimated emissions and the difference from the 2022 baseline each quarter [S1][S2].

Human answer quality: **4/5**.

Assessment: correct and cited, but it does not mention the metered-versus-estimated distinction or explained revisions.

## Question 3: When must the diesel shuttles be replaced, and how much money was reserved for that work?

Expected answer: All six diesel shuttles are to be replaced by June 2027; the committee reserved 400,000 dollars for vehicles and chargers.

### Vector

Retrieval time: **19.91 ms**.

1. `campus_climate_meeting.txt`, chunk 2, score 0.532 - six-shuttle June 2027 deadline
2. `campus_climate_plan.txt`, chunk 1, score 0.376 - shuttle replacement project
3. `campus_climate_meeting.txt`, chunk 1, score 0.343 - 400,000-dollar vehicle and charger allocation

Generated answer (live round-trip **2,592.11 ms**):

> The diesel shuttles must be replaced by June 2027, and $400,000 was reserved for that work. [S1][S3]

Human answer quality: **5/5**.

Assessment: complete multi-source answer; `[S1]` supports the date and `[S3]` supports the budget.

### Hybrid

Retrieval time: **28.82 ms**.

1. `campus_climate_meeting.txt`, chunk 2, score 0.091 - six-shuttle June 2027 deadline
2. `campus_climate_plan.txt`, chunk 1, score 0.081 - shuttle replacement project
3. `campus_climate_meeting.txt`, chunk 1, score 0.079 - 400,000-dollar vehicle and charger allocation

Generated answer (live round-trip **2,683.85 ms**):

> The diesel shuttles must be replaced by June 2027, and $400,000 was reserved for that work. [S1][S3]

Human answer quality: **5/5**.

Assessment: complete multi-source answer with both claims mapped to the relevant excerpts.

## Question 4: Why did the committee reject carbon offsets?

Expected answer: Offsets would not reduce energy consumed by campus buildings or vehicles, so the committee favored direct reduction measures.

### Vector

Retrieval time: **22.49 ms**.

1. `campus_climate_meeting.txt`, chunk 2, score 0.627 - explicit reason for rejecting offsets
2. `campus_climate_meeting.txt`, chunk 1, score 0.618 - direct project funding
3. `campus_climate_plan.txt`, chunk 2, score 0.365 - measuring reductions rather than treating offsets as equivalent

Generated answer (live round-trip **1,557.20 ms**):

> The committee rejected carbon offsets because they would not reduce the energy consumed by campus buildings or vehicles. [S1]

Human answer quality: **5/5**.

Assessment: concise, correct, and directly supported by `[S1]`.

### Hybrid

Retrieval time: **21.82 ms**.

1. `campus_climate_meeting.txt`, chunk 2, score 0.088 - explicit reason for rejecting offsets
2. `campus_climate_meeting.txt`, chunk 1, score 0.086 - direct project funding
3. `campus_climate_plan.txt`, chunk 2, score 0.077 - measuring reductions rather than treating offsets as equivalent

Generated answer (live round-trip **1,732.51 ms**):

> The committee rejected carbon offsets because they would not reduce the energy consumed by campus buildings or vehicles. [S1]

Human answer quality: **5/5**.

Assessment: concise, correct, and directly supported by `[S1]`.

## Question 5: What is the dean's name?

Expected answer: The sources do not name a dean. A grounded answer should say this information is unavailable.

### Vector

Retrieval time: **18.26 ms**.

1. `campus_climate_meeting.txt`, chunk 2, score 0.161 - explicitly states that no dean was named
2. `campus_climate_plan.txt`, chunk 1, score 0.067 - plan overview and target
3. `campus_climate_plan.txt`, chunk 2, score -0.002 - projects and audit

Generated answer (live round-trip **1,866.39 ms**):

> No dean is named in the excerpts. [S1]

Human answer quality: **5/5**.

Assessment: correct refusal to invent a name; `[S1]` explicitly supports the absence.

### Hybrid

Retrieval time: **21.21 ms**.

1. `campus_climate_meeting.txt`, chunk 2, score 0.091 - explicitly states that no dean was named
2. `campus_climate_plan.txt`, chunk 1, score 0.054 - plan overview and target
3. `campus_climate_plan.txt`, chunk 2, score 0.050 - projects and audit

Generated answer (live round-trip **1,875.23 ms**):

> No dean is named in the excerpts. [S1]

Human answer quality: **5/5**.

Assessment: correct refusal to invent a name; `[S1]` explicitly supports the absence.

## Results and conclusion

| Metric | Vector | Hybrid |
| --- | ---: | ---: |
| Complete supporting context in top 3 | 4/5 | 5/5 |
| Answer-quality total | 21/25 | 24/25 |
| Mean answer quality | 4.2/5 | 4.8/5 |
| Median retrieval latency | 19.70 ms | 21.21 ms |
| Median live answer round-trip | 1,806.66 ms | 1,747.37 ms |

Hybrid retrieval is the selected default. It recovered the exact target-and-baseline chunk that vector retrieval placed outside the production top three, raising complete-context coverage from four to five questions and mean answer quality from 4.2 to 4.8. Its 1.51 ms median retrieval overhead is operationally negligible compared with the roughly 1.7-1.8 second generation round-trip. The small timing difference in end-to-end responses is dominated by network and provider variability, so the quality improvement—not speed—is the reason for selecting hybrid.
