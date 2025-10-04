"""Tool Router — Tool discovery and routing."""

import logging
import importlib
from typing import Dict, Any, List, Type, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ToolRouter:
    """Routes parsed queries to appropriate tool implementations."""
    
    def __init__(self, config_path: str = "config"):
        """Initialize router and discover available tools."""
        self.config_path = Path(config_path)
        self.tools_registry = {}
        self._discover_tools()
        
        logger.info(f"ToolRouter initialized with {len(self.tools_registry)} tools")
    
    def _discover_tools(self):
        """Dynamically discover and load tools from tools/ directory."""
        tools_dir = Path("tools")
        
        if not tools_dir.exists():
            logger.warning("Tools directory not found, creating with basic tools")
            tools_dir.mkdir(exist_ok=True)
            return
        
        # Import all Python files in tools/ directory
        for tool_file in tools_dir.glob("*.py"):
            if tool_file.name.startswith("__"):
                continue
                
            try:
                module_name = f"tools.{tool_file.stem}"
                module = importlib.import_module(module_name)
                
                # Look for tool classes (convention: classes ending in 'Tool' or 'Fetcher')
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        hasattr(attr, 'tool_name') and 
                        hasattr(attr, 'execute')):
                        
                        tool_instance = attr()
                        self.tools_registry[tool_instance.tool_name] = tool_instance
                        logger.debug(f"Registered tool: {tool_instance.tool_name}")
                        
            except Exception as e:
                logger.error(f"Failed to load tool from {tool_file}: {e}")
    
    def route(self, parsed_params: Dict[str, Any]) -> Any:
        """
        Route a parsed query to the appropriate tool.
        
        Args:
            parsed_params: Parameters from query parser including tool name
            
        Returns:
            Tool instance ready for execution
            
        Raises:
            ValueError: If requested tool is not available
        """
        tool_name = parsed_params.get("tool", "get_events")
        
        if tool_name not in self.tools_registry:
            available_tools = list(self.tools_registry.keys())
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {available_tools}")
        
        tool_instance = self.tools_registry[tool_name]
        logger.debug(f"Routed to tool: {tool_name}")
        
        return tool_instance
    
    def list_tools(self) -> Dict[str, Any]:
        """
        List all available tools and their capabilities.
        
        Returns:
            Dictionary with tool information and metadata
        """
        tools_info = {}
        
        for tool_name, tool_instance in self.tools_registry.items():
            tools_info[tool_name] = {
                "name": tool_name,
                "description": getattr(tool_instance, 'description', 'No description available'),
                "parameters": getattr(tool_instance, 'parameters', []),
                "examples": getattr(tool_instance, 'examples', [])
            }
        
        return {
            "available_tools": tools_info,
            "count": len(self.tools_registry)
        }
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get a specific tool instance by name."""
        return self.tools_registry.get(tool_name)
    
    def register_tool(self, tool_instance: Any) -> bool:
        """
        Manually register a tool instance.
        
        Args:
            tool_instance: Tool object with tool_name and execute methods
            
        Returns:
            True if registration successful, False otherwise
        """
        if not hasattr(tool_instance, 'tool_name') or not hasattr(tool_instance, 'execute'):
            logger.error("Tool must have 'tool_name' and 'execute' attributes")
            return False
        
        self.tools_registry[tool_instance.tool_name] = tool_instance
        logger.info(f"Manually registered tool: {tool_instance.tool_name}")
        return True
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Remove a tool from the registry."""
        if tool_name in self.tools_registry:
            del self.tools_registry[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
            return True
        return False