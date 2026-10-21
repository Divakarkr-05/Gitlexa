# Gitlexa — Failure Prevention & Risk Mitigation

## 1. Technical Risks & Guardrails

| Risk | Impact | Prevention Strategy |
|---|---|---|
| **AWS Bedrock Rate Limits / Quotas** | Agent query failure during demo | Configure exponential backoff; cache static query results; have fallback Haiku/Sonnet failover. |
| **GitHub API Rate Limits** | Data collection breaks | Use authenticated tokens (5,000 req/hr); cache repository tree snapshots; implement conditional requests (`ETag`). |
| **Voice Latency (Alexa+ to Backend)** | Unresponsive voice response | Pre-warm agent endpoints; keep speech response under 3 sentences; stream telemetry asynchronously. |
| **LLM Hallucinations on Blocker Causes** | Incorrect recommendations | Strict Evidence Schema enforcement; reject any agent assertion not tied to a specific evidence object. |
| **Merge Conflicts Between Team Members** | Integration delays | Enforce strict subsystem ownership boundaries: Member 01 (Evidence/Cloud/Eval), Member 02 (Agent/MCP), Member 03 (GitHub), Member 04 (Frontend), Member 05 (Alexa+), Member 06 (QA/Docs). |

## 2. Emergency Plan for Demo Day
- Maintain a local pre-indexed test repository fixture (`backend/tests/evaluation/scenarios.json`).
- Ensure mock fallback modes can run locally without external cloud connectivity if the venue Wi-Fi fails.
