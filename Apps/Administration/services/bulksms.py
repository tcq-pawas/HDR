"""BulkSMS.com OTP SMS service.

This is the exclusive SMS provider for OTP delivery.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

BULKSMS_API_URL = "https://api.bulksms.com/v1/messages"

OTP_MESSAGE_TEMPLATE = (
    "Your Hhectare login OTP is {otp}. Valid for 10 minutes. "
    "Do not share this OTP. - Hhectare"
)


def format_phone_for_bulksms(phone_number: str) -> str | None:
    """
    Normalize a phone number to E.164-style for BulkSMS (+91...).

    Accepts values such as:
    - 9876543210
    - 919876543210
    - +919876543210
    - 91-98765-43210
    """
    if phone_number is None:
        return None

    raw = str(phone_number).strip()
    if not raw:
        return None

    had_plus = raw.startswith("+")
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None

    # Already international with country code 91
    if digits.startswith("91") and len(digits) == 12:
        return f"+{digits}"

    # Plain 10-digit Indian mobile
    if len(digits) == 10:
        return f"+91{digits}"

    # Explicit + with other valid length (keep as-is if already international)
    if had_plus and 11 <= len(digits) <= 15:
        return f"+{digits}"

    # 11–15 digits without +: assume already includes country code
    if 11 <= len(digits) <= 15:
        return f"+{digits}"

    return None


def build_otp_message(otp: str) -> str:
    return OTP_MESSAGE_TEMPLATE.format(otp=otp)


def _safe_response_body(response: requests.Response) -> str:
    """Return a truncated response body for logging (no secrets)."""
    try:
        text = (response.text or "")[:500]
    except Exception:
        text = "<unavailable>"
    return text


def send_otp_sms(phone_number: str, otp: str) -> dict[str, Any]:
    """
    Send an OTP SMS via BulkSMS.com.

    Returns a predictable result dict:
    {
        "success": bool,
        "error_code": str | None,
        "message": str,
        "status_code": int | None,
    }
    """
    token_id = getattr(settings, "BULKSMS_TOKEN_ID", None) or ""
    token_secret = getattr(settings, "BULKSMS_TOKEN_SECRET", None) or ""
    sender = getattr(settings, "BULKSMS_SENDER", None) or "HECTRE"

    if not token_id or not token_secret:
        logger.error("BulkSMS credentials are not configured (BULKSMS_TOKEN_ID / BULKSMS_TOKEN_SECRET).")
        return {
            "success": False,
            "error_code": "missing_credentials",
            "message": "SMS provider is not configured.",
            "status_code": None,
        }

    formatted_phone = format_phone_for_bulksms(phone_number)
    if not formatted_phone:
        logger.warning("Invalid phone number for BulkSMS OTP send.")
        return {
            "success": False,
            "error_code": "invalid_phone",
            "message": "Invalid phone number.",
            "status_code": None,
        }

    if not otp:
        return {
            "success": False,
            "error_code": "invalid_otp",
            "message": "OTP value is required.",
            "status_code": None,
        }

    payload = [
        {
            "to": formatted_phone,
            "body": build_otp_message(str(otp)),
            "from": sender,
        }
    ]

    try:
        response = requests.post(
            BULKSMS_API_URL,
            json=payload,
            auth=HTTPBasicAuth(token_id, token_secret),
            timeout=15,
            headers={"Content-Type": "application/json"},
        )
    except requests.exceptions.Timeout:
        logger.error("BulkSMS request timed out.")
        return {
            "success": False,
            "error_code": "timeout",
            "message": "SMS provider timed out.",
            "status_code": None,
        }
    except requests.exceptions.ConnectionError:
        logger.error("BulkSMS connection error.")
        return {
            "success": False,
            "error_code": "connection_error",
            "message": "Unable to reach SMS provider.",
            "status_code": None,
        }
    except requests.exceptions.RequestException as exc:
        logger.error("BulkSMS request failed: %s", type(exc).__name__)
        return {
            "success": False,
            "error_code": "request_error",
            "message": "SMS provider request failed.",
            "status_code": None,
        }

    status_code = response.status_code
    body_preview = _safe_response_body(response)

    if status_code in (200, 201):
        logger.info("BulkSMS OTP SMS accepted (status=%s).", status_code)
        return {
            "success": True,
            "error_code": None,
            "message": "OTP SMS sent successfully.",
            "status_code": status_code,
        }

    # Map common provider failures without exposing credentials
    if status_code in (401, 403):
        error_code = "auth_failed"
        message = "SMS provider authentication failed."
    elif status_code == 400:
        error_code = "bad_request"
        message = "SMS provider rejected the request."
        # Detect credit/balance hints without leaking full payload details
        lower = body_preview.lower()
        if any(token in lower for token in ("credit", "balance", "insufficient", "quota")):
            error_code = "insufficient_credits"
            message = "SMS provider reported insufficient credits."
    elif status_code == 429:
        error_code = "rate_limited"
        message = "SMS provider rate limit exceeded."
    elif 500 <= status_code < 600:
        error_code = "provider_error"
        message = "SMS provider is temporarily unavailable."
    else:
        error_code = f"http_{status_code}"
        message = "SMS provider returned an unexpected error."

    logger.error(
        "BulkSMS OTP send failed (status=%s, error_code=%s, body=%s).",
        status_code,
        error_code,
        body_preview,
    )
    return {
        "success": False,
        "error_code": error_code,
        "message": message,
        "status_code": status_code,
    }
