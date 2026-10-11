# Methodology Passport Card

## 1. Project information

**Research title:** Effectiveness of Generative AI Tools for Improving University Students' Understanding of Academic Material: A Controlled Study at Narxoz University  
**Authors:** [Mukhambet Asylzhan ,Muhtarhan Olzhas]  
**University:** Narxoz University  
**Public GitHub repository:** [https://github.com/Asylzhan579/ai-learning-effectiveness-narxoz]

## 2. Research type and justification

**Quantitative controlled experimental study**, with an optional supplementary perception questionnaire. A **randomized, counterbalanced crossover design** will be used with **20 Narxoz undergraduate students**: each student uses AI support for one learning module and conventional resources for another matched module. This design enables **paired, within-student** comparisons and reduces between-person differences. It should only be called mixed-methods if open-ended survey responses are collected and qualitatively coded; otherwise quantitative is the accurate classification.

## 3. Research questions and testable hypotheses

**RQ1 (primary):** Does AI-assisted studying produce a higher immediate normalized conceptual learning gain than studying with conventional resources?

- **H0:** Population mean paired difference in immediate normalized gain, μ(AI − conventional), is **≤ 0**.
- **H1:** Population mean paired difference in immediate normalized gain, μ(AI − conventional), is **> 0**.

**RQ2 (secondary):** Does AI-assisted studying improve retention after seven days?

- **H0:** Mean paired difference in 7-day delayed-test score, μ(AI − conventional), is **≤ 0**.
- **H1:** Mean paired difference in 7-day delayed-test score, μ(AI − conventional), is **> 0**.

**RQ3 (secondary):** Does AI-assisted studying improve learning efficiency?

- **H0:** Mean paired difference in raw score gain per study minute, μ(AI − conventional), is **≤ 0**.
- **H1:** Mean paired difference in raw score gain per study minute, μ(AI − conventional), is **> 0**.

These are **directional hypotheses**. Statistical significance is not evaluated by the Week-6 smoke test.

## 4. Variable matrix

| Class | Variable | Operationalization and units |
| --- | --- | --- |
| Independent | Learning condition | AI-assisted (generative AI tool under a standard prompt guide) vs conventional (lecture notes and textbooks, no AI) |
| Independent / design factor | Order and module assignment | Counterbalanced AI-first/conventional-first and topic/module A/B; recorded as design factors, not the primary treatment |
| Dependent — primary | Normalized immediate gain | (post_score − pre_score)/(max_score − pre_score), unitless; max_score=10; exclude/handle ceiling pretests by predefined rule |
| Dependent — secondary | Seven-day retention | Delayed test score, 0–10 points, recorded at day 7 |
| Dependent — secondary | Learning efficiency | (post_score − pre_score)/study_time_minutes, points/minute |
| Dependent — secondary | Time on task | Actual studying time, minutes |
| Controlled | Content and difficulty | Two similarly difficult, matched learning modules with equal length |
| Controlled | Testing protocol | Same pre-/post-test structure, score range 0–10 and marking rubric |
| Controlled | Technology | Same device category, model/tool settings and software versions recorded before real tests |
| Controlled | Context and duration | Same room/instructions, max. 30-minute sessions; same 7-day retention interval |
| Controlled | Prior understanding | Baseline pretest per module; normalized gain adjusts for ceiling effects where pretest<10 |

## 5. Metrics, baseline and acceptance controls

**Primary metric:** Average **paired** difference in normalized immediate gain, AI minus conventional. Positive values support the *direction* of H1; formal confirmation requires a prespecified statistical test and an uncertainty interval based on actual participants.

**Secondary metrics:** paired differences in (a) day-7 delayed score, (b) points gained per minute, and (c) study time in minutes.

**Guardrail metrics:** (1) 0% missing required fields; (2) score values in [0, 10]; (3) strictly positive study time ≤30 minutes; (4) retention test recorded exactly at day 7; (5) no personally identifiable data or AI transcripts committed to GitHub. For the current sample pipeline, invalid records trigger an error rather than being quietly deleted.

**Baseline/control condition:** Conventional study using the same type of source material (lecture notes/textbook) without generative AI, with matched learning objectives, total allowed time and tests. This is a fair active baseline; it is not an unassisted no-study condition.

**Sample size and allocation:** Planned 20 students, each observed under both conditions (40 real condition-level records). Participants will be randomly assigned to counterbalanced module/order sequences. The supplied CSV contains **8 synthetic records from 4 fictional participants** solely for software verification.

## 6. Reproducibility, data collection and analysis plan

- Use `configs/config.json` to define the score maximum, guardrails, source path and output path.
- Run `python3 -m unittest discover -s tests -v`, then `python3 -m src.benchmark --config configs/config.json` (or run via the Docker commands in README).
- The script validates input types, score bounds, time guardrails and the presence of paired study conditions. It calculates per-condition means, a paired primary effect and writes a JSON log.
- Before Week-7 data collection, finalize matched topic assessments, prompt guide, participant consent, randomization schedule, statistical test (e.g. paired permutation or paired t-test after distribution checks), confidence intervals and missing-data protocol.
- No real human-subject results or hypothesis-test claims have been generated for this deliverable.

**Submission links:** Public GitHub: [TO ADD] | Passport PDF: see separately supplied `Methodology_Passport_Card.pdf`.
