# PhishForge: Human Evaluation Analysis & Statistical Results

**Date**: August 29, 2026  
**Evaluator**: Human Rater (Blind Protocol, Single Rater)  
**Sample Size**: $N = 12$ items (5 `verifier_guided` PASS, 1 `verifier_guided` REJECTED_UNSAFE, 6 `baseline_direct`)  
**Data Artifacts**:
- Ratings source: [`rating_packet.md`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/rating_packet.md)
- Secret mapping: [`answer_key.json`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/answer_key.json)
- Statistical summary: [`human_eval_analysis.json`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/human_eval_analysis.json)
- Tabular breakdown: [`human_eval_analysis.csv`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/human_eval_analysis.csv)

---

## 1. Automated vs. Human Alignment (Correlation Metrics)

To evaluate the relationship between automated scoring and human judgment, Pearson correlation ($r$) and Spearman rank correlation ($\rho$) were computed across all quality-scored items ($N = 11$):

| Evaluation Dimension | Pearson $r$ | Spearman $\rho$ | Construct Compared | Methodological Note |
|:---|:---:|:---:|:---|:---|
| **Overall Quality vs. Score ($Q$)** | **0.677** | **0.716** | Human Overall (1–5) vs. Automated Overall Score ($Q \in [0, 100]$) | Descriptive positive correlation across the small sample. |
| **Realism Alignment** | **0.678** | **0.681** | Human Realism (1–5) vs. Automated Realism Score (0–100) | Descriptive positive correlation on linguistic authenticity. |
| **Role Relevance Alignment** | 0.533 | 0.136 | Human Role Relevance (1–5) vs. Automated Relevance Score (0–100) | **Discrepancy Note**: The Pearson value ($0.533$) is heavily driven by a single severe low-end anchor (`sample_08`, rated 2 by human and 60 by verifier). For the remaining 10 items, human ratings clustered tightly at 4/5 while automated scores varied, resulting in a weak rank correlation ($\rho = 0.136$). |
| **Difficulty Level Tracking** | **0.572** | **0.556** | Human Perceived Difficulty (1–4) vs. Scenario Target Difficulty ($D \in \{1,2,3,4\}$) | **Metric Clarification**: This correlates the human rater's perceived difficulty tier against the *requested* scenario difficulty level ($D$), assessing whether the simulation steered human perception to the intended difficulty tier. It does not measure the verifier's calibration accuracy score (`difficulty_score`). |

> **Methodological Caution**: At $N = 11$ with single-rater sampling and no formal significance testing, these correlations are descriptive only and range from weak to moderate depending on the dimension. The sample size is insufficient to draw definitive conclusions about any individual dimension.

---

## 2. Blind Condition Comparison (Human Ratings)

Descriptive comparison of blind human ratings between `verifier_guided` ($n=5$ PASS cases) and `baseline_direct` ($n=6$ unverified cases):

| Evaluation Criterion (1–5 Scale) | `verifier_guided` (PASS, $n=5$) | `baseline_direct` ($n=6$) | Observed Rating Delta ($\Delta$) |
|:---|:---:|:---:|:---:|
| **Overall Quality (1–5)** | **4.20** / 5.0 | **3.00** / 5.0 | **$+1.20$** |
| **Realism (1–5)** | **3.80** / 5.0 | **3.00** / 5.0 | **$+0.80$** |
| **Role Relevance (1–5)** | **4.20** / 5.0 | **3.50** / 5.0 | **$+0.70$** |
| **Perceived Difficulty (1–4 Rubric)** | **3.80** / 4.0 | **2.67** / 4.0 | **$+1.13$** |

### Observations & Limitations:
1. **Suggestive Trend**: The human rater assigned higher average ratings to `verifier_guided` outputs in this small sample. However, with $n=5$ and $n=6$ per group, these differences are suggestive rather than statistically confirmed.
2. **Qualitative Feedback on Baseline Outputs**: The rater noted mechanical or unnatural phrasing in several unguided baseline generations (e.g., `sample_06`: *"Hello IT Administrator sounds robotic"*, Quality=2; `sample_12`: *"Informal wording used in call to action"*, Quality=3).

---

## 3. Safety-Rejected Item Analysis (`sample_02`)

- **Item Identity**: `sample_02` originated from `verifier_guided_bench-07-it-verify-d3` (financial tech firm AWS Duo MFA token rotation).
- **Safety Gate Action**: Intercepted by the deterministic Safety Gate due to an unapproved synthetic domain format and terminated early as `REJECTED_UNSAFE` (never delivered or approved).
- **Human Rating**:
  - Realism: **4 / 5**
  - Role Relevance: **3 / 5**
  - Perceived Difficulty: **4 / 4**
  - Overall Quality: **4 / 5**
- **Case Observation**: This single case illustrates a plausible risk: a subtly unsafe simulation was rated highly by the human evaluator (4/5 overall, 4/4 difficulty), suggesting deterministic safety gating may catch risks that neither automated quality scoring nor a human reviewer focused on realism would necessarily flag. This is one example, not a demonstrated general pattern, and would need a larger sample to confirm.

---

## 4. Full Per-Sample Alignment Table

| Sample ID | Condition | Status | Role | Target Diff | Human Realism | Human Relevance | Human Diff | Human Overall | Auto $Q$ Score | Auto Realism | Auto Relevance | Auto Diff |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `sample_01` | `baseline_direct` | UNVERIFIED | `operations` | 2 | 4 | 5 | 3 | 4 | 94.0 | 85.0 | 95.0 | 95.0 |
| `sample_02` | `verifier_guided` | REJECTED | `it` | 3 | 4 | 3 | 4 | 4 | *N/A* | *N/A* | *N/A* | *N/A* |
| `sample_03` | `baseline_direct` | UNVERIFIED | `hr` | 1 | 2 | 4 | 1 | 2 | 87.8 | 75.0 | 90.0 | 95.0 |
| `sample_04` | `verifier_guided` | PASS | `sales` | 3 | 3 | 4 | 2 | 3 | 94.0 | 90.0 | 95.0 | 90.0 |
| `sample_05` | `baseline_direct` | UNVERIFIED | `executive` | 4 | 5 | 4 | 5 | 5 | 97.2 | 95.0 | 95.0 | 97.0 |
| `sample_06` | `baseline_direct` | UNVERIFIED | `it` | 3 | 2 | 4 | 3 | 2 | 95.8 | 90.0 | 95.0 | 96.0 |
| `sample_07` | `baseline_direct` | UNVERIFIED | `sales` | 3 | 4 | 5 | 4 | 5 | 92.0 | 90.0 | 90.0 | 90.0 |
| `sample_08` | `verifier_guided` | PASS | `it` | 1 | 2 | 2 | 2 | 2 | 92.8 | 85.0 | 90.0 | 95.0 |
| `sample_09` | `verifier_guided` | PASS | `finance` | 4 | 4 | 3 | 3 | 4 | 97.2 | 95.0 | 95.0 | 99.0 |
| `sample_10` | `verifier_guided` | PASS | `executive` | 4 | 5 | 4 | 5 | 5 | 96.7 | 95.0 | 95.0 | 97.0 |
| `sample_11` | `baseline_direct` | UNVERIFIED | `it` | 1 | 3 | 3 | 4 | 4 | 82.8 | 80.0 | 85.0 | 75.0 |
| `sample_12` | `verifier_guided` | PASS | `hr` | 1 | 3 | 4 | 3 | 3 | 90.0 | 80.0 | 90.0 | 95.0 |
