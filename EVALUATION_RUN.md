# RAG retrieval evaluation

Notebook: **Campus climate plan (example)** (`41222e98-470a-41fc-884d-7fd84e57a13c`)

Methods: cosine vector similarity; hybrid vector and lexical ranking. Top-k: 2.
The embedding model is warmed before each timed comparison. Timings cover retrieval only.
Answer quality must be scored by a reviewer against the expected answer and cited excerpts.

## Question 1: What is the emissions reduction target and baseline year?

Expected answer: Northbridge College targets a 35 percent reduction in operational greenhouse-gas emissions by 2030 compared with 2022.

### Vector

Retrieval time: **61.98 ms**; chunks retrieved: **2**.

1. **campus_climate_meeting.txt**, chunk 1, score 0.503: Campus Sustainability Committee minutes, March 2026 The committee approved a provisional capital budget of 1.2 million dollars for the library and science hall heat-pump conversion. It reserved 400,000 dollars for the electric shuttle purchase and chargers, and 150,000 dollars for the laboratory freezer replacement program. These allocations must be confirmed after the October 2026 energy audit. The committee asked procurement to prioritize equipment that can be maintained by local technicians a

2. **campus_climate_meeting.txt**, chunk 2, score 0.456: accessible summary of the audit after completion. The committee discussed purchasing carbon offsets as a shortcut. It rejected that proposal because offsets would not reduce energy consumed by campus buildings or vehicles. Members instead supported the heat-pump, shuttle, and freezer measures in the plan. The chair noted that the six diesel shuttles must be replaced by June 2027 to keep the fleet project on schedule. No dean or university president was named in these minutes.

Human answer quality (1–5): _____

Notes: _____

### Hybrid

Retrieval time: **50.34 ms**; chunks retrieved: **2**.

1. **campus_climate_meeting.txt**, chunk 1, score 0.088: Campus Sustainability Committee minutes, March 2026 The committee approved a provisional capital budget of 1.2 million dollars for the library and science hall heat-pump conversion. It reserved 400,000 dollars for the electric shuttle purchase and chargers, and 150,000 dollars for the laboratory freezer replacement program. These allocations must be confirmed after the October 2026 energy audit. The committee asked procurement to prioritize equipment that can be maintained by local technicians a

2. **campus_climate_plan.txt**, chunk 1, score 0.078: Campus Climate Plan, approved January 2026 The fictional Northbridge College adopted a target to cut operational greenhouse-gas emissions by 35 percent by 2030, compared with its 2022 baseline. The target covers campus electricity, heating fuel, and the college shuttle fleet. It does not count student travel. Facilities will publish a quarterly progress table on the LEAF-7 dashboard. Each table will show measured energy use, estimated emissions, and the difference from the baseline. The faciliti

Human answer quality (1–5): _____

Notes: _____

## Question 2: How will people check progress on LEAF-7?

Expected answer: The LEAF-7 dashboard publishes quarterly energy and emissions updates with the 2022 baseline, metered versus estimated figures, and explained revisions.

### Vector

Retrieval time: **56.26 ms**; chunks retrieved: **2**.

1. **campus_climate_plan.txt**, chunk 2, score 0.475: units to minus 70 degrees Celsius where research protocols permit. These projects are intended to lower direct fuel use and electricity demand in different parts of the campus. The college will measure actual results rather than claiming that buying offsets is equivalent to cutting emissions. An independent energy audit is scheduled for October 2026, and the next plan update will incorporate its findings. If the audit shows slower progress than forecast, facilities must propose additional buildi

2. **campus_climate_meeting.txt**, chunk 1, score 0.386: Campus Sustainability Committee minutes, March 2026 The committee approved a provisional capital budget of 1.2 million dollars for the library and science hall heat-pump conversion. It reserved 400,000 dollars for the electric shuttle purchase and chargers, and 150,000 dollars for the laboratory freezer replacement program. These allocations must be confirmed after the October 2026 energy audit. The committee asked procurement to prioritize equipment that can be maintained by local technicians a

Human answer quality (1–5): _____

Notes: _____

### Hybrid

Retrieval time: **53.78 ms**; chunks retrieved: **2**.

1. **campus_climate_plan.txt**, chunk 2, score 0.091: units to minus 70 degrees Celsius where research protocols permit. These projects are intended to lower direct fuel use and electricity demand in different parts of the campus. The college will measure actual results rather than claiming that buying offsets is equivalent to cutting emissions. An independent energy audit is scheduled for October 2026, and the next plan update will incorporate its findings. If the audit shows slower progress than forecast, facilities must propose additional buildi

2. **campus_climate_meeting.txt**, chunk 1, score 0.081: Campus Sustainability Committee minutes, March 2026 The committee approved a provisional capital budget of 1.2 million dollars for the library and science hall heat-pump conversion. It reserved 400,000 dollars for the electric shuttle purchase and chargers, and 150,000 dollars for the laboratory freezer replacement program. These allocations must be confirmed after the October 2026 energy audit. The committee asked procurement to prioritize equipment that can be maintained by local technicians a

Human answer quality (1–5): _____

Notes: _____

## Question 3: When must the diesel shuttles be replaced, and how much money was reserved for that work?

Expected answer: All six diesel shuttles are to be replaced by June 2027; the committee reserved 400,000 dollars for vehicles and chargers.

### Vector

Retrieval time: **51.44 ms**; chunks retrieved: **2**.

1. **campus_climate_meeting.txt**, chunk 2, score 0.532: accessible summary of the audit after completion. The committee discussed purchasing carbon offsets as a shortcut. It rejected that proposal because offsets would not reduce energy consumed by campus buildings or vehicles. Members instead supported the heat-pump, shuttle, and freezer measures in the plan. The chair noted that the six diesel shuttles must be replaced by June 2027 to keep the fleet project on schedule. No dean or university president was named in these minutes.

2. **campus_climate_plan.txt**, chunk 1, score 0.376: Campus Climate Plan, approved January 2026 The fictional Northbridge College adopted a target to cut operational greenhouse-gas emissions by 35 percent by 2030, compared with its 2022 baseline. The target covers campus electricity, heating fuel, and the college shuttle fleet. It does not count student travel. Facilities will publish a quarterly progress table on the LEAF-7 dashboard. Each table will show measured energy use, estimated emissions, and the difference from the baseline. The faciliti

Human answer quality (1–5): _____

Notes: _____

### Hybrid

Retrieval time: **63.47 ms**; chunks retrieved: **2**.

1. **campus_climate_meeting.txt**, chunk 2, score 0.091: accessible summary of the audit after completion. The committee discussed purchasing carbon offsets as a shortcut. It rejected that proposal because offsets would not reduce energy consumed by campus buildings or vehicles. Members instead supported the heat-pump, shuttle, and freezer measures in the plan. The chair noted that the six diesel shuttles must be replaced by June 2027 to keep the fleet project on schedule. No dean or university president was named in these minutes.

2. **campus_climate_plan.txt**, chunk 1, score 0.081: Campus Climate Plan, approved January 2026 The fictional Northbridge College adopted a target to cut operational greenhouse-gas emissions by 35 percent by 2030, compared with its 2022 baseline. The target covers campus electricity, heating fuel, and the college shuttle fleet. It does not count student travel. Facilities will publish a quarterly progress table on the LEAF-7 dashboard. Each table will show measured energy use, estimated emissions, and the difference from the baseline. The faciliti

Human answer quality (1–5): _____

Notes: _____

## Question 4: Why did the committee reject carbon offsets?

Expected answer: Offsets would not reduce energy consumed by campus buildings or vehicles, so the committee favored direct reduction measures.

### Vector

Retrieval time: **53.30 ms**; chunks retrieved: **2**.

1. **campus_climate_meeting.txt**, chunk 2, score 0.627: accessible summary of the audit after completion. The committee discussed purchasing carbon offsets as a shortcut. It rejected that proposal because offsets would not reduce energy consumed by campus buildings or vehicles. Members instead supported the heat-pump, shuttle, and freezer measures in the plan. The chair noted that the six diesel shuttles must be replaced by June 2027 to keep the fleet project on schedule. No dean or university president was named in these minutes.

2. **campus_climate_meeting.txt**, chunk 1, score 0.618: Campus Sustainability Committee minutes, March 2026 The committee approved a provisional capital budget of 1.2 million dollars for the library and science hall heat-pump conversion. It reserved 400,000 dollars for the electric shuttle purchase and chargers, and 150,000 dollars for the laboratory freezer replacement program. These allocations must be confirmed after the October 2026 energy audit. The committee asked procurement to prioritize equipment that can be maintained by local technicians a

Human answer quality (1–5): _____

Notes: _____

### Hybrid

Retrieval time: **39.13 ms**; chunks retrieved: **2**.

1. **campus_climate_meeting.txt**, chunk 2, score 0.088: accessible summary of the audit after completion. The committee discussed purchasing carbon offsets as a shortcut. It rejected that proposal because offsets would not reduce energy consumed by campus buildings or vehicles. Members instead supported the heat-pump, shuttle, and freezer measures in the plan. The chair noted that the six diesel shuttles must be replaced by June 2027 to keep the fleet project on schedule. No dean or university president was named in these minutes.

2. **campus_climate_meeting.txt**, chunk 1, score 0.086: Campus Sustainability Committee minutes, March 2026 The committee approved a provisional capital budget of 1.2 million dollars for the library and science hall heat-pump conversion. It reserved 400,000 dollars for the electric shuttle purchase and chargers, and 150,000 dollars for the laboratory freezer replacement program. These allocations must be confirmed after the October 2026 energy audit. The committee asked procurement to prioritize equipment that can be maintained by local technicians a

Human answer quality (1–5): _____

Notes: _____

## Question 5: What is the dean's name?

Expected answer: The sources do not name a dean. A grounded answer should say this information is unavailable.

### Vector

Retrieval time: **50.44 ms**; chunks retrieved: **2**.

1. **campus_climate_meeting.txt**, chunk 2, score 0.161: accessible summary of the audit after completion. The committee discussed purchasing carbon offsets as a shortcut. It rejected that proposal because offsets would not reduce energy consumed by campus buildings or vehicles. Members instead supported the heat-pump, shuttle, and freezer measures in the plan. The chair noted that the six diesel shuttles must be replaced by June 2027 to keep the fleet project on schedule. No dean or university president was named in these minutes.

2. **campus_climate_plan.txt**, chunk 1, score 0.067: Campus Climate Plan, approved January 2026 The fictional Northbridge College adopted a target to cut operational greenhouse-gas emissions by 35 percent by 2030, compared with its 2022 baseline. The target covers campus electricity, heating fuel, and the college shuttle fleet. It does not count student travel. Facilities will publish a quarterly progress table on the LEAF-7 dashboard. Each table will show measured energy use, estimated emissions, and the difference from the baseline. The faciliti

Human answer quality (1–5): _____

Notes: _____

### Hybrid

Retrieval time: **52.11 ms**; chunks retrieved: **2**.

1. **campus_climate_meeting.txt**, chunk 2, score 0.091: accessible summary of the audit after completion. The committee discussed purchasing carbon offsets as a shortcut. It rejected that proposal because offsets would not reduce energy consumed by campus buildings or vehicles. Members instead supported the heat-pump, shuttle, and freezer measures in the plan. The chair noted that the six diesel shuttles must be replaced by June 2027 to keep the fleet project on schedule. No dean or university president was named in these minutes.

2. **campus_climate_plan.txt**, chunk 1, score 0.054: Campus Climate Plan, approved January 2026 The fictional Northbridge College adopted a target to cut operational greenhouse-gas emissions by 35 percent by 2030, compared with its 2022 baseline. The target covers campus electricity, heating fuel, and the college shuttle fleet. It does not count student travel. Facilities will publish a quarterly progress table on the LEAF-7 dashboard. Each table will show measured energy use, estimated emissions, and the difference from the baseline. The faciliti

Human answer quality (1–5): _____

Notes: _____

## Conclusion

After scoring, summarize which method retrieved more relevant evidence, whether its answers were better grounded, and the latency tradeoff.
