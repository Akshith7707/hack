"""
HTTP Integration
Generic HTTP client for calling any API
"""
import httpx
from typing import Dict, List
from .base import Integration


class HTTPIntegration(Integration):
    """
    Generic HTTP integration for calling any REST API.
    Supports GET, POST, PUT, DELETE methods.
    """
    
    name = "http"
    description = "Make HTTP requests to any API"
    icon = "🔗"
    
    @property
    def triggers(self) -> List[Dict]:
        return [
            {
                "id": "poll_endpoint",
                "name": "Poll Endpoint",
                "description": "Periodically check an API endpoint for new data"
            }
        ]
    
    @property
    def actions(self) -> List[Dict]:
        return [
            {
                "id": "http_get",
                "name": "HTTP GET",
                "description": "Make a GET request"
            },
            {
                "id": "http_post",
                "name": "HTTP POST",
                "description": "Make a POST request with JSON body"
            },
            {
                "id": "http_put",
                "name": "HTTP PUT",
                "description": "Make a PUT request"
            },
            {
                "id": "http_delete",
                "name": "HTTP DELETE",
                "description": "Make a DELETE request"
            }
        ]
    
    @property
    def config_schema(self) -> Dict:
        return {
            "url": {
                "type": "string",
                "description": "The URL to call",
                "required": True
            },
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "DELETE"],
                "description": "HTTP method",
                "default": "GET"
            },
            "headers": {
                "type": "object",
                "description": "HTTP headers to include",
                "required": False
            },
            "auth": {
                "type": "object",
                "description": "Authentication config (bearer token, basic auth)",
                "required": False
            }
        }
    
    async def trigger(self, config: Dict) -> List[Dict]:
        """Poll an endpoint for new data"""
        url = config.get("url")
        if not url:
            return []
        
        headers = config.get("headers", {})
        
        # Add auth header if configured
        if config.get("auth", {}).get("bearer_token"):
            headers["Authorization"] = f"Bearer {config['auth']['bearer_token']}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    # Return as list of items if it's a list, otherwise wrap in list
                    if isinstance(data, list):
                        return data
                    return [data]
                return []
        except Exception:
            return []
    
    async def action(self, config: Dict, data: Dict) -> Dict:
        """Make an HTTP request"""
        url = config.get("url")
        if not url:
            return {"status": "error", "error": "No URL configured"}
        
        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})
        headers.setdefault("Content-Type", "application/json")
        
        # Add auth header if configured
        if config.get("auth", {}).get("bearer_token"):
            headers["Authorization"] = f"Bearer {config['auth']['bearer_token']}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=data)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    return {"status": "error", "error": f"Unsupported method: {method}"}
                
                return {
                    "status": "success",
                    "status_code": response.status_code,
                    "response": response.text[:1000]  # Truncate long responses
                }
        except httpx.TimeoutException:
            return {"status": "error", "error": "Request timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
