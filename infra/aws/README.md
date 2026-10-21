# AWS Infrastructure Architecture: Gitlexa

This directory maintains declarative configurations, IAM security policies, and architectural specifications for Gitlexa's cloud subsystems.

> **Ownership**: Maintained by **Member 01** (Cloud Security Architect & DevOps).  
> **Governance**: Governed by [.ai/SECURITY_RULES.md](file:///c:/Users/Divakar%20K%20R/Gitlexa/.ai/SECURITY_RULES.md) and [.ai/TEAM_ROLES.md](file:///c:/Users/Divakar%20K%20R/Gitlexa/.ai/TEAM_ROLES.md).

---

## 1. IAM Least-Privilege Architecture

The Gitlexa backend connects to Amazon Web Services to orchestrate LLM reasoning, retrieve secrets safely at runtime, and emit operational telemetry. In compliance with enterprise security requirements, permissions follow strict **Least-Privilege Principles**:

- **No Administrator or PowerUser Access**: No broad administrative roles or wildcard permissions (`*.*`, `iam:*`) are assigned.
- **Resource Scoping**: Permissions are explicitly scoped to Gitlexa resources (`/gitlexa/*`, `secret:gitlexa/*`).
- **No Wildcard Write Actions**: Wildcards are disallowed on mutating or data-altering actions.
- **Credential Safety**: No real AWS Account IDs, Access Keys, Secret Keys, or session tokens exist in repository files. Placeholders (`<AWS_ACCOUNT_ID>`, `<AWS_REGION>`, `<KMS_KEY_ID>`) must be parameterized via deployment pipelines.

---

## 2. Directory Structure

```
infra/aws/
├── README.md                          # This document
├── iam/
│   ├── policies/
│   │   ├── bedrock-invoke-policy.json         # Least-privilege Amazon Bedrock invocation & discovery
│   │   ├── secrets-manager-read-policy.json   # Least-privilege Secrets Manager read
│   │   ├── cloudwatch-logging-policy.json     # Least-privilege CloudWatch logging & metrics
│   │   └── gitlexa-backend-role-policy.json   # Consolidated application role policy
│   └── trust-policies/
│       ├── ecs-task-trust-policy.json         # Deployment Option A: ECS Task Execution assume-role trust
│       └── irsa-trust-policy.json             # Deployment Option B: EKS IRSA WebIdentity assume-role trust
├── bedrock/                           # Bedrock model orchestration specifications
├── cloudwatch/                        # CloudWatch dashboard and alarm specifications
├── deployment/                        # Container and infrastructure deployment manifests
└── secrets/                           # Secret schema definitions (names, keys, rotation)
```

---

## 3. Policy Specifications & Permission Justifications

### A. Amazon Bedrock Model Invocation (`bedrock-invoke-policy.json`)

| Action | Scoped Resource | Operational Justification & Resource Constraints |
|---|---|---|
| `bedrock:InvokeModel` | `arn:aws:bedrock:<AWS_REGION>::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0`<br>`arn:aws:bedrock:<AWS_REGION>::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0`<br>`arn:aws:bedrock:<AWS_REGION>::foundation-model/anthropic.claude-3-haiku-20240307-v1:0` | Executes agent decision logic, blocker evaluation, and reasoning prompts. Restricted strictly to approved Claude foundation models. |
| `bedrock:InvokeModelWithResponseStream` | `arn:aws:bedrock:<AWS_REGION>::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0`<br>`arn:aws:bedrock:<AWS_REGION>::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0`<br>`arn:aws:bedrock:<AWS_REGION>::foundation-model/anthropic.claude-3-haiku-20240307-v1:0` | Enables streaming LLM completions for interactive UI telemetry and conversational agent responses. Restricted to approved Claude foundation models. |
| `bedrock:GetFoundationModel` | `arn:aws:bedrock:<AWS_REGION>::foundation-model/anthropic.claude-*` | Retrieves model configuration parameters, context window limits, and modalities. Scoped to Claude models. |
| `bedrock:ListFoundationModels` | `*` | **AWS-Required Wildcard**: The `bedrock:ListFoundationModels` API action lists regional models and does **not support resource-level permissions**. AWS IAM returns an error if any resource ARN other than `*` is specified. |

#### Supported Bedrock Models Documentation
1. **Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20240620-v1:0`)**: Primary reasoning engine for complex code analysis, multi-repository blocker correlation, and agent task planning.
2. **Claude 3 Sonnet (`anthropic.claude-3-sonnet-20240229-v1:0`)**: Default baseline model configured in `backend/app/core/config.py` for standard reasoning workflows.
3. **Claude 3 Haiku (`anthropic.claude-3-haiku-20240307-v1:0`)**: High-speed, cost-efficient model for quick intent classification, title sanitization, and metric extraction.

---

### B. AWS Secrets Manager Read Access (`secrets-manager-read-policy.json`)

| Action | Scoped Resource | Operational Justification & Security Scoping |
|---|---|---|
| `secretsmanager:GetSecretValue`<br>`secretsmanager:DescribeSecret` | `arn:aws:secretsmanager:<AWS_REGION>:<AWS_ACCOUNT_ID>:secret:gitlexa/*` | Fetches runtime credentials (e.g., GitHub tokens, integration keys) safely into memory without storing secrets on disk or in repository code. Restricted exclusively to the `gitlexa/*` namespace. |
| `kms:Decrypt` | `arn:aws:kms:<AWS_REGION>:<AWS_ACCOUNT_ID>:key/<KMS_KEY_ID>` | Decrypts secret payloads encrypted with a customer-managed KMS key (CMK). Restricted with condition `kms:ViaService: secretsmanager.<AWS_REGION>.amazonaws.com`, preventing unauthorized use outside Secrets Manager. |

---

### C. CloudWatch Logging & Telemetry (`cloudwatch-logging-policy.json`)

| Action | Scoped Resource | Operational Justification & Security Scoping |
|---|---|---|
| `logs:CreateLogGroup` | `arn:aws:logs:<AWS_REGION>:<AWS_ACCOUNT_ID>:log-group:/gitlexa/*` | Automatically initializes application log groups under `/gitlexa/*` during startup or deployment. |
| `logs:CreateLogStream`<br>`logs:DescribeLogStreams`<br>`logs:PutLogEvents` | `arn:aws:logs:<AWS_REGION>:<AWS_ACCOUNT_ID>:log-group:/gitlexa/*:log-stream:*` | Writes application logs, redacted audit events, and diagnostic traces to CloudWatch Streams. Logs deletion (`logs:Delete*`) is strictly omitted. |
| `cloudwatch:PutMetricData` | `*` (Condition: `cloudwatch:namespace: Gitlexa`) | **AWS-Required Wildcard**: The `cloudwatch:PutMetricData` action does **not support resource-level permissions** (metrics do not possess ARNs). Least-privilege scoping is enforced through the `cloudwatch:namespace` condition key restricted strictly to `"Gitlexa"`. |

---

## 4. Analysis of Wildcard (`"Resource": "*"`) Requirements

In strict accordance with least privilege, wildcard resources are prohibited across the policy suite except for the following **two specific actions** where the AWS API architecture explicitly mandates it:

1. **`bedrock:ListFoundationModels`**:
   - **Why `*` is required**: This is an account-level discovery action to list foundation models available in a region. Per the [AWS Service Authorization Reference for Amazon Bedrock](https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonbedrock.html), `ListFoundationModels` has no resource type and does not accept an ARN.
2. **`cloudwatch:PutMetricData`**:
   - **Why `*` is required**: Custom metrics in Amazon CloudWatch do not have Amazon Resource Names (ARNs). Per the [AWS Service Authorization Reference for CloudWatch](https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazoncloudwatch.html), `PutMetricData` requires `"Resource": "*"`.
   - **Guardrail applied**: Scoped strictly via `"Condition": { "StringEquals": { "cloudwatch:namespace": "Gitlexa" } }` so the principal cannot publish metrics to arbitrary namespaces.

---

## 5. Trust Policies & Deployment Alternatives

The repository provides two trust policy files representing **mutually exclusive deployment alternatives**. Operators must configure only the one corresponding to their deployment target:

```
                  Deploying Gitlexa Backend
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   [Option A: AWS ECS]              [Option B: Amazon EKS]
Use ecs-task-trust-policy.json    Use irsa-trust-policy.json
(Trusts ecs-tasks.amazonaws.com)  (Trusts OIDC Federated Identity)
```

- **Option A: Amazon ECS Task Role (`ecs-task-trust-policy.json`)**:
  - Used when running containerized tasks on Amazon ECS (AWS Fargate or EC2 launch type).
  - Principal: `"Service": "ecs-tasks.amazonaws.com"`.
  - Action: `"sts:AssumeRole"`.

- **Option B: Amazon EKS IAM Roles for Service Accounts / IRSA (`irsa-trust-policy.json`)**:
  - Used when deployed into a Kubernetes cluster on Amazon EKS.
  - Principal: `"Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/<OIDC_PROVIDER>"`.
  - Action: `"sts:AssumeRoleWithWebIdentity"`.
  - Condition: Scoped to ServiceAccount `system:serviceaccount:gitlexa:gitlexa-backend-sa`.

---

## 6. Deployment Guardrails & Compliance

1. **No Real Credentials in Code**: Never commit instantiated account numbers or live secret values.
2. **Automated Verification**: Validate all policy JSON files using `backend/tests/unit/test_iam_policies.py` before applying in production environments.
3. **No Direct AWS Deployment**: Provisioning is performed exclusively through version-controlled Terraform modules or CloudFormation templates in downstream deployment milestones.
