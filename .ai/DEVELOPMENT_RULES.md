# Development Rules & Boundaries

## 1. General Principles
- **No Premature Implementation**: Establish interfaces, type definitions, and test scenarios before writing business logic.
- **Declarative Contracts**: All request/response structures must use Pydantic models (backend) or TypeScript interfaces (frontend).
- **Subsystem Isolation**: Backend, frontend, alexa, and infra are decoupled; communicate strictly across defined interfaces.

## 2. Python Standards (Backend & Alexa)
- Python 3.11+ compatibility.
- Follow PEP 8 guidelines; enforce using `black` and `ruff`.
- Complete type annotations (`typing`, Pydantic v2).
- Asynchronous I/O (`async`/`await`) for all network operations (FastAPI, httpx, boto3).

## 3. Frontend Standards
- React 18 functional components with hooks.
- TypeScript strict mode enabled (`"strict": true`).
- Clean separation of presentation components and data-fetching hooks.

## 4. Git & Commit Hygiene
- Format: `<type>(<scope>): <summary>` (e.g. `feat(mcp): add read_ci_status tool`).
- Atomic commits focused on single concerns.
- Do not commit generated build artifacts, virtual environments, or credentials.
