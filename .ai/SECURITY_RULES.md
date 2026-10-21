# Security & Compliance Rules

## 1. Credential Management
- **ZERO Hardcoded Secrets**: Under no circumstances should GitHub PATs, AWS access keys, or session tokens be hardcoded in any file.
- **Local Development**: Use `.env` files (loaded via `python-dotenv`) which must remain listed in `.gitignore`.
- **Production / Cloud**: Use AWS Secrets Manager and IAM Roles for Service Accounts (IRSA).

## 2. GitHub Token Scopes
- Request strictly read-only scopes (`repo:status`, `public_repo`, `read:org`) unless issue drafting is explicitly triggered by user consent.
- Enforce token rotation and sanitize authorization headers in logs.

## 3. Input Validation & Prompt Injection Defense
- Validate all incoming REST and MCP payloads with Pydantic schemas.
- Sanitize voice transcriptions and repository issue titles before passing into Bedrock prompts to guard against prompt injection.

## 4. Network & Transport Security
- TLS 1.3 enforced for all external communications.
- CORS restricted to configured localhost origins in development.
