"""GitHub App authentication and setup routes.

Provides official GitHub App installation redirect and post-installation setup callback.
Integrates with the existing GitHubAppAuth singleton and Supabase installation schema.
Never exposes private keys, client secrets, tokens, or personal access tokens to clients.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.core.config import settings
from app.core.logging import logger
from app.github.app_auth import github_app_auth

router = APIRouter()

# In-memory store for active GitHub App installations (mirrors Supabase github_installations table)
# Secrets and tokens are NEVER stored in this record.
installations_store: Dict[int, Dict[str, Any]] = {}


@router.get("/install", summary="Redirect to official GitHub App installation page")
async def github_install(
    request: Request,
    format: Optional[str] = Query(None, description="Set to 'json' to receive raw URL instead of redirect"),
) -> Any:
    """Redirect user's browser to the official GitHub App installation page for Gitlexa's-AI.

    Never redirects to third-party or random OAuth providers.
    Uses official GitHub App installation URL: https://github.com/apps/<slug>/installations/new
    """
    install_url = settings.get_github_app_install_url()
    logger.info("Redirecting browser to GitHub App install URL: %s", install_url)

    accept = request.headers.get("accept", "").lower()
    if format == "json" or ("application/json" in accept and "text/html" not in accept):
        return JSONResponse(
            status_code=200,
            content={
                "app_name": settings.GITHUB_APP_NAME,
                "app_slug": settings.GITHUB_APP_SLUG,
                "install_url": install_url,
            },
            headers={"Location": install_url},
        )

    return RedirectResponse(url=install_url, status_code=302)


@router.get("/setup", summary="GitHub App post-installation setup callback")
async def github_setup(
    request: Request,
    installation_id: Optional[str] = Query(None, description="Installation ID sent by GitHub redirect"),
    setup_action: Optional[str] = Query(None, description="GitHub setup action, e.g. install, update"),
    format: Optional[str] = Query(None, description="Set to 'json' or 'html'"),
    redirect: Optional[bool] = Query(None, description="Explicitly redirect to frontend Project page"),
) -> Any:
    """Handle GitHub App post-installation browser redirect.

    GitHub redirects the user to:
      /api/v1/github/setup?installation_id=174573260&setup_action=install

    Validates installation_id, associates metadata safely without exposing credentials,
    and returns a success response or redirects back to the frontend Project page.
    """
    if installation_id is None or not str(installation_id).strip():
        raise HTTPException(
            status_code=400,
            detail="Missing required installation_id parameter.",
        )

    clean_id_str = str(installation_id).strip()
    if not clean_id_str.isdigit():
        raise HTTPException(
            status_code=400,
            detail="Invalid installation_id parameter. Must be a positive integer.",
        )

    valid_id = int(clean_id_str)
    if valid_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid installation_id parameter. Must be a positive integer.",
        )

    # 1. Update the GitHubAppAuth singleton default installation ID
    github_app_auth.default_installation_id = valid_id

    # 2. Record installation metadata in the process-local store (schema matches github_installations)
    account_login: Optional[str] = None
    account_type: str = "user"

    # Attempt to fetch public account details from GitHub using App JWT if credentials are valid
    if github_app_auth.is_configured:
        try:
            details = await github_app_auth.get_installation_details(valid_id)
            account_data = details.get("account", {})
            if isinstance(account_data, dict):
                account_login = account_data.get("login")
                account_type = str(account_data.get("type", "user")).lower()
        except Exception as exc:
            logger.warning("Could not pre-fetch GitHub installation details for %d: %s", valid_id, exc)

    installations_store[valid_id] = {
        "installation_id": valid_id,
        "account_login": account_login or "pending_lookup",
        "account_type": account_type,
        "connection_type": "app_installation",
        "status": "active",
        "setup_action": setup_action or "install",
        "created_at": time.time(),
        "user_association": "pending (backend user authentication not yet configured)",
    }

    logger.info("GitHub App installation %d successfully registered (action: %s)", valid_id, setup_action)

    frontend_redirect_url = f"{settings.FRONTEND_URL}/project?github=connected&installation_id={valid_id}"
    accept_header = request.headers.get("accept", "").lower()
    wants_html = "text/html" in accept_header and format != "json"

    # Browser redirect flow: if explicit redirect requested or browser navigation (HTML accepted)
    if redirect is True or (redirect is not False and wants_html):
        # Return a pleasant HTML bridge page that displays confirmation and redirects immediately
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>GitHub App Connected — Gitlexa</title>
  <meta http-equiv="refresh" content="1;url={frontend_redirect_url}">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0b0f19;
      color: #e7ecf9;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
    }}
    .card {{
      background: #121826;
      border: 1px solid #1f293d;
      border-radius: 12px;
      padding: 32px 40px;
      text-align: center;
      max-width: 480px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }}
    h1 {{ font-size: 20px; margin: 0 0 12px; color: #4ade80; }}
    p {{ font-size: 14px; color: #929eb2; line-height: 1.6; margin: 8px 0; }}
    code {{ background: #1a2234; padding: 2px 8px; border-radius: 4px; color: #60a5fa; font-size: 13px; }}
    a {{ display: inline-block; margin-top: 16px; color: #60a5fa; text-decoration: none; font-weight: 500; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>GitHub connected successfully.</h1>
    <p>Installation ID: <code>{valid_id}</code></p>
    <p>Redirecting back to your Gitlexa workspace...</p>
    <a href="{frontend_redirect_url}">Click here if not redirected automatically</a>
  </div>
</body>
</html>"""
        return HTMLResponse(content=html_content, status_code=200)

    # JSON response flow (for API clients, automated tests, curl)
    return {
        "status": "success",
        "message": "GitHub connected successfully.",
        "installation_id": valid_id,
        "setup_action": setup_action or "install",
        "account_login": account_login,
        "account_type": account_type,
        "user_association": "pending (backend user authentication not yet configured)",
    }


@router.get("/status", summary="Public GitHub App connection status")
async def github_connection_status() -> Dict[str, Any]:
    """Retrieve public status of GitHub App connection.

    Never exposes private keys, client secrets, or raw installation access tokens.
    """
    public_status = github_app_auth.get_public_status()
    installed_ids = list(installations_store.keys())
    return {
        **public_status,
        "active_installations": installed_ids,
        "installed_count": len(installed_ids),
    }
