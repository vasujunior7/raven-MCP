"""Enhanced MCP Router with Combined Reasoning Support."""

import logging
from typing import Dict, Any, List, Optional
from core.router import ToolRouter

logger = logging.getLogger(__name__)

class EnhancedMCPRouter(ToolRouter):
    """
    Enhanced router that supports combined reasoning by automatically
    orchestrating multiple tools for complex queries.
    """
    
    def __init__(self, config_path: str = "config"):
        """Initialize enhanced router with combined reasoning support."""
        super().__init__(config_path)
        
        # Auto-setup combined reasoning if tools are available
        self._setup_combined_reasoning()
        
        logger.info("EnhancedMCPRouter initialized with combined reasoning support")
    
    def _setup_combined_reasoning(self):
        """Setup combined reasoning tool with tool dependencies."""
        try:
            # Get required tools
            polymarket_tool = self.get_tool("get_events")
            lunarcrush_tool = self.get_tool("get_coins_list")
            
            if polymarket_tool and lunarcrush_tool:
                # Import and create combined reasoning tool
                from tools.combined_reasoning import CombinedMCPReasoning
                
                combined_tool = CombinedMCPReasoning(
                    polymarket_tool=polymarket_tool,
                    lunarcrush_tool=lunarcrush_tool
                )
                
                # Register the combined tool
                self.register_tool(combined_tool)
                logger.info("✅ Combined reasoning tool setup successfully")
            else:
                logger.warning("⚠️ Cannot setup combined reasoning - required tools missing")
                
                # Still register but with limited functionality
                from tools.combined_reasoning import CombinedMCPReasoning
                combined_tool = CombinedMCPReasoning()
                self.register_tool(combined_tool)
                logger.info("⚠️ Combined reasoning tool setup with mock data fallback")
                
        except Exception as e:
            logger.error(f"❌ Failed to setup combined reasoning: {e}")
    
    def intelligent_route(self, query: str, parsed_params: Dict[str, Any] = None) -> Any:
        """
        Intelligent routing that can automatically detect when to use
        combined reasoning based on query patterns.
        
        Args:
            query: Raw user query
            parsed_params: Optional pre-parsed parameters
            
        Returns:
            Appropriate tool instance for the query
        """
        # Check if we should use combined reasoning
        combined_tool = self.get_tool("combined_reasoning")
        
        if combined_tool and combined_tool.should_use_combined_reasoning(query):
            logger.info(f"🎯 Intelligent routing: Using combined reasoning for '{query[:50]}...'")
            return combined_tool
        
        # Fall back to normal routing
        if parsed_params:
            return self.route(parsed_params)
        else:
            # Simple routing based on keywords
            return self._simple_keyword_routing(query)
    
    def _simple_keyword_routing(self, query: str) -> Any:
        """Simple routing based on query keywords."""
        query_lower = query.lower()
        
        # Check for explicit tool mentions first (highest priority)
        if "polymarket" in query_lower:
            tool = self.get_tool("get_events")
            if tool:
                logger.info("📊 Routing to Polymarket events tool (explicit mention)")
                return tool
        
        if "lunarcrush" in query_lower:
            tool = self.get_tool("get_coins_list")
            if tool:
                logger.info("🪙 Routing to LunarCrush coins tool (explicit mention)")
                return tool
        
        # For event-related queries, prioritize Polymarket
        if any(word in query_lower for word in ["events", "market", "prediction", "sports", "politics"]):
            tool = self.get_tool("get_events")
            if tool:
                logger.info("📊 Routing to Polymarket events tool")
                return tool
        
        # Keyword mappings for crypto data (price, sentiment analysis)
        if any(word in query_lower for word in ["coins", "price", "sentiment", "galaxy"]) and not any(word in query_lower for word in ["events", "market", "prediction"]):
            tool = self.get_tool("get_coins_list")
            if tool:
                logger.info("🪙 Routing to LunarCrush coins tool")
                return tool
        
        # Default to first available tool
        available_tools = list(self.tools_registry.values())
        if available_tools:
            logger.info(f"🔄 Default routing to {available_tools[0].tool_name}")
            return available_tools[0]
        
        raise ValueError("No tools available for routing")
    
    async def execute_intelligent_query(self, query: str, additional_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a query using intelligent routing and return results.
        
        Args:
            query: User query string
            additional_params: Optional additional parameters
            
        Returns:
            Execution results from the appropriate tool
        """
        logger.info(f"🚀 Executing intelligent query: '{query}'")
        
        try:
            # Get the right tool
            tool = self.intelligent_route(query)
            
            # Prepare parameters
            params = {"query": query}
            if additional_params:
                params.update(additional_params)
            
            # If it's combined reasoning, use the query directly
            if hasattr(tool, 'should_use_combined_reasoning'):
                return await tool.execute(params)
            
            # For other tools, extract relevant parameters
            if "get_coins_list" in tool.tool_name:
                # Extract LunarCrush parameters
                params.update({
                    "limit": additional_params.get("limit", 10),
                    "sort": additional_params.get("sort", "mc"),
                    "category": additional_params.get("category", "")
                })
            elif "get_events" in tool.tool_name:
                # Extract Polymarket parameters
                keyword = self._extract_keyword_simple(query)
                params.update({
                    "keyword": keyword,
                    "limit": additional_params.get("limit", 5),
                    "time_filter": additional_params.get("time_filter", "recent")
                })
            
            # Execute the tool
            return await tool.execute(params)
            
        except Exception as e:
            logger.error(f"❌ Intelligent query execution failed: {e}")
            return [{"error": f"Query execution failed: {str(e)}"}]
    
    def _extract_keyword_simple(self, query: str) -> str:
        """Simple keyword extraction for non-combined reasoning tools."""
        keywords = ["trump", "election", "bitcoin", "crypto", "sports", "politics", "tech"]
        query_lower = query.lower()
        
        for keyword in keywords:
            if keyword in query_lower:
                return keyword.title()
        
        return "general"
    
    def get_routing_info(self) -> Dict[str, Any]:
        """Get information about routing capabilities."""
        return {
            "routing_modes": ["standard", "intelligent", "combined_reasoning"],
            "available_tools": list(self.tools_registry.keys()),
            "combined_reasoning_available": "combined_reasoning" in self.tools_registry,
            "intelligent_patterns": [
                "position queries → combined_reasoning",
                "crypto queries → get_coins_list", 
                "market/event queries → get_events"
            ]
        }