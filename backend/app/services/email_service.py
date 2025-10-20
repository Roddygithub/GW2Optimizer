"""
Email Service Module

This module simulates sending emails for actions like registration and password recovery.
In a production environment, this should be replaced with a real email sending service
(e.g., using libraries like fastapi-mail with a provider like SendGrid or Mailgun).
"""

from app.core.logging import logger
from app.core.config import settings


async def send_verification_email(email_to: str, username: str):
    """
    Simulates sending a verification email to a new user.
    """
    # In a real app, you would generate a verification token and a URL
    verification_link = f"http://{settings.SERVER_HOST}/verify?token=some_verification_token"
    logger.info("---- SENDING VERIFICATION EMAIL (SIMULATED) ----")
    logger.info(f"To: {email_to}")
    logger.info(f"Subject: Welcome to GW2Optimizer, {username}!")
    logger.info(f"Body: Please verify your email by clicking here: {verification_link}")
    logger.info("-------------------------------------------------")


async def send_password_reset_email(email_to: str, token: str):
    """
    Simulates sending a password reset email.
    """
    reset_link = f"http://{settings.SERVER_HOST}/reset-password?token={token}"
    logger.info("---- SENDING PASSWORD RESET EMAIL (SIMULATED) ----")
    logger.info(f"To: {email_to}")
    logger.info(f"Subject: GW2Optimizer - Password Reset Request")
    logger.info(f"Body: Please reset your password by clicking here: {reset_link}")
    logger.info("--------------------------------------------------")
