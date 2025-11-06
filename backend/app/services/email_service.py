"""
Email Service Module

This module simulates sending emails for actions like registration and password recovery.
In a production environment, this should be replaced with a real email sending service
(e.g., using libraries like fastapi-mail with a provider like SendGrid or Mailgun).
"""

from app.core.logging import logger


def _mask_token(token: str) -> str:
    """Return a masked representation to avoid logging sensitive tokens."""

    if not token:
        return "<empty>"

    # Preserve only the last 4 characters to aid debugging if needed
    visible_suffix = token[-4:] if len(token) > 4 else token
    return f"***{visible_suffix}"


async def send_verification_email(email_to: str, username: str, verification_token: str = ""):
    """
    Simulates sending a verification email to a new user.
    """
    logger.info("---- SENDING VERIFICATION EMAIL (SIMULATED) ----")
    logger.info(f"To: {email_to}")
    logger.info(f"Subject: Welcome to GW2Optimizer, {username}!")
    logger.info("Body: Verification link generated; token omitted from logs")
    logger.info("-------------------------------------------------")


async def send_password_reset_email(email_to: str, token: str):
    """
    Simulates sending a password reset email.
    """
    logger.info("---- SENDING PASSWORD RESET EMAIL (SIMULATED) ----")
    logger.info(f"To: {email_to}")
    logger.info("Subject: GW2Optimizer - Password Reset Request")
    logger.info("Body: Password reset link generated; token omitted from logs")
    logger.info("--------------------------------------------------")
