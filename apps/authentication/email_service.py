"""
Email service for authentication OTP functionality
"""

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending authentication emails"""
    
    @staticmethod
    def send_otp_email(user, email, otp_code):
        """
        Send OTP verification email to user
        
        Args:
            user: User object
            email: Email address to send to
            otp_code: OTP code to send
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Log email configuration for debugging
            logger.info(f"Email configuration - Host: {settings.EMAIL_HOST}, Port: {settings.EMAIL_PORT}")
            logger.info(f"Email user: {settings.EMAIL_HOST_USER}, From: {settings.DEFAULT_FROM_EMAIL}")

            subject = 'Verify Your Email - Sisimpur'
            
            # Create email context
            context = {
                'user': user,
                'otp_code': otp_code,
                'expiry_minutes': settings.OTP_CONFIG.get('OTP_EXPIRY_MINUTES', 10),
                'site_name': 'Sisimpur',
            }
            
            # Create HTML email content
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Email Verification - Sisimpur</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f4f4f4;
                    }}
                    .container {{
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 0 20px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .logo {{
                        font-size: 28px;
                        font-weight: bold;
                        color: #4f46e5;
                        margin-bottom: 10px;
                    }}
                    .otp-code {{
                        background: #f8fafc;
                        border: 2px dashed #4f46e5;
                        padding: 20px;
                        text-align: center;
                        margin: 20px 0;
                        border-radius: 8px;
                    }}
                    .otp-number {{
                        font-size: 32px;
                        font-weight: bold;
                        color: #4f46e5;
                        letter-spacing: 8px;
                        font-family: 'Courier New', monospace;
                    }}
                    .warning {{
                        background: #fef3cd;
                        border: 1px solid #fecaca;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        color: #666;
                        font-size: 14px;
                    }}
                    .btn {{
                        display: inline-block;
                        padding: 12px 24px;
                        background: #4f46e5;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 10px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">🧠 SISIMPUR</div>
                        <h2>Email Verification Required</h2>
                    </div>
                    
                    <p>Hello <strong>{user.username}</strong>,</p>
                    
                    <p>Welcome to Sisimpur! To complete your account setup, please verify your email address using the OTP code below:</p>
                    
                    <div class="otp-code">
                        <p style="margin: 0; font-size: 16px; color: #666;">Your verification code is:</p>
                        <div class="otp-number">{otp_code}</div>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong>
                        <ul style="margin: 10px 0;">
                            <li>This code will expire in <strong>{context['expiry_minutes']} minutes</strong></li>
                            <li>Do not share this code with anyone</li>
                            <li>If you didn't request this, please ignore this email</li>
                        </ul>
                    </div>
                    
                    <p>Enter this code on the verification page to activate your account and start using Sisimpur's AI-powered exam preparation tools.</p>
                    
                    <div class="footer">
                        <p>This email was sent to <strong>{email}</strong></p>
                        <p>© 2025 Sisimpur - AI-Powered Exam Prep</p>
                        <p style="font-size: 12px;">If you have any issues, please contact our support team.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            plain_message = f"""
            Email Verification - Sisimpur
            
            Hello {user.username},
            
            Welcome to Sisimpur! To complete your account setup, please verify your email address.
            
            Your verification code is: {otp_code}
            
            Important:
            - This code will expire in {context['expiry_minutes']} minutes
            - Do not share this code with anyone
            - If you didn't request this, please ignore this email
            
            Enter this code on the verification page to activate your account.
            
            This email was sent to {email}
            © 2025 Sisimpur - AI-Powered Exam Prep
            """
            
            # Send email
            result = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            if result:
                logger.info(f"OTP email sent successfully to {email}")
                return True
            else:
                logger.error(f"Failed to send OTP email to {email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending OTP email to {email}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user, email):
        """
        Send welcome email after successful verification
        
        Args:
            user: User object
            email: Email address to send to
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            subject = 'Welcome to Sisimpur! 🎉'
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f4f4f4;
                    }}
                    .container {{
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 0 20px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .logo {{
                        font-size: 28px;
                        font-weight: bold;
                        color: #4f46e5;
                        margin-bottom: 10px;
                    }}
                    .success {{
                        background: #d1fae5;
                        border: 1px solid #10b981;
                        padding: 20px;
                        border-radius: 8px;
                        text-align: center;
                        margin: 20px 0;
                    }}
                    .btn {{
                        display: inline-block;
                        padding: 12px 24px;
                        background: #4f46e5;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 10px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">🧠 SISIMPUR</div>
                        <h2>Welcome to Sisimpur!</h2>
                    </div>
                    
                    <div class="success">
                        <h3>🎉 Account Verified Successfully!</h3>
                        <p>Your email has been verified and your account is now active.</p>
                    </div>
                    
                    <p>Hello <strong>{user.username}</strong>,</p>
                    
                    <p>Congratulations! Your Sisimpur account is now ready to use. You can now:</p>
                    
                    <ul>
                        <li>📄 Upload documents (PDFs, images)</li>
                        <li>🤖 Generate AI-powered questions</li>
                        <li>📝 Create custom quizzes</li>
                        <li>📊 Track your progress</li>
                        <li>🎯 Prepare for exams efficiently</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:8000/app/" class="btn">Start Using Sisimpur</a>
                    </div>
                    
                    <p>If you have any questions or need help getting started, feel free to reach out to our support team.</p>
                    
                    <div style="text-align: center; margin-top: 30px; color: #666; font-size: 14px;">
                        <p>© 2025 Sisimpur - AI-Powered Exam Prep</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            Welcome to Sisimpur!
            
            Hello {user.username},
            
            Congratulations! Your Sisimpur account is now ready to use.
            
            You can now:
            - Upload documents (PDFs, images)
            - Generate AI-powered questions
            - Create custom quizzes
            - Track your progress
            - Prepare for exams efficiently
            
            Visit http://localhost:8000/app/ to get started!
            
            © 2025 Sisimpur - AI-Powered Exam Prep
            """
            
            result = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=True,  # Don't fail if welcome email fails
            )
            
            logger.info(f"Welcome email sent to {email}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {email}: {str(e)}")
            return False
