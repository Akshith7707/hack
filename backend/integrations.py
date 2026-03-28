"""
FlexCode Integrations Module
Plugin-based integration system for triggers and actions
"""
import json
import os
import httpx
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod

DEMO_FILE = os.path.join(os.path.dirname(__file__), "..", "demo", "sample_emails.json")

# Track which emails have been processed
processed_emails = set()


# ============== INTEGRATION BASE CLASS ==============

class Integration(ABC):
    """Base class for all integrations (Zapier-style plugin)"""
    name: str = "base"
    description: str = ""
    
    @abstractmethod
    async def trigger(self, config: Dict) -> List[Dict]:
        """Trigger: Fetch data from external source"""
        pass
    
    @abstractmethod
    async def action(self, config: Dict, data: Dict) -> Dict:
        """Action: Send data to external destination"""
        pass


# ============== WEBHOOK INTEGRATION ==============

class WebhookIntegration(Integration):
    """Webhook trigger and HTTP action"""
    name = "webhook"
    description = "HTTP webhooks for triggers and actions"
    
    async def trigger(self, config: Dict) -> List[Dict]:
        """Receive webhook data (called by endpoint)"""
        return config.get("payload", [])
    
    async def action(self, config: Dict, data: Dict) -> Dict:
        """Send HTTP request"""
        url = config.get("url")
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=30.0
            )
            return {
                "status_code": response.status_code,
                "body": response.text[:500]
            }


# ============== MOCK EMAIL INTEGRATION ==============

class MockEmailIntegration(Integration):
    """Mock email integration for demo purposes"""
    name = "mock_email"
    description = "Demo email integration using sample data"
    
    async def trigger(self, config: Dict) -> List[Dict]:
        """Fetch mock emails"""
        emails = load_sample_emails()
        max_results = config.get("max_results", 5)
        return emails[:max_results]
    
    async def action(self, config: Dict, data: Dict) -> Dict:
        """Mock send email (just logs)"""
        return {
            "status": "sent",
            "to": config.get("to", "demo@example.com"),
            "subject": data.get("subject", "No Subject"),
            "message": "Email sent (mock)"
        }


# ============== SLACK INTEGRATION (WEBHOOK-BASED) ==============

class SlackIntegration(Integration):
    """Slack integration using webhooks"""
    name = "slack"
    description = "Send messages to Slack channels"
    
    async def trigger(self, config: Dict) -> List[Dict]:
        """Slack triggers would use Slack Events API (future)"""
        return []
    
    async def action(self, config: Dict, data: Dict) -> Dict:
        """Send message to Slack webhook"""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return {"error": "No webhook_url configured"}
        
        message = data.get("message", data.get("text", str(data)))
        channel = config.get("channel", "#general")
        
        payload = {
            "text": message,
            "channel": channel
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload, timeout=10.0)
            return {
                "status": "sent" if response.status_code == 200 else "failed",
                "status_code": response.status_code
            }


# ============== INTEGRATION REGISTRY ==============

INTEGRATIONS: Dict[str, Integration] = {
    "webhook": WebhookIntegration(),
    "mock_email": MockEmailIntegration(),
    "slack": SlackIntegration(),
}

def get_integration(name: str) -> Optional[Integration]:
    """Get integration by name"""
    return INTEGRATIONS.get(name)

def list_integrations() -> List[Dict]:
    """List all available integrations"""
    return [
        {"name": i.name, "description": i.description}
        for i in INTEGRATIONS.values()
    ]


# ============== LEGACY FUNCTIONS (for backwards compatibility) ==============

def fetch_latest_emails(max_results: int = 5) -> List[Dict]:
    """Fetch emails - uses mock data for demo"""
    emails = load_sample_emails()
    return [
        {
            "id": str(e.get("id", i)),
            "subject": e.get("subject", "No Subject"),
            "sender": e.get("sender", "unknown@example.com"),
            "snippet": e.get("body", "")[:100]
        }
        for i, e in enumerate(emails[:max_results])
    ]


def load_sample_emails() -> List[Dict]:
    """Load sample emails from JSON file"""
    try:
        with open(DEMO_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return get_default_emails()


def get_default_emails() -> List[Dict]:
    """Default emails if file not found"""
    return [
        {
            "id": 1,
            "subject": "URGENT: Production database is down",
            "sender": "ops@company.com",
            "body": "Our main production database has been unreachable for the past 15 minutes. All customer-facing services are affected. We need immediate action.",
            "urgency": "high"
        },
        {
            "id": 2,
            "subject": "Meeting follow-up: Q4 Planning",
            "sender": "sarah@company.com",
            "body": "Thanks for the great discussion today. Could you send me the slides and let me know your availability for a follow-up next week?",
            "urgency": "medium"
        },
        {
            "id": 3,
            "subject": "Quick question about the API",
            "sender": "developer@partner.com",
            "body": "Hey! I'm integrating with your API and noticed the /users endpoint returns a 404. Is this expected behavior or am I missing something?",
            "urgency": "medium"
        }
    ]


def get_next_mock_email() -> Optional[Dict]:
    """Get the next unprocessed mock email"""
    emails = load_sample_emails()
    
    for email in emails:
        if email['id'] not in processed_emails:
            processed_emails.add(email['id'])
            return email
    
    # If all processed, reset and start over
    processed_emails.clear()
    if emails:
        processed_emails.add(emails[0]['id'])
        return emails[0]
    
    return None


def reset_processed_emails():
    """Reset the processed emails tracker"""
    processed_emails.clear()


def format_email_for_input(email: Dict) -> str:
    """Format email dict as input string"""
    return f"""Subject: {email.get('subject', 'No Subject')}
From: {email.get('sender', 'unknown')}

{email.get('body', email.get('snippet', ''))}"""
