"""
SMS Handler for EngageSpark Integration
Handles incoming and outgoing SMS messages for farmers
"""
import os
import requests
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EngageSparkSMS:
    """
    EngageSpark SMS Integration for Filipino Farmers
    
    Supports:
    - Inbound SMS: Farmers send queries via SMS
    - Outbound SMS: Send price information back
    - Philippine mobile numbers
    """
    
    def __init__(self):
        """Initialize EngageSpark SMS client"""
        self.api_key = os.getenv("ENGAGESPARK_API_KEY")
        self.organization_id = os.getenv("ENGAGESPARK_ORG_ID")
        self.sender_id = os.getenv("ENGAGESPARK_SENDER_ID", "DA Price")
        
        # EngageSpark API endpoints
        self.base_url = "https://start.engagespark.com/api/v1"
        self.send_url = f"{self.base_url}/organizations/{self.organization_id}/send-sms"
        
        if self.api_key and self.organization_id:
            logger.info("✅ EngageSpark SMS Handler initialized")
        else:
            logger.warning("⚠️ EngageSpark credentials not found. SMS features disabled.")
    
    def send_sms(self, to: str, message: str) -> Dict[str, Any]:
        """
        Send SMS via EngageSpark
        
        Args:
            to: Recipient phone number (e.g., '09171234567' or '+639171234567')
            message: SMS message content (max 160 characters recommended)
            
        Returns:
            Dictionary with status and message_id
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "EngageSpark not configured"
            }
        
        try:
            # Format phone number
            phone = self._format_phone_number(to)
            
            # Prepare payload
            payload = {
                "recipients": [phone],
                "message": message,
                "sender_id": self.sender_id
            }
            
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Send SMS
            response = requests.post(
                self.send_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"✅ SMS sent to {phone}: {message[:50]}...")
            return {
                "success": True,
                "message_id": data.get("id"),
                "status": "sent",
                "recipient": phone
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to send SMS to {to}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error sending SMS: {str(e)}")
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
        Process incoming SMS from EngageSpark webhook
        
        EngageSpark sends webhook with:
        {
            "id": "message_id",
            "from": "+639171234567",
            "to": "your_number",
            "message": "Magkano kamatis",
            "timestamp": "2025-12-06T10:30:00Z"
        }
        
        Args:
            webhook_data: Webhook payload from EngageSpark
            
        Returns:
            Processed data
        """
        try:
            sender = webhook_data.get("from", webhook_data.get("sender"))
            message = webhook_data.get("message", webhook_data.get("text", ""))
            message_id = webhook_data.get("id")
            
            logger.info(f"📱 Incoming SMS from {sender}: {message}")
            
            return {
                "success": True,
                "sender": sender,
                "message": message,
                "message_id": message_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing webhook: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def truncate_for_sms(self, text: str, max_length: int = 160) -> str:
        """
        Truncate response to fit SMS limit
        
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


# Global SMS handler instance
sms_handler = EngageSparkSMS()
