from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.config import settings
from app.models.users import AuthUser   
from datetime import datetime
# -------------------------------------------------------------------
# Email Configuration
# -------------------------------------------------------------------
conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAILS_FROM_EMAIL,
    MAIL_FROM_NAME=settings.EMAILS_FROM_NAME,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

# -------------------------------------------------------------------
# 🧩 Template Loader
# -------------------------------------------------------------------
env = Environment(
    loader=FileSystemLoader("app/templates/email"),
    autoescape=select_autoescape(["html", "xml"])
)

# -------------------------------------------------------------------
# Password Reset Email
# -------------------------------------------------------------------
async def send_otp(to_email: str, otp: int, expiry_minutes: int):
    print(f"[SMTP] Preparing OTP email for {to_email}")

    subject = "Taskify | Password Reset OTP"
    template = env.get_template("reset_password_otp.html")
    current_year = datetime.now().year

    html_content = template.render(
        otp=otp,
        year=current_year,
        expiry_minutes=expiry_minutes
    )

    print("[SMTP] Email template rendered")

    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=html_content,
        subtype="html",
        headers={
        "X-Mailer": "Taskify",
        "Precedence": "Transactional"
    }
    )

    fm = FastMail(conf)
    print("[SMTP] Connecting to SMTP server...")
    
    await fm.send_message(message)

    print("[SMTP] Email dispatched to SMTP server")

async def user_registered(to_email: str, full_name: str):
    subject = "Registration Success"
    template = env.get_template("registation_success.html")
    html_content = template.render(
        full_name=full_name,
    )

    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=html_content,
        subtype="html",
        headers={
        "X-Mailer": "Taskify",
        "Precedence": "Transactional"
    }
    )

    fm = FastMail(conf)
    await fm.send_message(message)