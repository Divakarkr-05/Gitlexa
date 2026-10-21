# Member 05: Alexa+ Integration

## Ownership
- **Directories**:
  - `alexa/`
- **Technologies**: Alexa Skills Kit (ASK), ASK SDK Python, Voice Interaction Models, MCP Client Bridge.

## Core Responsibilities
1. **Alexa Skill & Interaction Models**:
   - Design and maintain `alexa/skill/skill.json` and `alexa/skill/interaction-model.json`.
   - Define custom intents (e.g. `CheckRepoHealthIntent`, `GetBlockersIntent`, `StandupBriefingIntent`) and realistic sample utterances.
2. **Voice-to-MCP Client Bridge**:
   - Implement `alexa/mcp/client.py` and `alexa/mcp/tools.py` connecting voice intent handlers to the backend MCP server.
   - Format concise verbal responses suited for fast standup consumption (keeping responses under 3 sentences).

## Strict Boundaries
- Voice layer delegates all repository analysis to the backend MCP server.
- Do not implement duplicate evidence or GitHub logic inside Alexa skill.
