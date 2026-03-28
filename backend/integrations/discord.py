"""
Discord Integration
Sends messages via webhooks or bot token
"""
import os
import httpx
from typing import Dict, List
from .base import Integration


class DiscordIntegration(Integration):
    """
    Discord integration supporting:
    - Webhook messages (simple, no auth needed)
    - Bot messages (requires bot token)
    """

    name = "discord"
    description = "Send messages to Discord channels"
    icon = "D"

    API_BASE = "https://discord.com/api/v10"

    # Default values from environment
    DEFAULT_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
    DEFAULT_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

    @property
    def triggers(self) -> List[Dict]:
        return []

    @property
    def actions(self) -> List[Dict]:
        return [
            {
                "id": "send_webhook",
                "name": "Send Webhook Message",
                "description": "Post a message via Discord webhook"
            },
            {
                "id": "send_embed",
                "name": "Send Rich Embed",
                "description": "Post a rich embed message via webhook"
            },
            {
                "id": "send_bot_message",
                "name": "Send Bot Message",
                "description": "Post a message as a bot to a channel"
            }
        ]

    @property
    def config_schema(self) -> Dict:
        return {
            "webhook_url": {
                "type": "string",
                "description": "Discord webhook URL",
                "required": False
            },
            "bot_token": {
                "type": "string",
                "description": "Discord bot token",
                "required": False
            },
            "channel_id": {
                "type": "string",
                "description": "Channel ID (for bot messages)",
                "required": False
            }
        }

    async def trigger(self, config: Dict) -> List[Dict]:
        """Discord triggers not implemented for MVP"""
        return []

    async def action(self, config: Dict, data: Dict) -> Dict:
        """Send a message to Discord"""
        action_type = config.get("action_type", "send_webhook")

        try:
            if action_type == "send_webhook":
                return await self._send_webhook(config, data)
            elif action_type == "send_embed":
                return await self._send_embed(config, data)
            elif action_type == "send_bot_message":
                return await self._send_bot_message(config, data)
            else:
                return {"status": "error", "error": f"Unknown action: {action_type}"}
        except httpx.TimeoutException:
            return {"status": "error", "error": "Discord request timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _send_webhook(self, config: Dict, data: Dict) -> Dict:
        """Send message via webhook"""
        webhook_url = config.get("webhook_url") or self.DEFAULT_WEBHOOK_URL

        if not webhook_url:
            return {
                "status": "skipped",
                "reason": "No Discord webhook configured. Set DISCORD_WEBHOOK_URL env var."
            }

        message = data.get("message") or data.get("text") or data.get("content") or str(data)

        payload = {"content": message}

        if data.get("username"):
            payload["username"] = data["username"]

        if data.get("avatar_url"):
            payload["avatar_url"] = data["avatar_url"]

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)

            if response.status_code in (200, 204):
                return {"status": "success", "message": "Message sent to Discord"}
            else:
                return {"status": "error", "error": f"Discord returned {response.status_code}"}

    async def _send_embed(self, config: Dict, data: Dict) -> Dict:
        """Send rich embed via webhook"""
        webhook_url = config.get("webhook_url") or self.DEFAULT_WEBHOOK_URL

        if not webhook_url:
            return {"status": "skipped", "reason": "No webhook configured"}

        embed = {
            "title": data.get("title", "FlexCode Notification"),
            "description": data.get("description") or data.get("message", ""),
            "color": data.get("color", 0x818cf8),
        }

        if data.get("fields"):
            embed["fields"] = data["fields"]

        if data.get("footer"):
            embed["footer"] = {"text": data["footer"]}

        if data.get("thumbnail"):
            embed["thumbnail"] = {"url": data["thumbnail"]}

        if data.get("image"):
            embed["image"] = {"url": data["image"]}

        payload = {"embeds": [embed]}

        if data.get("content"):
            payload["content"] = data["content"]

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)

            if response.status_code in (200, 204):
                return {"status": "success", "message": "Embed sent to Discord"}
            else:
                return {"status": "error", "error": f"Discord returned {response.status_code}"}

    async def _send_bot_message(self, config: Dict, data: Dict) -> Dict:
        """Send message as a bot"""
        bot_token = config.get("bot_token") or self.DEFAULT_BOT_TOKEN
        channel_id = config.get("channel_id") or data.get("channel_id")

        if not bot_token:
            return {"status": "skipped", "reason": "No bot token configured"}
        if not channel_id:
            return {"status": "error", "error": "channel_id required for bot messages"}

        message = data.get("message") or data.get("content") or str(data)

        headers = {
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json"
        }

        payload = {"content": message}

        if data.get("embeds"):
            payload["embeds"] = data["embeds"]

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.API_BASE}/channels/{channel_id}/messages",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                return {"status": "success", "message_id": response.json().get("id")}
            else:
                return {"status": "error", "error": f"Discord API error: {response.text[:500]}"}
