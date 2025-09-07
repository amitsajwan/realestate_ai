import logging
from typing import Optional, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@propertyai.com")
        self.from_name = os.getenv("FROM_NAME", "PropertyAI")
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email"""
        if not self.enabled:
            logger.info(f"Email service disabled. Would send email to {to_email}: {subject}")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_welcome_email(
        self,
        agent_email: str,
        agent_name: str,
        agent_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send welcome email to new agent"""
        subject = f"Welcome to PropertyAI, {agent_name}!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background-color: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .feature {{ margin: 15px 0; padding: 15px; background-color: white; border-radius: 5px; }}
                .footer {{ margin-top: 30px; text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to PropertyAI!</h1>
                    <p>Your AI-Powered Real Estate Assistant</p>
                </div>
                
                <div class="content">
                    <h2>Hi {agent_name},</h2>
                    
                    <p>Welcome to PropertyAI! We're thrilled to have you join our community of innovative real estate professionals.</p>
                    
                    <p>Your account has been successfully created, and you're now ready to:</p>
                    
                    <div class="feature">
                        <strong>🏠 Create Smart Property Listings</strong>
                        <p>Use AI to generate compelling property descriptions and optimize your listings</p>
                    </div>
                    
                    <div class="feature">
                        <strong>📱 Manage Facebook Campaigns</strong>
                        <p>Connect your Facebook account and promote properties directly from our platform</p>
                    </div>
                    
                    <div class="feature">
                        <strong>📊 Track Performance</strong>
                        <p>Get insights into your listings' performance and optimize for better results</p>
                    </div>
                    
                    <div class="feature">
                        <strong>🤖 AI-Powered Suggestions</strong>
                        <p>Receive intelligent recommendations to improve your property listings</p>
                    </div>
                    
                    <p><strong>Next Steps:</strong></p>
                    <ol>
                        <li>Complete your profile setup</li>
                        <li>Connect your Facebook account</li>
                        <li>Create your first property listing</li>
                    </ol>
                    
                    <center>
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard" class="button">
                            Go to Dashboard
                        </a>
                    </center>
                    
                    <p style="margin-top: 30px;">If you have any questions or need assistance, our support team is here to help!</p>
                    
                    <p>Best regards,<br>The PropertyAI Team</p>
                </div>
                
                <div class="footer">
                    <p>© {datetime.now().year} PropertyAI. All rights reserved.</p>
                    <p>This email was sent to {agent_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to PropertyAI, {agent_name}!
        
        Your account has been successfully created, and you're now ready to:
        
        - Create Smart Property Listings using AI
        - Manage Facebook Campaigns
        - Track Performance
        - Get AI-Powered Suggestions
        
        Next Steps:
        1. Complete your profile setup
        2. Connect your Facebook account
        3. Create your first property listing
        
        Visit your dashboard: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard
        
        Best regards,
        The PropertyAI Team
        """
        
        return await self.send_email(agent_email, subject, html_content, text_content)
    
    async def send_property_created_email(
        self,
        agent_email: str,
        agent_name: str,
        property_title: str,
        property_id: str
    ) -> bool:
        """Send email when a property is created"""
        subject = "Property Created Successfully!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #10B981; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background-color: #10B981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
                .property-info {{ background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Property Created Successfully!</h1>
                </div>
                
                <div class="content">
                    <h2>Hi {agent_name},</h2>
                    
                    <p>Great news! Your property listing has been created successfully.</p>
                    
                    <div class="property-info">
                        <h3>{property_title}</h3>
                        <p>Property ID: {property_id}</p>
                    </div>
                    
                    <p><strong>What's next?</strong></p>
                    <ul>
                        <li>Add high-quality photos to your listing</li>
                        <li>Share on social media for maximum visibility</li>
                        <li>Create a Facebook campaign to reach more buyers</li>
                        <li>Monitor inquiries and respond promptly</li>
                    </ul>
                    
                    <center>
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/properties/{property_id}" class="button">
                            View Property
                        </a>
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/properties/{property_id}/promote" class="button">
                            Promote Property
                        </a>
                    </center>
                    
                    <p style="margin-top: 30px;">Good luck with your listing!</p>
                    
                    <p>Best regards,<br>The PropertyAI Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(agent_email, subject, html_content)


# Global instance
email_service = EmailService()