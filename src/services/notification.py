import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Load .env from the server directory
server_dir = Path(__file__).resolve().parent.parent.parent
env_path = server_dir / '.env'
load_dotenv(dotenv_path=env_path)

class EmailNotificationService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv('EMAIL_ADDRESS')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        
        # Add validation for environment variables
        if not self.sender_email or not self.sender_password:
            logging.error("Email configuration is missing. Please check your .env file for EMAIL_ADDRESS and EMAIL_PASSWORD")
            logging.error(f"Current .env path: {env_path}")
            logging.error(f"EMAIL_ADDRESS: {'Set' if self.sender_email else 'Not Set'}")
            logging.error(f"EMAIL_PASSWORD: {'Set' if self.sender_password else 'Not Set'}")

    def generate_otp(self):
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))

    def send_registration_email(self, user_email, user_name):
        """
        Send a welcome email to newly registered users
        """
        try:
            if not self.sender_email or not self.sender_password:
                raise ValueError("Email configuration is missing. Check .env file.")

            # Generate OTP for email verification
            otp = self.generate_otp()

            # Create the email message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = user_email
            msg['Subject'] = "Welcome to AI Travel Assistant - Verify Your Email"

            # Email body
            body = f"""
            Dear {user_name},

            Welcome to AI Travel Assistant! We're excited to have you on board.

            To complete your registration, please use the following verification code:

            Your Verification Code: {otp}

            This code will expire in 10 minutes. Please enter this code in the verification page to activate your account.

            Thank you for registering with us. We're here to help make your travel planning experience 
            seamless and enjoyable.

            Best regards,
            The AI Travel Assistant Team
            """

            msg.attach(MIMEText(body, 'plain'))

            # Create SMTP session
            logging.info(f"Attempting to connect to SMTP server: {self.smtp_server}:{self.smtp_port}")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            logging.info(f"Attempting to login with email: {self.sender_email}")
            server.login(self.sender_email, self.sender_password)

            # Send email
            text = msg.as_string()
            server.sendmail(self.sender_email, user_email, text)
            server.quit()
            
            logging.info(f"Email sent successfully to {user_email}")
            return True, otp

        except ValueError as ve:
            logging.error(f"Configuration Error: {str(ve)}")
            return False, None
        except smtplib.SMTPAuthenticationError as auth_error:
            logging.error(f"SMTP Authentication Error: {str(auth_error)}")
            logging.error("This usually means your email or password is incorrect, or you need to enable 'Less secure app access' or use an App Password")
            return False, None
        except Exception as e:
            logging.error(f"Unexpected error while sending email: {str(e)}")
            return False, None

# Create an instance of the notification service
notification_service = EmailNotificationService()
