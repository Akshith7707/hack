"""
FlexCode Integrations Registry
Central registry for all available integrations
"""
from typing import Dict, Optional, List
from .base import Integration
from .webhook import WebhookIntegration
from .slack import SlackIntegration
from .http import HTTPIntegration
from .notion import NotionIntegration
from .discord import DiscordIntegration
from .stripe import StripeIntegration


# Registry of all available integrations
INTEGRATIONS: Dict[str, Integration] = {
    "webhook": WebhookIntegration(),
    "slack": SlackIntegration(),
    "http": HTTPIntegration(),
    "notion": NotionIntegration(),
    "discord": DiscordIntegration(),
    "stripe": StripeIntegration(),
}


def get_integration(name: str) -> Optional[Integration]:
    """Get an integration by name"""
    return INTEGRATIONS.get(name.lower())


def list_integrations() -> List[Dict]:
    """List all available integrations with their metadata"""
    return [integration.to_dict() for integration in INTEGRATIONS.values()]


def register_integration(integration: Integration):
    """Register a new integration (for plugins)"""
    INTEGRATIONS[integration.name.lower()] = integration


# Mock email integration for demo purposes
class MockEmailIntegration(Integration):
    """Mock email integration for demo/testing"""
    
    name = "mock_email"
    description = "Mock email source for testing"
    icon = "📧"
    
    MOCK_EMAILS = [
        {
            "id": "1",
            "subject": "URGENT: Server Down",
            "snippet": "Production server is not responding. Please check immediately.",
            "from": "ops@company.com",
            "urgency": "high"
        },
        {
            "id": "2", 
            "subject": "Meeting Tomorrow",
            "snippet": "Let's sync up tomorrow at 3pm to discuss the roadmap.",
            "from": "manager@company.com",
            "urgency": "medium"
        },
        {
            "id": "3",
            "subject": "Newsletter: Weekly Updates",
            "snippet": "Here's what happened this week in the company...",
            "from": "newsletter@company.com",
            "urgency": "low"
        },
        {
            "id": "4",
            "subject": "Customer Complaint",
            "snippet": "I've been waiting 3 days for support and no one has responded!",
            "from": "angry.customer@gmail.com",
            "urgency": "high"
        },
        {
            "id": "5",
            "subject": "Payment Failed",
            "snippet": "Your subscription payment failed. Please update your card.",
            "from": "billing@saas.com",
            "urgency": "high"
        }
    ]
    
    _index = 0
    
    @property
    def triggers(self) -> List[Dict]:
        return [
            {
                "id": "new_email",
                "name": "New Email",
                "description": "Triggered when a new mock email arrives"
            }
        ]
    
    @property
    def actions(self) -> List[Dict]:
        return [
            {
                "id": "send_reply",
                "name": "Send Reply",
                "description": "Send a mock email reply (logged only)"
            }
        ]
    
    async def trigger(self, config: Dict) -> List[Dict]:
        """Return the next mock email"""
        if self._index >= len(self.MOCK_EMAILS):
            self._index = 0  # Loop back
        
        email = self.MOCK_EMAILS[self._index]
        self._index += 1
        return [email]
    
    async def action(self, config: Dict, data: Dict) -> Dict:
        """Mock sending an email (just log it)"""
        return {
            "status": "success",
            "message": f"Mock email reply sent: {data.get('subject', 'No subject')}"
        }
    
    def get_next(self) -> Optional[Dict]:
        """Get the next mock email synchronously"""
        if self._index >= len(self.MOCK_EMAILS):
            self._index = 0
        
        email = self.MOCK_EMAILS[self._index]
        self._index += 1
        return email
    
    def reset(self):
        """Reset to the first email"""
        self._index = 0


# Register mock email
mock_email_integration = MockEmailIntegration()
INTEGRATIONS["mock_email"] = mock_email_integration


# Helper functions for backwards compatibility
def get_next_mock_email() -> Optional[Dict]:
    """Get the next mock email"""
    return mock_email_integration.get_next()


def reset_mock_emails():
    """Reset mock email index"""
    mock_email_integration.reset()


def format_email_for_input(email: Dict) -> str:
    """Format email as input text for workflow"""
    return f"""Subject: {email.get('subject', 'No Subject')}
From: {email.get('from', 'Unknown')}

{email.get('snippet', email.get('body', ''))}"""
