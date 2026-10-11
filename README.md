# Effectiveness of Generative AI Tools for University Students' Understanding of Academic Material

**Authors:** [Mukhambet Asylzhan , Muhtarhan Olzhas]  
**Institution:** Narxoz University, Kazakhstan  
**Repository:** [INSERT PUBLIC GITHUB LINK]

## Overview and Research Question

This research investigates whether generative-AI-assisted study improves immediate conceptual learning, one-week retention, and learning efficiency compared with conventional learning resources. The planned study is a **randomized, counterbalanced crossover study** with **20 undergraduate students at Narxoz University**. Each student completes both study conditions using two matched modules. Analysis is performed on within-student paired differences. The included 8-row CSV is **synthetic testing data**, not actual research findings.

**Research question:** Does studying with generative AI support lead to greater normalized immediate knowledge gain than conventional resources in matched learning tasks?

**Primary hypothesis:** H0: mean paired difference in normalized immediate knowledge gain (AI − conventional) ≤ 0. H1: mean paired difference > 0. The null may equivalently be stated as no improvement; the directional test requires a prespecified analysis plan.

## Research design / Benchmark plan

| Benchmark | Indicator | Comparison | Planned collection |
| --- | --- | --- | --- |
| Primary: immediate learning | Normalized gain `(post-pre)/(max-pre)` | Mean paired AI minus conventional | Pre-/post-test in each condition |
| Secondary: retention | Delayed test score (0–10) | Paired difference, day 7 | Same assessment format, 7-day interval |
| Secondary: efficiency | Raw gain per minute | Paired difference | Timed study sessions |
| Secondary: study duration | Time on task (minutes) | Paired difference | Same 30-minute cap |
| Data-quality guardrail | Missing required fields | 0% permitted in initial pipeline | CSV validation |
| Protocol guardrail | Time limit and delayed-test interval | ≤30 minutes, exactly 7 days | CSV validation |

**Baseline:** Conventional study resources (lecture notes/textbooks) without generative AI, applied to comparable content. This is an *active control condition*, not a no-study control. Same assessment length and scoring rubrics will be used. Assignment and module order should be counterbalanced; individual participant IDs must be pseudonymous.

## System requirements

- Docker Engine with access to `python:3.12.7-slim-bookworm` **or** Python **3.12.7**.
- No external Python packages; standard library only (exact external dependency set: empty).
- Disk space under 100 MB excluding the base container image.

## Quickstart (2 commands with Docker)

```bash
docker build -t narxoz-ai-study .
docker run --rm narxoz-ai-study
```

**Local alternative (2 commands):**

```bash
python3 -m unittest discover -s tests -v
python3 -m src.benchmark --config configs/config.json
```

The script reads `data/sample/pilot_synthetic.csv`, prints calculated metrics, and creates `results/benchmark_results.json`. The container also runs tests at build time. To save the output file directly from Docker:

```bash
docker run --rm -v "$(pwd)/results:/app/results" narxoz-ai-study
```

## Repository structure

```text
.
├── README.md
├── Dockerfile
├── .dockerignore
├── .gitignore
├── LICENSE
├── configs/config.json
├── data/sample/pilot_synthetic.csv
├── docs/Methodology_Passport_Card.md
├── src/__init__.py
├── src/benchmark.py
├── tests/test_benchmark.py
├── notebooks/.gitkeep
└── results/.gitkeep
```

## Operationalization and limitations

Study condition is the independent variable (AI-assisted versus conventional). Scores, time, and retention are dependent variables; fixed module length, environment, assessment scoring, delay, devices, and counterbalancing are intended controls. The study uses quantitative primary outcomes with a short supplementary perception questionnaire (mixed methods only if qualitative free-text responses are systematically collected and analyzed). Current benchmark code summarizes paired outcomes; **it does not yet run inferential hypothesis tests, adjust for period/topic effects, or establish causal results.** The planned n=20 study must predefine its directional paired statistical test, confidence interval, checks for carryover and missing-data handling before collecting real data.

**Research ethics:** Obtain consent, avoid collecting names and private chat transcripts, separate any identifiers from measurements, anonymize before publication. Never publish identifiable student records in this repository.

## Citation and License

Suggested citation: *[Authors]. (2026). Effectiveness of Generative AI Tools for University Students' Understanding of Academic Material: Research benchmark repository. GitHub: [URL].*

Code is licensed under the MIT License. Student data must be shared only under a separate appropriate data-use/consent policy.
