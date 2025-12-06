"""
Twilio SMS Handler - Virtual SMS Testing
Easy-to-use SMS integration with Twilio's free trial for testing
"""
import os
from twilio.rest import Client
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TwilioSMS:
    """
    Twilio SMS Integration for Virtual SMS Testing
    
    Features:
    - Free trial with $15 credit
    - Virtual phone numbers
    - Web-based testing console
    - Real SMS to Philippine numbers
    """
    
    def __init__(self):
        """Initialize Twilio client"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("✅ Twilio SMS Handler initialized")
                logger.info(f"📱 Sending from: {self.from_number}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Twilio: {str(e)}")
                self.client = None
        else:
            logger.warning("⚠️ Twilio credentials not found. SMS features disabled.")
            self.client = None
    
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send SMS via Twilio
        
        Args:
            to: Recipient phone number (e.g., '+639171234567')
            message: SMS message content
            
        Returns:
            Dictionary with status and message_id
        """
        if not self.client:
            return {
                "success": False,
                "error": "Twilio not configured. Check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env"
            }
        
        if not self.from_number:
            return {
                "success": False,
                "error": "TWILIO_PHONE_NUMBER not set in .env"
            }
        
        try:
            # Format phone number
            phone = self._format_phone_number(to)
            
            # Send SMS using Twilio
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone
            )
            
            logger.info(f"✅ SMS sent to {phone}: {message[:50]}...")
            return {
                "success": True,
                "message_id": twilio_message.sid,
                "status": twilio_message.status,
                "recipient": phone,
                "from": self.from_number,
                "price": twilio_message.price,
                "direction": "outbound"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to send SMS to {to}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_phone_number(self, phone: str) -> str:
        """
        Format Philippine phone number to E.164 format
        
        Args:
            phone: Phone number (e.g., '09171234567' or '639171234567')
            
        Returns:
            Formatted phone number (e.g., '+639171234567')
        """
        # Remove spaces, dashes, parentheses
        phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Handle different formats
        if phone.startswith("+63"):
            return phone
        elif phone.startswith("63"):
            return f"+{phone}"
        elif phone.startswith("0"):
            return f"+63{phone[1:]}"
        else:
            # Assume it's missing country code
            return f"+63{phone}"
    
    def handle_inbound_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """
        Process incoming SMS from Twilio webhook
        
        Twilio sends webhook with these parameters:
        - MessageSid: Unique message ID
        - From: Sender's phone number
        - To: Your Twilio number
        - Body: Message text
        - FromCountry, FromCity, FromState, FromZip (optional)
        
        Args:
            webhook_data: Webhook payload from Twilio (form data)
            
        Returns:
            Processed data
        """
        try:
            sender = webhook_data.get("From", "")
            message = webhook_data.get("Body", "")
            message_id = webhook_data.get("MessageSid", "")
            to_number = webhook_data.get("To", "")
            
            logger.info(f"📱 Incoming SMS from {sender}: {message}")
            
            return {
                "success": True,
                "sender": sender,
                "message": message,
                "message_id": message_id,
                "to": to_number,
                "timestamp": datetime.now().isoformat(),
                "source": "twilio"
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing Twilio webhook: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def truncate_for_sms(self, text: str, max_length: int = 160) -> str:
        """
        Truncate response to fit SMS limit
        
        Twilio supports up to 1600 chars (concatenated SMS),
        but single SMS is 160 chars for best compatibility
        
        Args:
            text: Full response text
            max_length: Maximum SMS length (default 160)
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        # Try to truncate at sentence boundary
        truncated = text[:max_length - 3]
        
        # Find last period or comma
        last_period = truncated.rfind(".")
        last_comma = truncated.rfind(",")
        
        if last_period > max_length // 2:
            return truncated[:last_period + 1]
        elif last_comma > max_length // 2:
            return truncated[:last_comma] + "..."
        else:
            return truncated + "..."
    
    def get_account_balance(self) -> Dict[str, Any]:
        """
        Check Twilio account balance
        
        Returns:
            Balance information
        """
        if not self.client:
            return {
                "success": False,
                "error": "Twilio not configured"
            }
        
        try:
            balance = self.client.balance.fetch()
            return {
                "success": True,
                "balance": balance.balance,
                "currency": balance.currency
            }
        except Exception as e:
            logger.error(f"❌ Failed to fetch balance: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Global Twilio SMS handler instance
twilio_sms = TwilioSMS()
