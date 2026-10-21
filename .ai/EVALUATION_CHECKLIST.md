# Gitlexa — Evaluation & Judging Checklist

## 1. Judging Criteria Alignment

### A. Technical Execution & Architecture (25%)
- [ ] Clean separation of concerns between backend, frontend, MCP, and voice layers.
- [ ] Proper error handling, logging, and typing contracts across all subsystems.
- [ ] Secure credential management (zero tokens in git; environment-driven config).

### B. Use of AWS & Generative AI (25%)
- [ ] Amazon Bedrock foundation models effectively leveraged for task planning and blocker correlation.
- [ ] High accuracy and low latency in agent reasoning.
- [ ] Model Context Protocol (MCP) correctly orchestrating tools.

### C. Voice Integration & User Experience (20%)
- [ ] Alexa+ voice interaction model feels natural, concise, and standup-friendly.
- [ ] Web dashboard is responsive, aesthetically polished, and clearly displays correlated evidence.

### D. Evidence Quality & Blocker Accuracy (20%)
- [ ] Blocker detection outputs cite real commit SHAs, PR numbers, and CI logs.
- [ ] Severity scores accurately reflect production impact.

### E. Presentation & Demo (10%)
- [ ] Clear narrative flow from problem to voice query to visual resolution.
- [ ] Working live demonstration within time limits.
