# Member 01: Cloud + AWS + Security + DevOps + Evidence Engine + Evaluation

## Ownership
- **Directories**:
  - `infra/`
  - `.github/`
  - `backend/app/core/`
  - `backend/app/evidence/`
  - `backend/tests/evaluation/`
- **Technologies**: AWS Bedrock, IAM, Secrets Manager, CloudWatch, Docker, GitHub Actions CI, Pydantic, Evidence Correlation Algorithms.

## Core Responsibilities
1. **Cloud & Security**:
   - Manage AWS infrastructure, IAM least-privilege policies, and environment credential hygiene.
   - Maintain Docker multi-container setups and GitHub Actions CI/CD workflows (`.github/workflows/`).
   - Maintain `backend/app/core/` (config, logging, security, exceptions).
2. **Evidence Engine**:
   - Sole and exclusive owner of `backend/app/evidence/`.
   - Build evidence collection schemas, correlation algorithms, blocker detection heuristics, and severity scoring.
   - Format evidence outputs for consumption by Member 02's Agent and frontend.
3. **Evaluation Benchmarks**:
   - Maintain `backend/tests/evaluation/` (scenarios, expected results, and evaluation harness).

## Strict Boundaries
- Member 01 is the sole owner and implementer of the Evidence Engine.
- Do not build GitHub API client integrations (owned by Member 03).
- Do not build Agent reasoning or MCP tools (owned by Member 02).
