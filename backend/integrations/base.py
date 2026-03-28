"""
FlowForge Integration Base Class
Abstract base for all integrations (like Zapier's "apps")
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class Integration(ABC):
    """
    Base class for all integrations.
    Each integration can provide triggers (input sources) and actions (output destinations).
    """
    
    name: str = "base"
    description: str = "Base integration"
    icon: str = "🔌"
    
    @property
    def triggers(self) -> List[Dict]:
        """List of available triggers this integration provides"""
        return []
    
    @property
    def actions(self) -> List[Dict]:
        """List of available actions this integration provides"""
        return []
    
    @property
    def config_schema(self) -> Dict:
        """JSON Schema for this integration's configuration"""
        return {}
    
    @abstractmethod
    async def trigger(self, config: Dict) -> List[Dict]:
        """
        Pull data from the integration (for polling triggers).
        Returns a list of trigger events/data items.
        """
        pass
    
    @abstractmethod
    async def action(self, config: Dict, data: Dict) -> Dict:
        """
        Push data to the integration (send a message, create a record, etc.).
        Returns the result of the action.
        """
        pass
    
    def validate_config(self, config: Dict) -> bool:
        """Validate configuration against schema"""
        # Simple validation - can be extended
        return True
    
    def to_dict(self) -> Dict:
        """Serialize integration metadata"""
        return {
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "triggers": self.triggers,
            "actions": self.actions,
            "config_schema": self.config_schema
        }
