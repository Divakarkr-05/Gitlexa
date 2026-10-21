# Gitlexa — Demo Strategy & Presentation Flow

## 1. Demo Objectives
Deliver a crisp, compelling 3-minute presentation highlighting the end-to-end integration:
Voice query (Alexa+) $\rightarrow$ MCP & Bedrock Agent reasoning $\rightarrow$ Evidence correlation $\rightarrow$ Live Web Dashboard updates.

## 2. Narrative Arc
1. **The Hook (Standup Friction)**:
   - Present a realistic scenario: "It's 9:00 AM, the build failed overnight, and 3 PRs are pending review. Who is blocked?"
2. **The Voice Interaction**:
   - The presenter asks Alexa+: *"Alexa, ask Gitlexa: What is blocking our main branch?"*
   - Alexa+ calls the Gitlexa MCP bridge, queries the Bedrock agent, and speaks a concise verbal summary of the highest-severity blocker.
3. **The Deep-Dive Dashboard**:
   - Show the live React dashboard synchronizing in real time.
   - Point out the Evidence Graph: the failing CI step, correlated PR #42 modifying the test fixture, and the proposed resolution.
4. **Autonomous Triage**:
   - Demonstrate the agent executing the `draft_issue` MCP tool to draft an automated remediation ticket with full context.

## 3. Demo Fallback & Reliability Guardrails
- **Pre-seeded Scenario**: Have a standard synthetic repository scenario (`scenarios.json`) deployed and validated.
- **Network Resilience**: Maintain local mock recording buffers in case external network latency causes timeouts during live judging.
