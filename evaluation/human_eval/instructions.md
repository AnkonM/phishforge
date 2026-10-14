# PhishForge: Human Evaluation Instructions

Welcome to the blind evaluation round for PhishForge simulations. You will evaluate a randomized sample of **12 synthetic phishing awareness training emails**.

---

## 1. Overview & Objective

Each item presents:
- **Scenario Context**: Target role, organizational context, scenario type, and target difficulty level.
- **Simulation**: The subject line, sender display name/address, and email body.

Your goal is to evaluate the quality and realism of each email independently, strictly based on the content presented, without attempting to guess the generation pipeline or condition.

---

## 2. Rating Dimensions (1–5 Likert & 1–4 Rubric)

For each item, please assign ratings across the following 4 criteria:

1. **Realism (1–5)**:
   - *1 = Completely implausible, robotic, or absurd.*
   - *3 = Moderately believable with minor artificial stiffness.*
   - *5 = Highly authentic, natural business communication.*

2. **Role Relevance (1–5)**:
   - *1 = Completely irrelevant to the specified employee role and organization context.*
   - *3 = Generic organizational communication with loose role applicability.*
   - *5 = Deeply grounded in the role's specific workflows, tools, and authority structure.*

3. **Perceived Difficulty (1–4)**:
   - Assign a discrete integer from **1 to 4** based strictly on the operational definitions in [`rubric_reference.md`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/rubric_reference.md):
     - `1`: Obvious (glaring red flags, obvious panic triggers)
     - `2`: Moderate (obvious upon inspection, 1-2 clear tells)
     - `3`: Advanced (plausible at a glance, subtle process/domain anomalies)
     - `4`: Expert (sophisticated spear-phishing, highly subtle tells)

4. **Overall Quality (1–5)**:
   - *1 = Very Poor (unusable for awareness training).*
   - *3 = Acceptable (usable standard training fixture).*
   - *5 = Outstanding (exemplary contextual awareness simulation).*

---

## 3. How to Submit Ratings

You can record your ratings directly inside [`rating_packet.md`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/rating_packet.md) under each item or in the summary table at the bottom of the packet.

---

## 4. Estimated Completion Time

- **Estimated Time**: **15–20 minutes** (~1 to 1.5 minutes per scenario).
