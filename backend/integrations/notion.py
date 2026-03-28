"""
Notion Integration
Creates pages and databases, queries content
"""
import os
import httpx
from typing import Dict, List
from .base import Integration


class NotionIntegration(Integration):
    """
    Notion integration using Internal Integration Token.
    Requires NOTION_API_KEY environment variable.
    """

    name = "notion"
    description = "Create and query Notion pages and databases"
    icon = "N"

    API_BASE = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    # Default API key from environment
    DEFAULT_API_KEY = os.environ.get("NOTION_API_KEY")

    def _get_headers(self, api_key: str = None) -> Dict:
        key = api_key or self.DEFAULT_API_KEY
        return {
            "Authorization": f"Bearer {key}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json"
        }

    @property
    def triggers(self) -> List[Dict]:
        return [
            {
                "id": "database_query",
                "name": "Query Database",
                "description": "Poll a Notion database for new items"
            }
        ]

    @property
    def actions(self) -> List[Dict]:
        return [
            {
                "id": "create_page",
                "name": "Create Page",
                "description": "Create a new page in a database"
            },
            {
                "id": "append_block",
                "name": "Append Content",
                "description": "Add content to an existing page"
            },
            {
                "id": "update_page",
                "name": "Update Page Properties",
                "description": "Update properties of an existing page"
            }
        ]

    @property
    def config_schema(self) -> Dict:
        return {
            "api_key": {
                "type": "string",
                "description": "Notion Internal Integration Token",
                "required": False
            },
            "database_id": {
                "type": "string",
                "description": "Target database ID",
                "required": True
            }
        }

    async def trigger(self, config: Dict) -> List[Dict]:
        """Query a Notion database for items"""
        database_id = config.get("database_id")
        if not database_id:
            return []

        api_key = config.get("api_key") or self.DEFAULT_API_KEY
        if not api_key:
            return [{"error": "No Notion API key configured"}]

        headers = self._get_headers(api_key)

        body = {}
        if config.get("filter"):
            body["filter"] = config["filter"]
        if config.get("sorts"):
            body["sorts"] = config["sorts"]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.API_BASE}/databases/{database_id}/query",
                    headers=headers,
                    json=body
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
                else:
                    return [{"error": f"Notion API error: {response.status_code}"}]
        except httpx.TimeoutException:
            return [{"error": "Notion request timed out"}]
        except Exception as e:
            return [{"error": str(e)}]

    async def action(self, config: Dict, data: Dict) -> Dict:
        """Execute a Notion action"""
        action_type = config.get("action_type", "create_page")
        api_key = config.get("api_key") or self.DEFAULT_API_KEY

        if not api_key:
            return {
                "status": "skipped",
                "reason": "No Notion API key configured. Set NOTION_API_KEY env var."
            }

        headers = self._get_headers(api_key)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if action_type == "create_page":
                    return await self._create_page(client, headers, config, data)
                elif action_type == "append_block":
                    return await self._append_block(client, headers, config, data)
                elif action_type == "update_page":
                    return await self._update_page(client, headers, config, data)
                else:
                    return {"status": "error", "error": f"Unknown action: {action_type}"}
        except httpx.TimeoutException:
            return {"status": "error", "error": "Notion request timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _create_page(self, client, headers, config, data) -> Dict:
        """Create a new page in a database"""
        database_id = config.get("database_id")

        if not database_id:
            return {"status": "error", "error": "database_id required"}

        payload = {
            "parent": {"database_id": database_id},
            "properties": self._build_properties(data, config.get("property_mapping", {}))
        }

        if data.get("content"):
            payload["children"] = self._text_to_blocks(data["content"])

        response = await client.post(
            f"{self.API_BASE}/pages",
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            return {"status": "success", "page_id": response.json().get("id")}
        else:
            return {"status": "error", "error": response.text[:500]}

    async def _append_block(self, client, headers, config, data) -> Dict:
        """Append blocks to an existing page"""
        page_id = config.get("page_id") or data.get("page_id")

        if not page_id:
            return {"status": "error", "error": "page_id required"}

        content = data.get("content") or data.get("text") or str(data)
        blocks = self._text_to_blocks(content)

        response = await client.patch(
            f"{self.API_BASE}/blocks/{page_id}/children",
            headers=headers,
            json={"children": blocks}
        )

        if response.status_code == 200:
            return {"status": "success", "message": "Content appended"}
        else:
            return {"status": "error", "error": response.text[:500]}

    async def _update_page(self, client, headers, config, data) -> Dict:
        """Update page properties"""
        page_id = config.get("page_id") or data.get("page_id")

        if not page_id:
            return {"status": "error", "error": "page_id required"}

        properties = self._build_properties(data, config.get("property_mapping", {}))

        response = await client.patch(
            f"{self.API_BASE}/pages/{page_id}",
            headers=headers,
            json={"properties": properties}
        )

        if response.status_code == 200:
            return {"status": "success", "message": "Page updated"}
        else:
            return {"status": "error", "error": response.text[:500]}

    def _build_properties(self, data: Dict, mapping: Dict) -> Dict:
        """Convert data to Notion property format"""
        properties = {}

        if "title" in data:
            properties["Name"] = {
                "title": [{"text": {"content": str(data["title"])}}]
            }

        for source_field, notion_config in mapping.items():
            if source_field in data:
                prop_type = notion_config.get("type", "rich_text")
                prop_name = notion_config.get("name", source_field)
                value = data[source_field]

                if prop_type == "rich_text":
                    properties[prop_name] = {
                        "rich_text": [{"text": {"content": str(value)}}]
                    }
                elif prop_type == "select":
                    properties[prop_name] = {"select": {"name": str(value)}}
                elif prop_type == "number":
                    properties[prop_name] = {"number": float(value)}
                elif prop_type == "checkbox":
                    properties[prop_name] = {"checkbox": bool(value)}

        return properties

    def _text_to_blocks(self, text: str) -> List[Dict]:
        """Convert plain text to Notion blocks"""
        paragraphs = text.split("\n\n")
        return [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": p}}]
                }
            }
            for p in paragraphs if p.strip()
        ]
