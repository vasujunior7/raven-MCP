#!/usr/bin/env python3
"""
HTTP Server version for easier testing and debugging.
This creates a simple web interface to test the MCP server.
"""

import asyncio
import json
import logging
from aiohttp import web, web_response
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from main import MCPServer
from utils.logger import setup_logger

logger = setup_logger(__name__)

class HTTPMCPServer:
    """HTTP wrapper for MCP server testing."""
    
    def __init__(self, port=8080):
        self.port = port
        self.mcp_server = MCPServer()
        self.app = web.Application()
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_get('/', self.home_page)
        self.app.router.add_post('/query', self.handle_query)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/tools', self.list_tools)
        
        # Enable CORS for web testing
        self.app.router.add_options('/query', self.handle_options)
    
    async def handle_options(self, request):
        """Handle CORS preflight requests."""
        return web_response.Response(
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        )
    
    async def home_page(self, request):
        """Serve a simple test interface."""
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>🧠 Raven MCP Server - Test Interface</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: #f0f8ff; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .query-box { width: 100%; padding: 10px; font-size: 16px; border: 2px solid #ddd; border-radius: 5px; }
        .button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .button:hover { background: #0056b3; }
        .results { background: #f8f9fa; padding: 20px; border-radius: 5px; margin-top: 20px; white-space: pre-wrap; }
        .example { background: #e7f3ff; padding: 10px; margin: 5px 0; border-radius: 5px; cursor: pointer; }
        .example:hover { background: #cce7ff; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 Raven MCP Server</h1>
        <p>Natural language interface for Polymarket prediction markets</p>
        <p><strong>✨ Enhanced with typo tolerance and fuzzy matching!</strong></p>
    </div>
    
    <h2>🎯 Test Your Queries</h2>
    <input type="text" id="queryInput" class="query-box" placeholder="Enter your query here..." value="sports events limit 3">
    <br><br>
    <button class="button" onclick="sendQuery()">🚀 Send Query</button>
    
    <h3>📝 Example Queries (click to try):</h3>
    <div class="example" onclick="setQuery('sports events limit 5')">🏈 sports events limit 5</div>
    <div class="example" onclick="setQuery('fetch me cryptp events')">💎 fetch me cryptp events (typo test!)</div>
    <div class="example" onclick="setQuery('poltics events limit 2')">🗳️ poltics events limit 2 (typo test!)</div>
    <div class="example" onclick="setQuery('get some sports events')">🎾 get some sports events</div>
    <div class="example" onclick="setQuery('crypto events limit 3 offset 5')">🪙 crypto events limit 3 offset 5</div>
    
    <div id="results" class="results" style="display: none;">
        <h3>📊 Results:</h3>
        <div id="resultsContent"></div>
    </div>
    
    <script>
        function setQuery(query) {
            document.getElementById('queryInput').value = query;
        }
        
        async function sendQuery() {
            const query = document.getElementById('queryInput').value;
            if (!query.trim()) {
                alert('Please enter a query!');
                return;
            }
            
            const resultsDiv = document.getElementById('results');
            const resultsContent = document.getElementById('resultsContent');
            
            resultsContent.innerHTML = '⏳ Processing query...';
            resultsDiv.style.display = 'block';
            
            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let output = `✅ Found ${data.count} results:\\n\\n`;
                    
                    // Use the formatted table from server if available
                    if (data.formatted_output) {
                        output += data.formatted_output;
                    } else if (data.results && data.results.length > 0) {
                        // Fallback to basic formatting
                        data.results.forEach((result, index) => {
                            output += `${index + 1}. ${result.title || result.name || 'Untitled'}\\n`;
                            if (result.volume !== undefined) {
                                output += `   💰 Volume: $${result.volume.toLocaleString()}\\n`;
                            }
                            if (result.price !== undefined) {
                                output += `   💰 Price: $${result.price.toLocaleString()}\\n`;
                            }
                            if (result.endDate) {
                                output += `   📅 End Date: ${result.endDate}\\n`;
                            }
                            if (result.url) {
                                output += `   🔗 URL: ${result.url}\\n`;
                            }
                            output += '\\n';
                        });
                    } else {
                        output += '(No results found - this may be normal for crypto/politics markets)';
                    }
                    
                    resultsContent.innerHTML = output;
                } else {
                    resultsContent.innerHTML = `❌ Error: ${data.error || 'Unknown error'}`;
                }
            } catch (error) {
                resultsContent.innerHTML = `❌ Network Error: ${error.message}`;
            }
        }
        
        // Allow Enter key to submit
        document.getElementById('queryInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendQuery();
            }
        });
    </script>
</body>
</html>'''
        return web_response.Response(text=html, content_type='text/html')
    
    async def handle_query(self, request):
        """Handle query requests."""
        try:
            data = await request.json()
            query = data.get('query', '')
            
            if not query:
                return web.json_response({
                    'success': False,
                    'error': 'No query provided'
                }, headers={'Access-Control-Allow-Origin': '*'})
            
            logger.info(f"HTTP Query: {query}")
            
            # Process through MCP server
            result = await self.mcp_server.process_query(query)
            
            # Format the results using the same table formatter as CLI
            if result['success'] and result['results']:
                from utils.formatter import ResponseFormatter
                formatter = ResponseFormatter()
                formatted_table = formatter.format_table(result['results'])
                
                # Return formatted table text instead of raw JSON
                return web.json_response({
                    'success': True,
                    'query': result['query'],
                    'count': result['count'],
                    'formatted_output': formatted_table,
                    'results': result['results']  # Keep raw data for compatibility
                }, headers={'Access-Control-Allow-Origin': '*'})
            else:
                return web.json_response(result, headers={
                    'Access-Control-Allow-Origin': '*'
                })
            
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, headers={'Access-Control-Allow-Origin': '*'})
    
    async def health_check(self, request):
        """Health check endpoint."""
        health = self.mcp_server.health_check()
        return web.json_response(health, headers={
            'Access-Control-Allow-Origin': '*'
        })
    
    async def list_tools(self, request):
        """List available tools."""
        tools = self.mcp_server.list_tools()
        return web.json_response(tools, headers={
            'Access-Control-Allow-Origin': '*'
        })
    
    async def start(self):
        """Start the HTTP server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        print(f"🌐 Raven MCP Server running at: http://localhost:{self.port}")
        print(f"📱 Open the link above to test the server!")
        print(f"🔍 Try queries like: 'fetch me cryptp events' or 'sports events limit 3'")
        print(f"⚠️  For MCP Inspector, use: python mcp_server.py")
        print(f"🛑 Press Ctrl+C to stop")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\\n🛑 Stopping server...")
            await runner.cleanup()

async def main():
    server = HTTPMCPServer(port=8080)
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())