# PhishForge Human Evaluation: Blind Rating Packet

Please rate the following 12 simulations independently based on the scenario context provided. Refer to [`rubric_reference.md`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/rubric_reference.md) and [`instructions.md`](file:///c:/Users/Ankon/Documents/Code/GenAI%20IA1/phishforge/evaluation/human_eval/instructions.md) for rating criteria.

---

## Item 1 — ID: `sample_01`

### Scenario Target Context
- **Target Role**: `operations`
- **Scenario Type**: `account_verification`
- **Target Difficulty**: Level 2 (Scale 1–4)
- **Organization Context**: National distribution company, 600 workers. Operations supervisors manage inventory access through SAP ERP portals.

### Training Simulation Content
**Subject**: Action Required: Verify SAP ERP Inventory Access Permissions

**Sender**: Logistics Systems Admin <admin-portal@logistics-update.example-corp-sim.local>

**Body**:
```text
Dear Operations Supervisor,

As part of our routine quarterly access review, all operations supervisors must verify their current permission levels for the SAP ERP inventory portals to maintain compliance standards.

Failure to complete this verification within 24 hours may result in temporary suspension of your inventory management credentials.

Please verify your account details immediately by accessing the verification portal below:

[SIMULATED LINK: Verify SAP ERP Access - https://sap-portal-verify.example-corp-sim.local]

Thank you for your prompt attention to this matter.

Regards,

Logistics Systems Administration Team
```

### Your Evaluation Ratings
- **Realism (1–5)**: [4]
- **Role Relevance (1–5)**: [5]
- **Perceived Difficulty (1–4)**: [3]
- **Overall Quality (1–5)**: [4]
- **Notes / Observations (optional)**: 

---

## Item 2 — ID: `sample_02`

### Scenario Target Context
- **Target Role**: `it`
- **Scenario Type**: `account_verification`
- **Target Difficulty**: Level 3 (Scale 1–4)
- **Organization Context**: Financial technology firm, 450 engineers. IT administrators manage production AWS clusters with mandatory Duo MFA token rotation.

### Training Simulation Content
**Subject**: Action Required: Mandatory Duo MFA Certificate Renewal for Production AWS Access

**Sender**: Cloud Infrastructure Identity Team <identity-ops@internal-aws-auth.sim-training.test>

**Body**:
```text
Hi IT Team,

As part of our routine quarterly security hardening for our financial infrastructure, all administrators managing production AWS clusters are required to re-verify and sync their Duo MFA security tokens.

Recent compliance audits indicate that your account requires manual token re-attestation to prevent temporary access suspension during the upcoming maintenance window.

Please complete the verification process within the next 48 hours to maintain uninterrupted access to the production environment:

[SIMULATED LINK: Access Duo MFA Token Sync Portal at https://auth-verify.sim-training.test/duo-sync]

If you have any questions regarding this security procedure, please reach out via internal Slack.

Regards,

Cloud Infrastructure Identity Team
Apex Financial Tech Engineering
```

### Your Evaluation Ratings
- **Realism (1–5)**: [4]
- **Role Relevance (1–5)**: [3]
- **Perceived Difficulty (1–4)**: [4]
- **Overall Quality (1–5)**: [4]
- **Notes / Observations (optional)**: 

---

## Item 3 — ID: `sample_03`

### Scenario Target Context
- **Target Role**: `hr`
- **Scenario Type**: `internal_policy_update`
- **Target Difficulty**: Level 1 (Scale 1–4)
- **Organization Context**: Mid-size logistics firm, 400 employees. HR uses Workday for company-wide policy distribution.

### Training Simulation Content
**Subject**: URGENT: Updat your Workday HR policies immeditly

**Sender**: HR Policy Team <hr-admin@logistics-update.sim-training.test>

**Body**:
```text
Dear Employee,

We have updated the company HR policies regarding logistics operations and benifits. All staff must review and agree to these changes today or your account will be locked.

Please click the link below to review the document:

[SIMULATED LINK: Workday HR Policy Login]

Thank you,
HR Department
```

### Your Evaluation Ratings
- **Realism (1–5)**: [2]
- **Role Relevance (1–5)**: [4]
- **Perceived Difficulty (1–4)**: [1]
- **Overall Quality (1–5)**: [2]
- **Notes / Observations (optional)**: 

---

## Item 4 — ID: `sample_04`

### Scenario Target Context
- **Target Role**: `sales`
- **Scenario Type**: `invoice_fraud`
- **Target Difficulty**: Level 3 (Scale 1–4)
- **Organization Context**: Enterprise cloud consultancy, 250 employees. Sales account directors finalize client contracts with custom milestone billing schedules.

### Training Simulation Content
**Subject**: Updated Milestone Billing Schedule - Apex Logistics Q3 Contract

**Sender**: Director of Finance <finance-director@apex-logistics-sim.local>

**Body**:
```text
Hi team,

I just finished reviewing the preliminary milestone billing schedule for the Apex Logistics account expansion. Following our executive alignment call this morning, we need to adjust the invoicing terms to reflect the accelerated delivery phases we agreed upon.

Please review the updated milestone distribution and confirm your alignment by end of day so we can lock in the contract terms before the client reviews it tomorrow morning.

[SIMULATED LINK: View Updated Milestone Schedule]

Regards,

Director of Finance
Apex Logistics Enterprise Services
```

### Your Evaluation Ratings
- **Realism (1–5)**: [3]
- **Role Relevance (1–5)**: [4]
- **Perceived Difficulty (1–4)**: [2]
- **Overall Quality (1–5)**: [3]
- **Notes / Observations (optional)**: 

---

## Item 5 — ID: `sample_05`

### Scenario Target Context
- **Target Role**: `executive`
- **Scenario Type**: `password_alert`
- **Target Difficulty**: Level 4 (Scale 1–4)
- **Organization Context**: Venture capital firm, 40 partners. Senior leadership uses hardware security keys (YubiKey) for multi-factor authentication on corporate email.

### Training Simulation Content
**Subject**: Mandatory Security Token Policy Update: YubiKey Re-attestation Required

**Sender**: Global Security Directorate <security-admin@apex-ventures.sim-training.test>

**Body**:
```text
Dear Margaret,

In alignment with our updated Q3 cryptographic governance framework, all senior partners utilizing hardware-based security keys (YubiKey) are required to complete a routine compliance re-attestation by end of business tomorrow.

This update ensures our firmware policies remain synchronized with the latest enterprise authentication standards for high-privilege access corridors. No interruption to your active sessions will occur if completed within the designated window.

Please navigate to the internal compliance portal to verify your hardware token registration:

[SIMULATED LINK: Access YubiKey Re-Attestation Portal]

Thank you for your prompt attention to this governance requirement.

Best regards,

Global Security Directorate
Apex Capital Partners
```

### Your Evaluation Ratings
- **Realism (1–5)**: [5]
- **Role Relevance (1–5)**: [4]
- **Perceived Difficulty (1–4)**: [5]
- **Overall Quality (1–5)**: [5]
- **Notes / Observations (optional)**: 

---

## Item 6 — ID: `sample_06`

### Scenario Target Context
- **Target Role**: `it`
- **Scenario Type**: `account_verification`
- **Target Difficulty**: Level 3 (Scale 1–4)
- **Organization Context**: Financial technology firm, 450 engineers. IT administrators manage production AWS clusters with mandatory Duo MFA token rotation.

### Training Simulation Content
**Subject**: Action Required: Scheduled Duo MFA Token Rotation for AWS Production Access

**Sender**: Cloud Infrastructure Security <aws-admin@infra-secure-sim-training.test>

**Body**:
```text
Hello IT Administrator,

As part of our quarterly security compliance schedule, all administrative accounts managing production AWS clusters must complete their mandatory Duo MFA token re-validation and metadata rotation.

Failure to complete this verification within 48 hours will result in a temporary suspension of elevated AWS console privileges to maintain compliance with internal security baselines.

Please complete your re-validation via the internal portal link below:

[SIMULATED LINK: AWS MFA Token Rotation Portal - https://auth.aws-mfa-verify.example-corp-sim.local/login]

Thank you for your prompt attention to this matter.

Best regards,

Cloud Infrastructure Security Team
Nexus Financial Technologies
```

### Your Evaluation Ratings
- **Realism (1–5)**: [2]
- **Role Relevance (1–5)**: [4]
- **Perceived Difficulty (1–4)**: [3]
- **Overall Quality (1–5)**: [2]
- **Notes / Observations (optional)**:Hello IT Administrator sounds robotic.

---

## Item 7 — ID: `sample_07`

### Scenario Target Context
- **Target Role**: `sales`
- **Scenario Type**: `invoice_fraud`
- **Target Difficulty**: Level 3 (Scale 1–4)
- **Organization Context**: Enterprise cloud consultancy, 250 employees. Sales account directors finalize client contracts with custom milestone billing schedules.

### Training Simulation Content
**Subject**: Action Required: Updated Milestone Billing Authorization for Apex Cloud Project

**Sender**: Director of Finance <finance-approvals@cloud-apex-sim.local>

**Body**:
```text
Hi team,

We are finalizing the Q3 milestone billing schedules for the upcoming client deployments. Following our leadership review, all custom milestone invoices must now be routed through our newly integrated portal before final release to clients.

Please review the updated billing structure and confirm your assigned client accounts via the secure portal link below by end of day tomorrow to avoid any processing delays.

[SIMULATED LINK: Access Billing Portal -> https://portal-auth.cloud-apex-sim.local/login]

Regards,

Finance Operations
CloudSync Solutions
```

### Your Evaluation Ratings
- **Realism (1–5)**: [4]
- **Role Relevance (1–5)**: [5]
- **Perceived Difficulty (1–4)**: [4]
- **Overall Quality (1–5)**: [5]
- **Notes / Observations (optional)**: 

---

## Item 8 — ID: `sample_08`

### Scenario Target Context
- **Target Role**: `it`
- **Scenario Type**: `password_alert`
- **Target Difficulty**: Level 1 (Scale 1–4)
- **Organization Context**: Global tech consulting firm, 1200 employees. IT department uses Okta for SSO.

### Training Simulation Content
**Subject**: URGENT: Your password expires today! Update Now

**Sender**: Admin Support <support@admin-update-sim-training.test>

**Body**:
```text
Dear User,

Your network password is going to expire in 2 hours. If you do not update your password right now, your account will be locked and you will lose access to all IT systems!

Please click here immediately to reset your password:
[SIMULATED LINK: Reset Password Portal]

Thank you,
IT Help Desk
```

### Your Evaluation Ratings
- **Realism (1–5)**: [2]
- **Role Relevance (1–5)**: [2]
- **Perceived Difficulty (1–4)**: [2]
- **Overall Quality (1–5)**: [2]
- **Notes / Observations (optional)**: 

---

## Item 9 — ID: `sample_09`

### Scenario Target Context
- **Target Role**: `finance`
- **Scenario Type**: `internal_policy_update`
- **Target Difficulty**: Level 4 (Scale 1–4)
- **Organization Context**: Multinational audit corporation, 5000 employees. Finance department operates under strict SOX compliance guidelines with annual mandatory policy re-attestation.

### Training Simulation Content
**Subject**: Action Required: Annual SOX Policy Attestation Update - Fiscal Year Review

**Sender**: Corporate Compliance & Governance <governance-updates@nexus-audit-sim.local>

**Body**:
```text
Dear David,

As part of our ongoing commitment to regulatory compliance and our annual SOX attestation schedule, all Finance department personnel are required to review and re-certify adherence to the updated Internal Controls Framework v4.2.

Following our recent audit committee review, Section 4 of the financial reporting guidelines has been revised regarding segregation of duties and variance documentation thresholds. You are requested to review the updated policy document and complete your digital attestation before the close of the current business cycle.

Please access the portal to review the changes and submit your sign-off: [SIMULATED LINK: Access Policy Attestation Portal]

Thank you for your prompt attention to this compliance requirement.

Best regards,

Internal Governance & Regulatory Affairs
Nexus Audit Corporation
```

### Your Evaluation Ratings
- **Realism (1–5)**: [4]
- **Role Relevance (1–5)**: [3]
- **Perceived Difficulty (1–4)**: [3]
- **Overall Quality (1–5)**: [4]
- **Notes / Observations (optional)**: 

---

## Item 10 — ID: `sample_10`

### Scenario Target Context
- **Target Role**: `executive`
- **Scenario Type**: `password_alert`
- **Target Difficulty**: Level 4 (Scale 1–4)
- **Organization Context**: Venture capital firm, 40 partners. Senior leadership uses hardware security keys (YubiKey) for multi-factor authentication on corporate email.

### Training Simulation Content
**Subject**: Action Required: Annual Hardware Security Key Recertification

**Sender**: Global Security Operations <security-ops@apex-ventures.example-corp-sim.local>

**Body**:
```text
Dear Jonathan,

As part of our ongoing compliance audit and risk mitigation protocols for Q3, all executive partners utilizing hardware-based multi-factor authentication tokens must complete an annual security token attestation.

Recent updates to our identity management infrastructure require your YubiKey profile to be re-synchronized to ensure uninterrupted access to internal deal-flow portals and restricted communication channels. Failure to verify your device registry within 48 hours may result in a temporary suspension of secondary authentication privileges until manual recertification is completed by the security team.

Please navigate to the internal compliance portal to confirm your device identifier:

[SIMULATED LINK: Access Apex Ventures Security Portal - https://auth-recertification.example-corp-sim.local/login]

Thank you for your prompt attention to this matter.

Best regards,

Global Security Operations
Apex Capital Partners
```

### Your Evaluation Ratings
- **Realism (1–5)**: [5]
- **Role Relevance (1–5)**: [4]
- **Perceived Difficulty (1–4)**: [5]
- **Overall Quality (1–5)**: [5]
- **Notes / Observations (optional)**: 

---

## Item 11 — ID: `sample_11`

### Scenario Target Context
- **Target Role**: `it`
- **Scenario Type**: `password_alert`
- **Target Difficulty**: Level 1 (Scale 1–4)
- **Organization Context**: Global tech consulting firm, 1200 employees. IT department uses Okta for SSO.

### Training Simulation Content
**Subject**: Urgent: Action Required to Reset Your Okta Single Sign-On Password

**Sender**: Global Tech IT Helpdesk <support@okta-auth-sim-training.test>

**Body**:
```text
Dear User,

Our system records indicate that your Okta single sign-on credentials for your global tech consulting account are set to expire today. If you do not update your password immediately, your access to internal resources will be temporarily suspended until manual intervention is completed by the IT department.

Please click the link below to update your credentials:

[SIMULATED LINK: Update Okta Password - https://auth.okta-auth-sim-training.test/reset]

Thank you,
IT Security Team
```

### Your Evaluation Ratings
- **Realism (1–5)**: [3]
- **Role Relevance (1–5)**: [3]
- **Perceived Difficulty (1–4)**: [4]
- **Overall Quality (1–5)**: [4]
- **Notes / Observations (optional)**: 

---

## Item 12 — ID: `sample_12`

### Scenario Target Context
- **Target Role**: `hr`
- **Scenario Type**: `internal_policy_update`
- **Target Difficulty**: Level 1 (Scale 1–4)
- **Organization Context**: Mid-size logistics firm, 400 employees. HR uses Workday for company-wide policy distribution.

### Training Simulation Content
**Subject**: URGENT: Upadte your HR profile immediately or lose access

**Sender**: HR Depatment <hr-admin@logistics-update.sim-training.test>

**Body**:
```text
Dear Employee,

We have updated our company-wide policy regarding Workday payroll and benefits. All staff members are required to verfy their employee details within the next 24 hours to avoid suspension of account.

Please click the link below to complete the mandatory form right now:

[SIMULATED LINK: Login to Workday Policy Portal at https://workday-verify.example-corp-sim.local]

Failure to act fast will result in immediate termination of system access.

Thank you,
Human Resources Team
```

### Your Evaluation Ratings
- **Realism (1–5)**: [3]
- **Role Relevance (1–5)**: [4]
- **Perceived Difficulty (1–4)**: [3]
- **Overall Quality (1–5)**: [3]
- **Notes / Observations (optional)**:Informal wording used in call to action (last paragraph). 

---

## Summary Ratings Table

| Sample ID | Target Role | Target Diff | Realism (1-5) | Relevance (1-5) | Perceived Diff (1-4) | Overall Quality (1-5) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `sample_01` | `operations` | Level 2 | | | | |
| `sample_02` | `it` | Level 3 | | | | |
| `sample_03` | `hr` | Level 1 | | | | |
| `sample_04` | `sales` | Level 3 | | | | |
| `sample_05` | `executive` | Level 4 | | | | |
| `sample_06` | `it` | Level 3 | | | | |
| `sample_07` | `sales` | Level 3 | | | | |
| `sample_08` | `it` | Level 1 | | | | |
| `sample_09` | `finance` | Level 4 | | | | |
| `sample_10` | `executive` | Level 4 | | | | |
| `sample_11` | `it` | Level 1 | | | | |
| `sample_12` | `hr` | Level 1 | | | | |