"""MCP Protocol Integration for VSCode and other MCP clients."""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, List, Optional, Sequence
from dataclasses import dataclass
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import MCPServer
from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class MCPTool:
    """MCP Tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any]

@dataclass 
class MCPResource:
    """MCP Resource definition."""
    uri: str
    name: str
    description: str
    mimeType: str

class MCPProtocolServer:
    """MCP Protocol Server implementation for VSCode and other clients."""
    
    def __init__(self):
        """Initialize the MCP protocol server."""
        self.mcp_server = MCPServer()
        self.tools: List[MCPTool] = []
        self.resources: List[MCPResource] = []
        
        # Register available tools
        self._register_tools()
        
        logger.info("MCPProtocolServer initialized")
    
    def _register_tools(self):
        """Register available tools in MCP format."""
        # Get events tool
        self.tools.append(MCPTool(
            name="get_events",
            description="Fetch prediction market events from various sources with natural language queries",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query (e.g., 'Show me 3 Trump election events')"
                    },
                    "limit": {
                        "type": "integer", 
                        "description": "Maximum number of results to return",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 5
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Specific keyword or category filter",
                        "enum": ["politics", "sports", "crypto", "technology", "environment", "general"]
                    }
                },
                "required": ["query"]
            }
        ))
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        logger.info("MCP client initializing")
        
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
                "logging": {}
            },
            "serverInfo": {
                "name": "mcp-server",
                "version": "1.0.0"
            }
        }
    
    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP list tools request."""
        logger.debug("Listing available tools")
        
        tools_list = []
        for tool in self.tools:
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
        
        return {"tools": tools_list}
    
    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"Tool call: {tool_name} with args: {arguments}")
        
        try:
            if tool_name == "get_events":
                return await self._handle_get_events(arguments)
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Unknown tool: {tool_name}"
                        }
                    ],
                    "isError": True
                }
        
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "content": [
                    {
                        "type": "text", 
                        "text": f"Tool execution failed: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _handle_get_events(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_events tool call."""
        query = arguments.get("query", "")
        
        if not query:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Query parameter is required"
                    }
                ],
                "isError": True
            }
        
        # Process query through MCP server
        result = await self.mcp_server.process_query(query)
        
        if result["success"]:
            # Format results for MCP response
            results_text = self._format_results_for_mcp(result["results"], query)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": results_text
                    }
                ]
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Query failed: {result['error']}"
                    }
                ],
                "isError": True
            }
    
    def _format_results_for_mcp(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format results for MCP text response."""
        if not results:
            return f"No results found for query: '{query}'"
        
        output_lines = [f"📊 Results for: '{query}' ({len(results)} found)\n"]
        
        for i, result in enumerate(results, 1):
            output_lines.append(f"{i}. **{result.get('title', 'Untitled')}**")
            
            if result.get('endDate'):
                output_lines.append(f"   📅 End Date: {result['endDate'][:10]}")
            
            if result.get('volume'):
                volume = result['volume']
                if volume >= 1_000_000:
                    volume_str = f"{volume/1_000_000:.1f}M"
                elif volume >= 1_000:
                    volume_str = f"{volume/1_000:.1f}K"
                else:
                    volume_str = f"{volume:.0f}"
                output_lines.append(f"   💰 Volume: {volume_str}")
            
            if result.get('tags'):
                tags = result['tags']
                if isinstance(tags, list):
                    output_lines.append(f"   🏷️ Tags: {', '.join(tags)}")
            
            if result.get('url'):
                output_lines.append(f"   🔗 URL: {result['url']}")
            
            output_lines.append("")  # Empty line
        
        return "\n".join(output_lines)
    
    async def handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP list resources request."""
        return {"resources": []}
    
    async def handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP read resource request."""
        return {
            "contents": [
                {
                    "uri": params.get("uri", ""),
                    "mimeType": "text/plain",
                    "text": "Resource not implemented"
                }
            ]
        }
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process an MCP request and return response."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        logger.debug(f"Processing MCP request: {method}")
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_list_tools(params)
            elif method == "tools/call":
                result = await self.handle_call_tool(params)
            elif method == "resources/list":
                result = await self.handle_list_resources(params)
            elif method == "resources/read":
                result = await self.handle_read_resource(params)
            else:
                result = {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            response = {
                "jsonrpc": "2.0", 
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
        
        return response

async def main():
    """Main entry point for MCP protocol server."""
    server = MCPProtocolServer()
    
    # Example MCP requests for testing
    test_requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        },
        {
            "jsonrpc": "2.0", 
            "id": 2,
            "method": "tools/list",
            "params": {}
        },
        {
            "jsonrpc": "2.0",
            "id": 3, 
            "method": "tools/call",
            "params": {
                "name": "get_events",
                "arguments": {
                    "query": "Show me 3 Trump election events"
                }
            }
        }
    ]
    
    print("🧠 MCP Protocol Server Test")
    print("=" * 40)
    
    for request in test_requests:
        print(f"\n📨 Request: {request['method']}")
        response = await server.process_request(request)
        
        if "error" in response:
            print(f"❌ Error: {response['error']['message']}")
        else:
            print(f"✅ Success")
            if request['method'] == "tools/call":
                # Print the actual results
                content = response.get("result", {}).get("content", [])
                if content:
                    print(content[0].get("text", "No content"))

if __name__ == "__main__":
    asyncio.run(main())