import os
from typing import Optional

import requests


class EmailError(Exception):
    pass


def _send_via_resend(
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    html: Optional[str] = None,
    text: Optional[str] = None,
):
    url = "https://api.resend.com/emails"
    payload = {
        "from": from_email,
        "to": to_email,
        "subject": subject,
    }
    if html:
        payload["html"] = html
    if text:
        payload["text"] = text

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    if resp.status_code >= 300:
        raise EmailError(f"Resend API error {resp.status_code}: {resp.text}")
    return resp.json()


def send_email(
    to_email: str,
    subject: str,
    html: Optional[str] = None,
    text: Optional[str] = None,
    *,
    from_email: Optional[str] = None,
):
    """
    Send an email using the configured provider.

    Environment variables:
      - EMAIL_PROVIDER: 'resend' (default)
      - EMAIL_API_KEY: API key for the provider
      - EMAIL_FROM: default from address ("EVisionBet <noreply@yourdomain>")
    """
    provider = os.getenv("EMAIL_PROVIDER", "resend").lower()
    api_key = os.getenv("EMAIL_API_KEY")
    from_addr = from_email or os.getenv("EMAIL_FROM")

    if not api_key:
        raise EmailError("EMAIL_API_KEY not configured")
    if not from_addr:
        raise EmailError("EMAIL_FROM not configured")

    if provider == "resend":
        return _send_via_resend(
            api_key,
            from_addr,
            to_email,
            subject,
            html,
            text,
        )

    raise EmailError(f"Unsupported EMAIL_PROVIDER: {provider}")
