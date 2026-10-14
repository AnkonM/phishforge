# PhishForge Benchmark: Results Interpretation & Empirical Analysis

**Date**: August 29, 2026  
**Evaluation Scope**: Curated Benchmark Suite ($N = 12$ scenarios $\times$ 2 conditions = 24 experimental runs)  
**Evaluated Conditions**:
1. `verifier_guided`: PhishForge closed-loop synthesis (Generation $\rightarrow$ Deterministic Safety Gate $\rightarrow$ Hybrid Verification $\rightarrow$ Scoring Engine $\rightarrow$ Refinement Controller).
2. `baseline_direct`: Unconstrained single-shot generation (`direct_only=True`), with post-hoc evaluation via the same Safety Gate, Verifier, and Scoring Engine.

---

## 1. Summary Metrics Table

The table below presents empirical results across both conditions on identical scenario specifications:

| Metric | `verifier_guided` (Proposed) | `baseline_direct` (Single-Shot) | Delta ($\Delta$) |
|:---|:---:|:---:|:---:|
| **Total Scenarios Evaluated ($N$)** | 12 | 12 | — |
| **Mean Overall Quality Score ($Q$)** | **93.9** / 100 | **93.5** / 100 | $+0.4$ |
| **Quality Pass Rate ($Q \ge 80.0$)** | 83.3% (10/12) | 100.0% (12/12) | $-16.7\%$ * |
| **Safety Gate Pass Rate** | **83.3%** (10/12) | **75.0%** (9/12) | $+8.3\%$ |
| **Unsafe Simulations Approved / Delivered** | **0 / 12 (0.0%)** | **3 / 12 (25.0%)** | **$-25.0\%$** |
| Mean Realism Score | 87.5 / 100 | 88.5 / 100 | $-1.0$ |
| Mean Role Relevance Score | 92.3 / 100 | 90.8 / 100 | $+1.5$ |
| Mean Indicator Coverage Score | 100.0 / 100 | 100.0 / 100 | $0.0$ |
| Mean Difficulty Calibration Match | 94.7 / 100 | 93.5 / 100 | $+1.2$ |
| Mean Language Quality Score | 100.0 / 100 | 100.0 / 100 | $0.0$ |
| Mean Iterations to Terminate | 1.1 | 1.0 | $+0.1$ |
| **Terminal State Distribution** | `PASS`: 10<br>`REJECTED_UNSAFE`: 2 | `GENERATED_UNVERIFIED`: 12 | — |

*\* Note: As analyzed in Section 3, `baseline_direct`'s 100% quality pass rate reflects the absence of safety gating, allowing unsafe simulations to be scored on semantic quality alone.*

---

## 2. Quality Score Analysis: Modest Difference at $N=12$

The observed mean overall quality score difference between `verifier_guided` ($93.9$) and `baseline_direct` ($93.5$) is $+0.4$ points on a $100$-point scale.

### Methodological Context
- **Sample Size and Power**: At $N = 12$ scenarios per condition with single-trial sampling, this difference is minor and cannot be claimed as statistically significant.
- **Interpretation**: We do **not** claim that `verifier_guided` demonstrates clear superiority in raw linguistic or semantic generation quality over a single unguided prompt when the base model (`gemini-3.5-flash-lite`) is already highly capable at first-pass instruction following.
- **Dimension Nuance**: Minor positive deltas appear in **Role Relevance** ($92.3$ vs $90.8$) and **Difficulty Calibration Match** ($94.7$ vs $93.5$), while **Realism** is slightly lower ($87.5$ vs $88.5$) due to strict synthetic domain constraints enforced by Layer A heuristics.

---

## 3. Safety Gate Filtering: The Core Empirical Finding

The primary differentiation between the two conditions is **delivery safety**:

1. **Safety Vulnerability in Direct Generation (`baseline_direct`)**:
   - In the unconstrained baseline, **3 out of 12 simulations (25.0%) failed the deterministic Safety Gate rules** upon post-hoc verification (`Safety Gate Pass Rate = 75.0%`).
   - Specifically, the baseline model leaked unapproved domain patterns (e.g. non-whitelisted corporate TLDs) and brand impersonation tells into the generated content.
   - In a production environment without closed-loop safety gating, these 3 unsafe simulations would have been dispatched directly to end users.

2. **Delivery Safety Filtering in `verifier_guided`**:
   - Under `verifier_guided`, the deterministic Safety Gate acts as a fail-closed prior before scoring.
   - When unsafe simulations were generated (Scenarios 7 and 8), the orchestrator immediately terminated execution with `terminal_state: REJECTED_UNSAFE`, preventing any unapproved simulation from being finalized or marked as `PASS`.
   - **Result**: In this benchmark sample, **0% of approved simulations under `verifier_guided` contained safety violations**. This finding, while based on a small sample, supports the architectural rationale for deterministic safety boundaries in automated awareness systems — that provider-level and generation-level controls alone are insufficient.

### Clarifying the 100% vs 83.3% Quality Pass Rate
A surface reading of the metrics might suggest `baseline_direct` (100% pass rate) outperformed `verifier_guided` (83.3% pass rate). **This is an artifact of evaluation design**:
- In `verifier_guided`, the 2 safety-rejected runs terminated early (`REJECTED_UNSAFE`) with no quality score computed, resulting in 10 passes out of 12 total scenarios ($83.3\%$). Among runs that cleared safety, the quality pass rate was $100.0\%$ ($10/10$).
- In `baseline_direct`, all 12 simulations received post-hoc quality scores, including the 3 unsafe simulations that should have been disqualified. Because the Scoring Engine measures persuasion and relevance rather than safety compliance, unsafe outputs still received high quality scores.

---

## 4. Refinement Loop Dynamics & Limitations (H3 Assessment)

- **Iteration Efficiency**: `verifier_guided` converged in a mean of **1.1 iterations**.
- **First-Pass Convergence**: 9 out of 10 approved scenarios passed the quality threshold ($Q \ge 80.0$) on Iteration 1. Only 1 scenario (`01_it_password_alert_d1.json`) required a second iteration (improving from initial feedback to $92.8$).
- **Scientific Limitation regarding Hypothesis H3**:
  - Because `gemini-3.5-flash-lite` produced high-quality simulations on initial generation for most standard scenarios, the multi-step refinement loop was rarely stressed in this standard benchmark set.
  - Consequently, this benchmark provides **limited statistical evidence regarding H3** (the degree to which multi-iteration critique drives cumulative score improvement).
- **Recommendation for Future Work**: Future benchmark suites should deliberately incorporate adversarial, underspecified, or conflicting scenario constraints (e.g., highly restrictive word counts combined with complex role contexts) to force lower initial quality scores and thoroughly evaluate multi-turn convergence trajectories.

---

## 5. Ongoing Limitations from Document A v2 §18

The results of this benchmark do **not** alter the foundational architectural limitations identified in Document A v2 §18:

1. **Self-Evaluation & LLM Circularity**:
   - Both Layer B of the Hybrid Verifier and the Generator utilize models from the Gemini family. While prompting constraints strictly separate generator and critic roles, an external check (e.g., human expert review or independent cross-family models) has not yet been conducted.
2. **Absence of Human-in-the-Loop Validation**:
   - Automated quality scoring $Q$ approximates educational realism and difficulty calibration using established rubrics, but empirical transfer to human vulnerability or click-rate discrimination remains unvalidated until Future Scope clinical trials are conducted.

---

## 6. Summary Conclusion

The curated benchmark provides initial empirical evidence regarding the central architectural thesis of PhishForge:
> While unguided LLM generation can produce plausible text, it leaks safety violations (25% failure rate in this sample). In this benchmark sample, embedding generative models within a deterministic safety gate and hybrid verification loop prevented any of the safety violations observed in direct generation from reaching approved status — supporting, though not conclusively proving at this sample size, the architectural case for verification as a required layer rather than an optional add-on.
