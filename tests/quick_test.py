#!/usr/bin/env python3
"""Quick test of the MCP tools endpoint."""

import asyncio
import aiohttp
import json

async def test_mcp_tools():
    """Test the updated MCP tools endpoint."""
    print("🔍 Testing MCP tools endpoint...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8001/mcp/tools") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Response: {json.dumps(data, indent=2)}")
                    
                    # Check if it has the success field
                    if data.get("success", False):
                        tools = data.get("tools", [])
                        print(f"✅ Successfully fetched {len(tools)} tools")
                        return True
                    else:
                        print(f"❌ Success field is False or missing")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Error: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())