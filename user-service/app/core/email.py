import re
import logging
import aiosmtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import List, Optional

from jinja2 import Template
from app.core.config import settings

logger = logging.getLogger(__name__)

# Email Templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: Optional[str] = None,
) -> bool:
    """
    Send an email using configured SMTP server.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content of the email
        from_email: Sender email (defaults to settings.MAIL_FROM)
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not from_email:
        from_email = settings.MAIL_FROM
        
    message = EmailMessage()
    message["From"] = f"{settings.MAIL_FROM_NAME} <{from_email}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.add_alternative(html_content, subtype="html")
    
    try:
        smtp = aiosmtplib.SMTP(
            hostname=settings.MAIL_SERVER,
            port=settings.MAIL_PORT,
            use_tls=settings.MAIL_TLS,
        )
        
        await smtp.connect()
        
        if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
            await smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        
        await smtp.send_message(message)
        await smtp.quit()
        
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def render_template(template_name: str, **kwargs) -> str:
    """
    Render a Jinja2 template with provided parameters.
    
    Args:
        template_name: Name of the template file
        **kwargs: Variables to pass to the template
        
    Returns:
        str: Rendered HTML content
    """
    template_path = TEMPLATES_DIR / template_name
    
    if not template_path.exists():
        # Use basic fallback template if file doesn't exist
        if template_name == "email_verification.html":
            return f"""
            <h1>Verify Your Email</h1>
            <p>Please click the link below to verify your email address:</p>
            <p><a href="{kwargs.get('verification_url', '')}">Verify Email</a></p>
            """
        elif template_name == "password_reset.html":
            return f"""
            <h1>Reset Your Password</h1>
            <p>Please click the link below to reset your password:</p>
            <p><a href="{kwargs.get('reset_url', '')}">Reset Password</a></p>
            """
        else:
            return f"""
            <h1>{kwargs.get('subject', 'Notification')}</h1>
            <p>{kwargs.get('content', '')}</p>
            """
    
    # Read and render the actual template file
    with open(template_path, "r") as f:
        template_content = f.read()
    
    template = Template(template_content)
    return template.render(**kwargs)


async def send_verification_email(email: str, token: str) -> bool:
    """
    Send an email verification link.
    
    Args:
        email: The user's email address
        token: The verification token
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    verification_url = f"{settings.VERIFY_EMAIL_URL}?token={token}"
    
    html_content = render_template(
        "email_verification.html",
        verification_url=verification_url,
        user_email=email,
    )
    
    return await send_email(
        to_email=email,
        subject="Verify Your Email Address",
        html_content=html_content,
    )


async def send_password_reset_email(email: str, token: str) -> bool:
    """
    Send a password reset link.
    
    Args:
        email: The user's email address
        token: The password reset token
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    reset_url = f"{settings.RESET_PASSWORD_URL}?token={token}"
    
    html_content = render_template(
        "password_reset.html",
        reset_url=reset_url,
        user_email=email,
    )
    
    return await send_email(
        to_email=email,
        subject="Reset Your Password",
        html_content=html_content,
    )


async def send_welcome_email(email: str, name: str) -> bool:
    """
    Send a welcome email to new users.
    
    Args:
        email: The user's email address
        name: The user's name
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    html_content = render_template(
        "welcome.html",
        user_name=name,
        user_email=email,
    )
    
    return await send_email(
        to_email=email,
        subject="Welcome to Our E-commerce Platform",
        html_content=html_content,
    )