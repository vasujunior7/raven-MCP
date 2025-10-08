#!/usr/bin/env python3
"""
MCP Server - Model Context Protocol compatibility layer for MCP Inspector.
This provides a standard MCP interface for hosted testing.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Sequence
from contextlib import asynccontextmanager

# MCP Server imports
try:
    from mcp.server import Server
    from mcp.types import (
        Resource, Tool, TextContent, ImageContent, EmbeddedResource,
        LoggingLevel, CallToolResult, ReadResourceResult, ListResourcesResult,
        ListToolsResult
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️ MCP not available - install with: pip install mcp")

# Our server imports
from main import MCPServer
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MCPInspectorServer:
    """MCP Inspector compatible server wrapper."""
    
    def __init__(self):
        """Initialize the MCP Inspector server."""
        self.raven_server = MCPServer()
        self.app = Server("raven-mcp") if MCP_AVAILABLE else None
        logger.info("MCP Inspector Server initialized")
    
    async def setup_mcp_handlers(self):
        """Setup MCP protocol handlers."""
        if not MCP_AVAILABLE:
            logger.error("MCP not available - cannot setup handlers")
            return
        
        # List available tools
        @self.app.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools for MCP Inspector."""
            tools_info = self.raven_server.list_tools()
            
            tools = []
            for tool_name, tool_data in tools_info["available_tools"].items():
                tools.append(Tool(
                    name=tool_name,
                    description=tool_data["description"],
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query"
                            },
                            "keyword": {
                                "type": "string", 
                                "description": "Category keyword (sports, politics, crypto)",
                                "enum": ["sports", "politics", "crypto"]
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "minimum": 1,
                                "maximum": 50,
                                "default": 5
                            },
                            "offset": {
                                "type": "integer",
                                "description": "Pagination offset",
                                "minimum": 0,
                                "default": 0
                            }
                        },
                        "required": ["query"]
                    }
                ))
            
            return ListToolsResult(tools=tools)
        
        # Handle tool calls
        @self.app.call_tool()
        async def call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool execution calls."""
            try:
                # Extract query and convert to natural language format
                query = arguments.get("query", "")
                keyword = arguments.get("keyword", "")
                limit = arguments.get("limit", 5)
                offset = arguments.get("offset", 0)
                
                # Build enhanced query
                if keyword and keyword not in query.lower():
                    query = f"{keyword} {query}"
                
                if limit != 5:
                    query += f" limit {limit}"
                
                if offset > 0:
                    query += f" offset {offset}"
                
                logger.info(f"Processing MCP tool call: {name} with query: '{query}'")
                
                # Process through our main server
                result = await self.raven_server.process_query(query)
                
                if result["success"]:
                    # Format results for MCP Inspector using the same formatter as CLI
                    content = []
                    
                    # Add summary
                    summary = f"✅ Found {result['count']} results:\n"
                    content.append(TextContent(type="text", text=summary))
                    
                    # Add formatted table using the same formatter as CLI
                    if result["results"]:
                        from utils.formatter import ResponseFormatter
                        formatter = ResponseFormatter()
                        table_output = formatter.format_table(result["results"])
                        content.append(TextContent(type="text", text=table_output))
                    else:
                        content.append(TextContent(type="text", text="No results found."))
                    
                    return CallToolResult(content=content)
                else:
                    error_msg = f"Query failed: {result.get('error', 'Unknown error')}"
                    return CallToolResult(
                        content=[TextContent(type="text", text=error_msg)],
                        isError=True
                    )
                    
            except Exception as e:
                logger.error(f"Tool call error: {str(e)}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
        
        # List resources (optional)
        @self.app.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available resources."""
            resources = [
                Resource(
                    uri="raven://health",
                    name="Health Check",
                    description="Server health status",
                    mimeType="application/json"
                ),
                Resource(
                    uri="raven://tools",
                    name="Available Tools",
                    description="List of available tools and capabilities",
                    mimeType="application/json"
                )
            ]
            return ListResourcesResult(resources=resources)
        
        # Read resources
        @self.app.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read resource content."""
            if uri == "raven://health":
                health_data = self.raven_server.health_check()
                return ReadResourceResult(
                    contents=[TextContent(
                        type="text", 
                        text=json.dumps(health_data, indent=2)
                    )]
                )
            elif uri == "raven://tools":
                tools_data = self.raven_server.list_tools()
                return ReadResourceResult(
                    contents=[TextContent(
                        type="text",
                        text=json.dumps(tools_data, indent=2)
                    )]
                )
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    def _format_results_for_mcp(self, results: list) -> str:
        """Format results for MCP Inspector display."""
        if not results:
            return "No results to display."
        
        # Detect result type
        first_result = results[0]
        
        if "title" in first_result and "volume" in first_result:
            # Polymarket events format
            formatted = "📊 **Polymarket Events**\n\n"
            for i, event in enumerate(results, 1):
                formatted += f"**{i}. {event.get('title', 'Untitled')}**\n"
                formatted += f"   💰 Volume: ${event.get('volume', 0):,.2f}\n"
                formatted += f"   📅 End Date: {event.get('endDate', 'TBD')}\n"
                formatted += f"   🏷️ Tags: {', '.join(event.get('tags', []))}\n"
                formatted += f"   🔗 URL: {event.get('url', 'N/A')}\n\n"
            
        elif "symbol" in first_result and ("price" in first_result or "galaxy_score" in first_result):
            # Crypto data format - Enhanced with table-like display
            formatted = "🪙 **Cryptocurrency Sentiment Analysis**\n\n"
            
            # Create table header
            formatted += "```\n"
            formatted += "Title     | Symbol   | Price    | Galaxy_Score | Sentiment | Market_Cap\n"
            formatted += "----------------------------------------------------------------------------\n"
            
            # Format each crypto entry
            for coin in results:
                title = (coin.get('title', coin.get('name', 'Unknown')) or 'Unknown')[:9].ljust(9)
                symbol = f"({coin.get('symbol', 'N/A')})"[:8].ljust(8)
                
                # Price formatting
                price = coin.get('price', 0)
                if price >= 1000:
                    price_str = f"${price:,.0f}"[:8]
                elif price >= 1:
                    price_str = f"${price:,.2f}"[:8]
                else:
                    price_str = f"${price:.4f}"[:8]
                price_str = price_str.ljust(8)
                
                # Galaxy score with star
                galaxy_score = coin.get('galaxy_score', 0)
                galaxy_str = f"{galaxy_score:.1f}⭐"[:12].ljust(12)
                
                # Sentiment with emoji
                sentiment = coin.get('sentiment', 'Neutral')
                if 'bullish' in sentiment.lower():
                    sentiment_str = f"📈 {sentiment}"
                elif 'bearish' in sentiment.lower():
                    sentiment_str = f"📉 {sentiment}"
                else:
                    sentiment_str = f"➖ {sentiment}"
                sentiment_str = sentiment_str[:11].ljust(11)
                
                # Market cap formatting
                market_cap = coin.get('market_cap', 0)
                if market_cap >= 1e12:
                    mc_str = f"${market_cap/1e12:.1f}T"
                elif market_cap >= 1e9:
                    mc_str = f"${market_cap/1e9:.1f}B"
                elif market_cap >= 1e6:
                    mc_str = f"${market_cap/1e6:.1f}M"
                else:
                    mc_str = f"${market_cap:,.0f}"
                
                formatted += f"{title} | {symbol} | {price_str} | {galaxy_str} | {sentiment_str} | {mc_str}\n"
            
            formatted += "```\n\n"
            
            # Add detailed breakdown
            formatted += "**Detailed Breakdown:**\n\n"
            for i, coin in enumerate(results, 1):
                formatted += f"**{i}. {coin.get('title', coin.get('name', 'Unknown'))} ({coin.get('symbol', 'N/A')})**\n"
                formatted += f"   💰 Price: ${coin.get('price', 0):,.2f}\n"
                formatted += f"   ⭐ Galaxy Score: {coin.get('galaxy_score', 'N/A')}/100\n"
                formatted += f"   � Sentiment: {coin.get('sentiment', 'N/A')}\n"
                formatted += f"   🏦 Market Cap: ${coin.get('market_cap', 0):,.0f}\n"
                formatted += f"   📈 24h Change: {coin.get('percent_change_24h', 'N/A')}%\n"
                formatted += f"   📊 Volume 24h: ${coin.get('volume_24h', 0):,.0f}\n"
                formatted += f"   🎯 Alt Rank: #{coin.get('alt_rank', 'N/A')}\n\n"
        
        else:
            # Generic format
            formatted = "📋 **Results**\n\n"
            for i, item in enumerate(results, 1):
                formatted += f"**{i}.** {json.dumps(item, indent=2)}\n\n"
        
        return formatted
    
    async def run_server(self):
        """Run the MCP server with stdio transport."""
        if not MCP_AVAILABLE:
            logger.error("Cannot run MCP server - MCP not installed")
            return
        
        await self.setup_mcp_handlers()
        
        # Import and setup stdio transport
        from mcp.server.stdio import stdio_server
        
        logger.info("Starting MCP Inspector compatible server...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream, 
                write_stream,
                self.app.create_initialization_options()
            )

# Standalone runner for MCP Inspector
async def main():
    """Main entry point for MCP Inspector."""
    server = MCPInspectorServer()
    await server.run_server()

if __name__ == "__main__":
    if MCP_AVAILABLE:
        asyncio.run(main())
    else:
        print("❌ MCP not available. Install with: pip install mcp")
        print("💡 For manual testing, use: python client/cli.py 'your query here'")
        sys.exit(1)