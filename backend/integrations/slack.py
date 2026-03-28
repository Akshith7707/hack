"""
Slack Integration
Posts messages to Slack via webhooks
"""
import os
import httpx
from typing import Dict, List
from .base import Integration


class SlackIntegration(Integration):
    """
    Slack integration for sending messages.
    Uses Slack's incoming webhooks feature.
    """
    
    name = "slack"
    description = "Send messages to Slack channels"
    icon = "💬"
    
    # Default webhook from environment (optional)
    DEFAULT_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
    
    @property
    def triggers(self) -> List[Dict]:
        # Slack triggers would need Slack's Events API - not implemented for MVP
        return []
    
    @property
    def actions(self) -> List[Dict]:
        return [
            {
                "id": "send_message",
                "name": "Send Message",
                "description": "Post a message to a Slack channel"
            }
        ]
    
    @property
    def config_schema(self) -> Dict:
        return {
            "webhook_url": {
                "type": "string",
                "description": "Slack incoming webhook URL",
                "required": False  # Can use default from env
            },
            "channel": {
                "type": "string",
                "description": "Override channel (optional)",
                "required": False
            }
        }
    
    async def trigger(self, config: Dict) -> List[Dict]:
        """Slack triggers not implemented for MVP"""
        return []
    
    async def action(self, config: Dict, data: Dict) -> Dict:
        """Send a message to Slack"""
        webhook_url = config.get("webhook_url") or self.DEFAULT_WEBHOOK_URL
        
        if not webhook_url:
            return {
                "status": "skipped",
                "reason": "No Slack webhook configured. Set SLACK_WEBHOOK_URL env var or provide webhook_url in config."
            }
        
        # Build the Slack message payload
        message = data.get("message") or data.get("text") or str(data)
        
        payload = {"text": message}
        
        # Optional: override channel
        if config.get("channel"):
            payload["channel"] = config["channel"]
        
        # Optional: add blocks for rich formatting
        if data.get("blocks"):
            payload["blocks"] = data["blocks"]
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload)
                
                if response.status_code == 200:
                    return {"status": "success", "message": "Message sent to Slack"}
                else:
                    return {
                        "status": "error",
                        "error": f"Slack returned {response.status_code}: {response.text}"
                    }
        except httpx.TimeoutException:
            return {"status": "error", "error": "Slack request timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
