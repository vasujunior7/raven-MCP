"""OpenAI Script with MCP Tool Integration using Raven Reasoning Model."""

import asyncio
import json
import logging
import os
import aiohttp
from typing import Dict, Any, List
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPToolClient:
    """OpenAI client that uses MCP server as a tool."""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8000"):
        """Initialize the client with Raven model and MCP server."""
        self.mcp_server_url = mcp_server_url
        
        # Initialize Raven Reasoning Model
        api_key = os.getenv('RAVEN_REASONING_MODEL_API_KEY')
        api_url = os.getenv('RAVEN_REASONING_MODEL_API_URL')
        model_name = os.getenv('RAVEN_REASONING_MODEL_DEPLOYMENT_NAME', 'raven-model')
        
        if not api_key or not api_url:
            raise ValueError("Raven model credentials not found in .env file")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_url
        )
        self.model_name = model_name
        
        logger.info(f"Initialized Raven client with model: {model_name}")
        logger.info(f"MCP Server URL: {mcp_server_url}")
    
    async def call_mcp_tool(self, query: str) -> Dict[str, Any]:
        """Call the MCP server to get prediction market data."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mcp_server_url}/query",
                    json={"query": query},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"MCP server error {response.status}: {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to connect to MCP server: {str(e)}"
            }
    
    async def get_mcp_tool_definitions(self) -> List[Dict[str, Any]]:
        """Fetch tool definitions from MCP server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.mcp_server_url}/mcp/tools",
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success", False):
                            return data.get("tools", [])
                        else:
                            logger.error(f"MCP server returned error: {data.get('error', 'Unknown error')}")
                            return []
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to fetch tool definitions: {response.status} {error_text}")
                        return []
        except Exception as e:
            logger.error(f"Failed to connect to MCP server for tool definitions: {str(e)}")
            return []
    
    async def process_user_request(self, user_message: str) -> str:
        """Process user request using Raven model with MCP tool access."""
        try:
            # First, check if we need to call MCP tools
            if any(keyword in user_message.lower() for keyword in ['prediction', 'market', 'trump', 'election', 'betting', 'forecast']):
                # This looks like a prediction market query, call MCP directly
                print("🔍 Detected prediction market query, calling MCP directly...")
                mcp_result = await self.call_mcp_tool(user_message)
                
                if mcp_result.get("success", False):
                    # Format the MCP results for the LLM
                    results = mcp_result.get("results", [])
                    
                    # Create a simple prompt for Raven model (no function calling)
                    enhanced_prompt = f"""User asked: {user_message}

Here are the prediction market results I found:

{json.dumps(results, indent=2)}

Please analyze these prediction markets and provide insights about the data."""
                    
                    # Simple chat completion without tools
                    response = await self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert prediction market analyst. Analyze the provided market data and give insightful commentary."
                            },
                            {
                                "role": "user", 
                                "content": enhanced_prompt
                            }
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    # Handle different response formats from Raven model
                    message_content = response.choices[0].message.content
                    if message_content:
                        return message_content
                    else:
                        # If content is None, try to extract from the full response
                        logger.info(f"Response content is None, full response: {response}")
                        return "I successfully retrieved prediction market data, but the analysis response was empty. The MCP integration is working correctly."
                else:
                    return f"I couldn't fetch prediction market data: {mcp_result.get('error', 'Unknown error')}"
            else:
                # For non-prediction market queries, use simple completion
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that can answer questions about various topics."
                        },
                        {
                            "role": "user", 
                            "content": user_message
                        }
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

async def main():
    """Main interactive loop."""
    print("🧠 Raven Reasoning Model with MCP Prediction Markets")
    print("=" * 60)
    print("Ask me about prediction markets, betting odds, or forecasts!")
    print("Examples:")
    print("  - What are the latest Trump election odds?")
    print("  - Show me crypto price predictions")
    print("  - Find sports betting markets for this weekend")
    print("  - What do prediction markets say about AI development?")
    print("\nType 'quit' to exit\n")
    
    # Check if MCP server is running
    try:
        client = MCPToolClient()
        health_check = await client.call_mcp_tool("test")
        if "error" in health_check and "connect" in health_check["error"].lower():
            print("⚠️  MCP Server not running. Please start it first:")
            print("   python server.py")
            return
        else:
            print("✅ Connected to MCP Server")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    print()
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("🧠 Raven: ", end="", flush=True)
            
            # Process with Raven model
            response = await client.process_user_request(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())