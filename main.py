#!/usr/bin/env python3
"""
🧠 MCP Server — Main Entry Point

This is the central entry point for the MCP (Model Context Protocol) Server.
It orchestrates natural language query understanding, tool routing, and response formatting.

Architecture:
- Input Understanding Layer (parser)
- Tool Invocation Layer (router) 
- Execution & Post-Processing Layer (executor)
- Response formatting
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from core.parser import QueryParser
from core.router import ToolRouter
from core.executor import ToolExecutor
from core.postprocess import ResponseProcessor
from utils.logger import setup_logger
from utils.http import HTTPClient

# Setup logging
logger = setup_logger(__name__)

class MCPServer:
    """
    Main MCP Server class that coordinates all components.
    
    This server converts natural language queries into structured tool invocations,
    executes them against external APIs, and returns normalized JSON responses.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the MCP Server with configuration."""
        self.config_path = config_path or "config"
        
        # Initialize core components
        self.parser = QueryParser(self.config_path)
        self.router = ToolRouter(self.config_path)
        self.executor = ToolExecutor()
        self.processor = ResponseProcessor()
        
        logger.info("MCP Server initialized successfully")
    
    async def process_query(self, query: str, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a natural language query end-to-end.
        
        Args:
            query: Natural language query (e.g., "Show me 3 Trump election events")
            tool_name: Optional specific tool to use (defaults to auto-detection)
            
        Returns:
            Structured JSON response with normalized data
        """
        try:
            logger.info(f"Processing query: '{query}'")
            
            # Step 1: Parse natural language into structured parameters
            parsed_params = self.parser.parse(query, tool_name)
            logger.debug(f"Parsed parameters: {parsed_params}")
            
            # Step 2: Route to appropriate tool
            tool_instance = self.router.route(parsed_params)
            logger.debug(f"Routed to tool: {tool_instance.__class__.__name__}")
            
            # Step 3: Execute the tool
            raw_results = await self.executor.execute(tool_instance, parsed_params)
            logger.debug(f"Execution completed, got {len(raw_results)} results")
            
            # Step 4: Post-process and normalize results
            processed_results = self.processor.process(raw_results, parsed_params)
            logger.info(f"Query processed successfully, returning {len(processed_results)} results")
            
            return {
                "success": True,
                "query": query,
                "results": processed_results,
                "count": len(processed_results)
            }
            
        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "results": []
            }
    
    async def list_available_tools(self) -> Dict[str, Any]:
        """List all available tools and their capabilities."""
        return self.router.list_tools()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the server."""
        return {
            "status": "healthy",
            "components": {
                "parser": "ok",
                "router": "ok", 
                "executor": "ok",
                "processor": "ok"
            }
        }

if __name__ == "__main__":
    # Simple test when run directly
    import asyncio
    
    async def test():
        server = MCPServer()
        result = await server.process_query("Show me sports events")
        print(f"Test query result: {result['count']} results found")
    
    asyncio.run(test())