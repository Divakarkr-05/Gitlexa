# Gitlexa — Hackathon Rules & Compliance

## 1. Hackathon Context & Scope
Gitlexa is built as a hackathon submission integrating Generative AI, Cloud Services (AWS Bedrock), Model Context Protocol (MCP), and Voice (Alexa+) to deliver real-time developer operations intelligence and automated blocker triage.

## 2. Core Hackathon Directives
1. **Model Governance**: Primary foundation models must leverage Amazon Bedrock (e.g., Claude 3 Sonnet / Claude 3 Haiku).
2. **Protocol Standard**: Inter-tool communication must conform to the Model Context Protocol (MCP) standard.
3. **No Synthetic Shortcuts in Production Evaluation**: Verification benchmarks must run against reproducible scenarios, not hardcoded mock responses.
4. **Originality & Intellectual Property**: All architectural models, prompts, evidence correlations, and frontend components must be original work.
5. **Clean Boundaries**: Each team member operates strictly within their assigned ownership domain to avoid merge conflicts and scope creep.

## 3. Strict Prohibitions
- **No Hardcoded Secrets**: Zero credentials, tokens, or private keys allowed in git history.
- **No Premature Feature Code in Foundation**: Foundation commit must contain only contracts, structure, boundaries, and governance.
- **No Overlapping Implementations**: Evidence Engine belongs exclusively to Member 01; GitHub data retrieval belongs exclusively to Member 03; Agent orchestration belongs to Member 02.
