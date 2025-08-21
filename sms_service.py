"""
SMS Service for PropertyAI Real Estate CRM
Supports multiple SMS providers for verification codes
"""

import os
import random
import string
import time
from typing import Optional, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

class SMSService:
    """SMS Service supporting multiple providers"""
    
    def __init__(self):
        self.provider = os.getenv('SMS_PROVIDER', 'textlocal')  # textlocal, twilio, fast2sms
        self.api_key = os.getenv('SMS_API_KEY')
        self.sender_id = os.getenv('SMS_SENDER_ID', 'PropertyAI')
        
        # In-memory storage for verification codes (use Redis in production)
        self.verification_codes = {}
    
    def generate_verification_code(self, length: int = 6) -> str:
        """Generate a random verification code"""
        return ''.join(random.choices(string.digits, k=length))
    
    async def send_verification_code(self, phone_number: str, user_id: str = None) -> Dict[str, Any]:
        """Send verification code to phone number"""
        try:
            # Clean phone number (remove +91, spaces, etc.)
            clean_phone = self._clean_phone_number(phone_number)
            
            # Generate verification code
            code = self.generate_verification_code()
            
            # Store code with expiration (5 minutes)
            key = f"{clean_phone}_{user_id}" if user_id else clean_phone
            self.verification_codes[key] = {
                'code': code,
                'timestamp': time.time(),
                'attempts': 0
            }
            
            # Send SMS based on provider
            if self.provider == 'textlocal':
                result = await self._send_textlocal(clean_phone, code)
            elif self.provider == 'twilio':
                result = await self._send_twilio(clean_phone, code)
            elif self.provider == 'fast2sms':
                result = await self._send_fast2sms(clean_phone, code)
            else:
                # Demo mode - just log the code
                result = await self._send_demo(clean_phone, code)
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Verification code sent successfully',
                    'phone': clean_phone,
                    'expires_in': 300  # 5 minutes
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to send SMS')
                }
                
        except Exception as e:
            logger.error(f"Error sending verification code: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def verify_code(self, phone_number: str, code: str, user_id: str = None) -> Dict[str, Any]:
        """Verify the SMS code"""
        try:
            clean_phone = self._clean_phone_number(phone_number)
            key = f"{clean_phone}_{user_id}" if user_id else clean_phone
            
            stored_data = self.verification_codes.get(key)
            if not stored_data:
                return {
                    'success': False,
                    'error': 'No verification code found for this number'
                }
            
            # Check expiration (5 minutes)
            if time.time() - stored_data['timestamp'] > 300:
                del self.verification_codes[key]
                return {
                    'success': False,
                    'error': 'Verification code has expired'
                }
            
            # Check attempts (max 3)
            if stored_data['attempts'] >= 3:
                del self.verification_codes[key]
                return {
                    'success': False,
                    'error': 'Too many failed attempts'
                }
            
            # Verify code
            if stored_data['code'] == code:
                del self.verification_codes[key]
                return {
                    'success': True,
                    'message': 'Phone number verified successfully'
                }
            else:
                self.verification_codes[key]['attempts'] += 1
                return {
                    'success': False,
                    'error': 'Invalid verification code'
                }
                
        except Exception as e:
            logger.error(f"Error verifying code: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number"""
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        # Handle Indian phone numbers
        if digits.startswith('91') and len(digits) == 12:
            return digits[2:]  # Remove country code
        elif len(digits) == 10:
            return digits
        else:
            raise ValueError("Invalid phone number format")
    
    async def _send_textlocal(self, phone: str, code: str) -> Dict[str, Any]:
        """Send SMS via TextLocal (Indian SMS provider)"""
        try:
            url = "https://api.textlocal.in/send/"
            message = f"Your PropertyAI verification code is: {code}. Valid for 5 minutes. Do not share this code."
            
            data = {
                'apikey': self.api_key,
                'numbers': f"91{phone}",  # Add country code
                'message': message,
                'sender': self.sender_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data)
                result = response.json()
                
                if result.get('status') == 'success':
                    return {'success': True, 'message_id': result.get('message_id')}
                else:
                    return {'success': False, 'error': result.get('errors', 'Unknown error')}
                    
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _send_twilio(self, phone: str, code: str) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            from_number = os.getenv('TWILIO_PHONE_NUMBER')
            
            client = Client(account_sid, auth_token)
            message = f"Your PropertyAI verification code is: {code}. Valid for 5 minutes."
            
            result = client.messages.create(
                body=message,
                from_=from_number,
                to=f"+91{phone}"
            )
            
            return {'success': True, 'message_id': result.sid}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _send_fast2sms(self, phone: str, code: str) -> Dict[str, Any]:
        """Send SMS via Fast2SMS (Indian provider)"""
        try:
            url = "https://www.fast2sms.com/dev/bulkV2"
            message = f"Your PropertyAI verification code is: {code}. Valid for 5 minutes."
            
            headers = {
                'authorization': self.api_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                'route': 'v3',
                'sender_id': self.sender_id,
                'message': message,
                'language': 'english',
                'flash': 0,
                'numbers': phone
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers)
                result = response.json()
                
                if result.get('return'):
                    return {'success': True, 'message_id': result.get('message_id')}
                else:
                    return {'success': False, 'error': result.get('message', 'Unknown error')}
                    
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _send_demo(self, phone: str, code: str) -> Dict[str, Any]:
        """Demo mode - just log the code (for development)"""
        print(f"📱 SMS Demo Mode")
        print(f"📞 Phone: +91{phone}")
        print(f"🔢 Verification Code: {code}")
        print(f"⏰ Valid for 5 minutes")
        
        return {
            'success': True, 
            'message_id': f"demo_{phone}_{code}",
            'demo_mode': True
        }

# Global SMS service instance
sms_service = SMSService()

# FastAPI endpoints
async def send_verification_code_endpoint(phone_number: str, user_id: str = None):
    """FastAPI endpoint to send verification code"""
    return await sms_service.send_verification_code(phone_number, user_id)

async def verify_code_endpoint(phone_number: str, code: str, user_id: str = None):
    """FastAPI endpoint to verify code"""
    return await sms_service.verify_code(phone_number, code, user_id)
