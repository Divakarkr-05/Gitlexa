# Gitlexa — Project Context & Hackathon Vision

## 1. Executive Summary
Gitlexa is an intelligent AI-assisted GitHub operations and voice-enabled repository insights platform. It bridges repository telemetry (CI/CD status, commit history, pull request reviews, open issues) with Amazon Bedrock foundation models and the Model Context Protocol (MCP). Through either an intuitive React web dashboard or hands-free Alexa voice interactions, developers and engineering leaders can instantly query repo health, detect delivery blockers, and orchestrate automated triage.

## 2. Core Value Proposition
- **Voice-Activated Repository Telemetry**: Ask Alexa about build statuses, failing workflows, or blocking pull requests during standups.
- **MCP-Native Tooling**: Modular Model Context Protocol server exposing granular GitHub queries (`list_issues`, `read_ci_status`, `search_code`, etc.) to LLM reasoning agents.
- **Evidence-Based Blocker Detection**: Correlates failing test outputs, conflicting PR diffs, and stale issue discussions into verifiable blocker reports.

## 3. Hackathon Scope & Boundaries
- **Primary Platform**: AWS Bedrock (Claude 3 Sonnet / Haiku) + Model Context Protocol.
- **Integrations**: GitHub REST/GraphQL API + Amazon Alexa Skill Kit.
- **Target Audience**: DevOps engineers, Scrum Masters, individual developers, and tech leads.
