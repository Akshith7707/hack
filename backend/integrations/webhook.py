"""
Webhook Integration
Sends and receives HTTP POST requests
"""
import httpx
from typing import Dict, List
from .base import Integration


class WebhookIntegration(Integration):
    """
    Webhook integration for sending/receiving HTTP requests.
    - Trigger: Receives webhook POST (handled by API endpoint)
    - Action: Sends HTTP POST to a URL
    """
    
    name = "webhook"
    description = "Send and receive HTTP webhooks"
    icon = "🌐"
    
    @property
    def triggers(self) -> List[Dict]:
        return [
            {
                "id": "webhook_received",
                "name": "Webhook Received",
                "description": "Triggered when an HTTP POST is received"
            }
        ]
    
    @property
    def actions(self) -> List[Dict]:
        return [
            {
                "id": "send_webhook",
                "name": "Send Webhook",
                "description": "Send an HTTP POST to a URL"
            }
        ]
    
    @property
    def config_schema(self) -> Dict:
        return {
            "url": {
                "type": "string",
                "description": "The URL to send the webhook to",
                "required": True
            },
            "headers": {
                "type": "object",
                "description": "Optional headers to include",
                "required": False
            }
        }
    
    async def trigger(self, config: Dict) -> List[Dict]:
        """Webhook triggers are handled by the API endpoint, not polling"""
        return []
    
    async def action(self, config: Dict, data: Dict) -> Dict:
        """Send HTTP POST to the configured URL"""
        url = config.get("url")
        if not url:
            return {"status": "error", "error": "No URL configured"}
        
        headers = config.get("headers", {})
        headers.setdefault("Content-Type", "application/json")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=data, headers=headers)
                return {
                    "status": "success",
                    "status_code": response.status_code,
                    "response": response.text[:500]  # Truncate long responses
                }
        except httpx.TimeoutException:
            return {"status": "error", "error": "Request timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
