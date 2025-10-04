# 🔧 MCP Server Tools

This directory contains pluggable tool implementations that extend the MCP Server's capabilities. Each tool provides specific functionality for external API integration and data retrieval.

## 📋 Available Tools

### 📊 Prediction Markets

| Tool                   | File                    | Description                      | APIs           |
| ---------------------- | ----------------------- | -------------------------------- | -------------- |
| **Polymarket Fetcher** | `polymarket_fetcher.py` | Prediction market data retrieval | Polymarket API |

## 🏗️ Tool Architecture

### Base Tool Interface

All tools implement a common interface for consistency:

```python
class BaseTool:
    tool_name = "tool_name"
    description = "Tool description"

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return OpenAI function calling schema."""
        pass
```

### Tool Discovery

Tools are automatically discovered by the MCP Server through:

1. **File-based Discovery**: Files in `/tools` directory
2. **Class Inspection**: Classes implementing the tool interface
3. **Dynamic Registration**: Tools register themselves at startup

## 📊 Polymarket Fetcher

### Overview

The Polymarket Fetcher retrieves prediction market data and events based on natural language queries.

### Features

- **Natural Language Processing**: Convert queries to market filters
- **Event Categorization**: Politics, sports, crypto, technology
- **Data Normalization**: Consistent JSON response format
- **Mock Data Support**: Fallback data for development/testing

### Usage

```python
from tools.polymarket_fetcher import PolymarketFetcher

fetcher = PolymarketFetcher()
results = await fetcher.execute({
    "keyword": "politics",
    "limit": 5
})
```

### Response Format

```json
{
  "success": true,
  "results": [
    {
      "id": "event_123",
      "title": "Will Donald Trump win the 2024 US Presidential Election?",
      "description": "Resolves to Yes if Trump is elected president...",
      "endDate": "2025-11-05T23:59:59Z",
      "volume": 150000.0,
      "tags": ["politics", "election"],
      "category": "politics",
      "source": "polymarket",
      "url": "https://polymarket.com/event/..."
    }
  ],
  "count": 1,
  "query_info": {
    "keyword": "politics",
    "limit": 5,
    "tool_used": "polymarket_fetcher"
  }
}
```

## 🚀 Adding New Tools

### 1. Create Tool File

```python
# tools/new_tool.py
from typing import Dict, Any

class NewTool:
    tool_name = "new_tool"
    description = "Description of what this tool does"

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation."""
        try:
            # Your tool logic here
            results = await self.fetch_data(params)

            return {
                "success": True,
                "results": results,
                "count": len(results),
                "query_info": params
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query_info": params
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return OpenAI function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.tool_name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
```

### 2. Register Tool

The MCP Server automatically discovers tools in the `/tools` directory. No manual registration needed!

### 3. Test Tool

```python
# Test your new tool
python -c "
from tools.new_tool import NewTool
import asyncio

async def test():
    tool = NewTool()
    result = await tool.execute({'query': 'test query'})
    print(result)

asyncio.run(test())
"
```

## 🔧 Tool Development Guidelines

### Best Practices

1. **Error Handling**: Always return structured error responses
2. **Async Support**: Use `async/await` for all network operations
3. **Schema Definition**: Provide clear OpenAI function schemas
4. **Data Normalization**: Return consistent JSON formats
5. **Logging**: Use the project's logging utilities

### Response Standards

All tools should return responses in this format:

```python
{
    "success": bool,
    "results": list,      # On success
    "error": str,         # On failure
    "count": int,         # Number of results
    "query_info": dict    # Original query parameters
}
```

### Testing

Each tool should include:

- Unit tests for core functionality
- Integration tests with external APIs
- Mock data for offline testing
- Error scenario testing

## 📚 Tool Examples

### API Integration Tool

```python
class APITool:
    async def fetch_from_api(self, endpoint: str, params: dict):
        """Fetch data from external API."""
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params) as response:
                return await response.json()
```

### Data Processing Tool

```python
class DataProcessor:
    def normalize_data(self, raw_data: list) -> list:
        """Normalize raw data to standard format."""
        return [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "category": self.categorize(item),
                "source": self.tool_name
            }
            for item in raw_data
        ]
```

## 🔮 Future Tools

Planned tool expansions:

- **LunarCrush Integration**: Social sentiment analysis
- **Twitter API**: Real-time social media monitoring
- **News APIs**: Current events and trending topics
- **Financial Data**: Stock market and economic indicators
- **Custom ML Models**: AI-powered predictions and analysis

## 🤝 Contributing

1. Fork the repository
2. Create your tool in `/tools` directory
3. Follow the established patterns and interfaces
4. Add comprehensive tests
5. Update this README with your tool documentation
6. Submit a pull request

---

**Ready to build? Check out `polymarket_fetcher.py` as a reference implementation! 🚀**
