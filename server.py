"""MCP Server Web Service - Runs on a port for external access."""

import asyncio
import json
import logging
from typing import Dict, Any
from aiohttp import web, ClientSession
from aiohttp.web_runner import GracefulExit

from main import MCPServer
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MCPWebServer:
    """Web service wrapper for MCP Server."""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        """Initialize the web server."""
        self.host = host
        self.port = port
        self.mcp_server = MCPServer()
        self.app = web.Application()
        self._setup_routes()
        
        logger.info(f"MCP Web Server initialized on {host}:{port}")
    
    def _setup_routes(self):
        """Set up HTTP routes."""
        self.app.router.add_post('/query', self.handle_query)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/tools', self.handle_list_tools)
        self.app.router.add_get('/mcp/tools', self.handle_mcp_tool_definitions)
        self.app.router.add_options('/query', self.handle_cors)
        
        # Add CORS middleware
        self.app.middlewares.append(self.cors_handler)
    
    @web.middleware
    async def cors_handler(self, request, handler):
        """Handle CORS for cross-origin requests."""
        if request.method == 'OPTIONS':
            response = web.Response()
        else:
            response = await handler(request)
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    async def handle_cors(self, request):
        """Handle CORS preflight requests."""
        return web.Response(headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })
    
    async def handle_query(self, request):
        """Handle prediction market queries."""
        try:
            data = await request.json()
            query = data.get('query', '')
            tool_name = data.get('tool_name')
            
            if not query:
                return web.json_response({
                    'error': 'Query parameter is required'
                }, status=400)
            
            logger.info(f"Processing web query: {query}")
            
            # Process through MCP server
            result = await self.mcp_server.process_query(query, tool_name)
            
            return web.json_response(result)
            
        except json.JSONDecodeError:
            return web.json_response({
                'error': 'Invalid JSON in request body'
            }, status=400)
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            return web.json_response({
                'error': str(e)
            }, status=500)
    
    async def handle_health(self, request):
        """Health check endpoint."""
        health = self.mcp_server.health_check()
        health['web_server'] = 'ok'
        health['endpoint'] = f"http://{self.host}:{self.port}"
        return web.json_response(health)
    
    async def handle_list_tools(self, request):
        """List available tools endpoint."""
        tools = await self.mcp_server.list_available_tools()
        return web.json_response(tools)
    
    async def handle_mcp_tool_definitions(self, request):
        """Get MCP tool definitions for OpenAI function calling."""
        try:
            # Get available tools from MCP server
            tools_info = await self.mcp_server.list_available_tools()
            
            # Convert to OpenAI function calling format
            openai_tools = []
            
            for tool_name, tool_info in tools_info["available_tools"].items():
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": f"mcp_{tool_name}",
                        "description": tool_info.get("description", f"Execute {tool_name} tool"),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Natural language query for the tool"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
                openai_tools.append(openai_tool)
            
            # Add a general prediction markets tool
            prediction_markets_tool = {
                "type": "function",
                "function": {
                    "name": "get_prediction_markets",
                    "description": "Get prediction market events and data based on natural language queries. Can find political elections, sports betting, crypto predictions, technology forecasts, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query for prediction markets (e.g. 'Trump election markets', 'crypto price predictions', 'sports betting events')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
            openai_tools.append(prediction_markets_tool)
            
            return web.json_response({
                "success": True,
                "tools": openai_tools,
                "mcp_server_info": {
                    "available_tools": len(tools_info["available_tools"]),
                    "server_status": "healthy",
                    "server_url": f"http://{self.host}:{self.port}"
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting tool definitions: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)
    
    async def start_server(self):
        """Start the web server."""
        try:
            logger.info(f"Starting MCP Web Server on http://{self.host}:{self.port}")
            
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            
            print(f"🚀 MCP Server running on http://{self.host}:{self.port}")
            print(f"📋 Available endpoints:")
            print(f"   POST /query - Process prediction market queries")
            print(f"   GET  /health - Health check")
            print(f"   GET  /tools - List available tools")
            print(f"   GET  /mcp/tools - Get OpenAI tool definitions")
            print(f"\n📝 Example request:")
            print(f'   curl -X POST http://{self.host}:{self.port}/query \\')
            print(f'     -H "Content-Type: application/json" \\')
            print(f'     -d \'{{"query": "Show me 3 Trump election events"}}\'')
            print(f"\n🛑 Press Ctrl+C to stop the server")
            
            # Keep server running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
            finally:
                await runner.cleanup()
                
        except Exception as e:
            logger.error(f"Server startup failed: {e}")
            raise

async def main():
    """Main entry point for the web server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server Web Service")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    server = MCPWebServer(host=args.host, port=args.port)
    await server.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")