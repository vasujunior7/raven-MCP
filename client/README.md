# 👥 MCP Server Client Interfaces

This directory contains various client implementations for interacting with the MCP Server, providing different interfaces for different use cases.

## 📋 Available Clients

| Client           | File              | Purpose                | Usage                              |
| ---------------- | ----------------- | ---------------------- | ---------------------------------- |
| **CLI Client**   | `cli.py`          | Command-line interface | Development, testing, automation   |
| **MCP Protocol** | `mcp_protocol.py` | VSCode MCP integration | IDE integration, development tools |

## 🖥️ CLI Client (`cli.py`)

### Overview

The CLI client provides a user-friendly command-line interface for interacting with the MCP Server. Perfect for development, testing, and automation scripts.

### Features

- **Interactive Mode**: Real-time conversation with the MCP server
- **Single Query Mode**: Execute one-off queries
- **Batch Processing**: Process multiple queries from files
- **Output Formatting**: JSON, table, and human-readable formats
- **Error Handling**: Graceful error reporting and debugging

### Usage Examples

#### Interactive Mode

```bash
# Start interactive session
python client/cli.py --interactive

# Example session:
$ python client/cli.py --interactive
🧠 MCP Server CLI - Interactive Mode
Type 'quit' to exit, 'help' for commands

> Show me 3 Trump election markets
✅ Found 3 prediction markets:
1. Will Donald Trump win the 2024 US Presidential Election?
   - Volume: $150,000
   - End Date: 2025-11-05

2. Trump indictment before Jan 2026
   - Volume: $80,000
   - End Date: 2025-12-31

> quit
Goodbye! 👋
```

#### Single Query Mode

```bash
# Execute single query
python client/cli.py "Show me 5 crypto predictions"

# With custom output format
python client/cli.py "Bitcoin markets" --format json

# With server URL
python client/cli.py "Sports betting" --server http://localhost:8001
```

#### Batch Processing

```bash
# Process queries from file
python client/cli.py --batch queries.txt --output results.json
```

### Command Line Options

```bash
python client/cli.py [OPTIONS] [QUERY]

Options:
  --interactive, -i        Start interactive mode
  --server URL             MCP server URL (default: http://localhost:8000)
  --format FORMAT          Output format: json, table, human (default: human)
  --batch FILE             Process queries from file
  --output FILE            Save results to file
  --timeout SECONDS        Request timeout (default: 30)
  --verbose, -v            Enable verbose logging
  --help, -h               Show help message
```

### Configuration

Create `~/.mcp_client_config.json` for default settings:

```json
{
  "server_url": "http://localhost:8000",
  "default_format": "human",
  "timeout": 30,
  "auto_save_history": true,
  "history_file": "~/.mcp_history.json"
}
```

## 🔌 MCP Protocol Client (`mcp_protocol.py`)

### Overview

Implements the Model Context Protocol for VSCode integration, enabling the MCP Server to work as a VSCode extension tool.

### Features

- **VSCode Integration**: Native VSCode MCP support
- **JSON-RPC Communication**: Standard MCP protocol implementation
- **Tool Discovery**: Automatic tool capability advertisement
- **Error Handling**: Protocol-compliant error responses
- **Async Support**: Non-blocking operations

### MCP Protocol Implementation

```python
from client.mcp_protocol import MCPClient

# Initialize MCP client
client = MCPClient()

# List available tools
tools = await client.list_tools()

# Execute tool
result = await client.call_tool(
    name="get_prediction_markets",
    arguments={"query": "Trump election markets"}
)
```

### VSCode Integration

Add to your VSCode `settings.json`:

```json
{
  "mcp.servers": {
    "prediction-markets": {
      "command": "python",
      "args": ["client/mcp_protocol.py"],
      "cwd": "/path/to/MCP-server"
    }
  }
}
```

### Protocol Messages

#### Tool Listing

```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_prediction_markets",
        "description": "Get prediction market data",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "Natural language query"
            }
          }
        }
      }
    ]
  }
}
```

#### Tool Execution

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 2,
  "params": {
    "name": "get_prediction_markets",
    "arguments": {
      "query": "Show me Trump election markets"
    }
  }
}
```

## 🚀 Creating Custom Clients

### Base Client Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseClient(ABC):
    """Base interface for MCP clients."""

    def __init__(self, server_url: str):
        self.server_url = server_url

    @abstractmethod
    async def query(self, query: str) -> Dict[str, Any]:
        """Execute a query against the MCP server."""
        pass

    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the server."""
        pass
```

### HTTP Client Example

```python
import aiohttp
from typing import Dict, Any

class HTTPClient(BaseClient):
    """HTTP-based MCP client."""

    async def query(self, query: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.server_url}/query",
                json={"query": query}
            ) as response:
                return await response.json()

    async def list_tools(self) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.server_url}/tools"
            ) as response:
                data = await response.json()
                return data.get("available_tools", [])
```

### WebSocket Client Example

```python
import websockets
import json

class WebSocketClient(BaseClient):
    """WebSocket-based real-time MCP client."""

    async def connect(self):
        self.websocket = await websockets.connect(
            f"ws://{self.server_url.replace('http://', '')}/ws"
        )

    async def query(self, query: str) -> Dict[str, Any]:
        message = {
            "type": "query",
            "data": {"query": query}
        }
        await self.websocket.send(json.dumps(message))
        response = await self.websocket.recv()
        return json.loads(response)
```

## 🧪 Testing Clients

### CLI Client Testing

```bash
# Test basic functionality
python client/cli.py "test query"

# Test interactive mode (automated)
echo -e "test query\nquit" | python client/cli.py --interactive

# Test batch processing
echo "query1\nquery2\nquery3" > test_queries.txt
python client/cli.py --batch test_queries.txt
```

### MCP Protocol Testing

```python
import pytest
from client.mcp_protocol import MCPClient

@pytest.mark.asyncio
async def test_mcp_client():
    client = MCPClient()

    # Test tool listing
    tools = await client.list_tools()
    assert len(tools) > 0

    # Test tool execution
    result = await client.call_tool(
        "get_prediction_markets",
        {"query": "test"}
    )
    assert result["success"] == True
```

## 🔧 Client Configuration

### Environment Variables

```bash
export MCP_SERVER_URL="http://localhost:8000"
export MCP_TIMEOUT=30
export MCP_FORMAT="json"
export MCP_LOG_LEVEL="INFO"
```

### Configuration Files

#### CLI Config (`~/.mcp_cli_config.json`)

```json
{
  "server_url": "http://localhost:8000",
  "default_format": "human",
  "timeout": 30,
  "save_history": true,
  "history_limit": 1000,
  "color_output": true
}
```

#### MCP Protocol Config (`mcp_config.json`)

```json
{
  "server_url": "http://localhost:8000",
  "protocol_version": "2024-10-04",
  "capabilities": {
    "tools": true,
    "resources": false,
    "prompts": false
  }
}
```

## 📊 Client Features Comparison

| Feature                 | CLI Client | MCP Protocol | Custom HTTP | Custom WebSocket |
| ----------------------- | ---------- | ------------ | ----------- | ---------------- |
| **Interactive Mode**    | ✅         | ❌           | ➕          | ✅               |
| **VSCode Integration**  | ❌         | ✅           | ❌          | ❌               |
| **Batch Processing**    | ✅         | ❌           | ➕          | ➕               |
| **Real-time Updates**   | ❌         | ❌           | ❌          | ✅               |
| **Protocol Compliance** | ❌         | ✅           | ➕          | ➕               |
| **Ease of Use**         | ✅         | ⚖️           | ⚖️          | ⚖️               |

Legend: ✅ Built-in, ➕ Possible, ⚖️ Moderate, ❌ Not available

## 🔮 Future Client Development

### Planned Clients

- **Web Dashboard**: Browser-based GUI client
- **REST API Client**: Full REST API wrapper
- **Python SDK**: Pythonic client library
- **Jupyter Extension**: Notebook integration
- **Slack Bot**: Slack workspace integration

### Client Plugin Architecture

```python
class ClientPlugin(ABC):
    """Base class for client plugins."""

    @abstractmethod
    def process_query(self, query: str) -> str:
        """Process query before sending to server."""
        pass

    @abstractmethod
    def process_response(self, response: dict) -> dict:
        """Process response from server."""
        pass
```

## 🤝 Contributing

### Adding New Clients

1. Implement the `BaseClient` interface
2. Add comprehensive error handling
3. Include configuration support
4. Add unit and integration tests
5. Document usage examples
6. Update this README

### Client Best Practices

- **Error Handling**: Graceful failure and user-friendly errors
- **Configuration**: Support multiple configuration sources
- **Logging**: Comprehensive logging for debugging
- **Testing**: Unit tests and integration tests
- **Documentation**: Clear usage examples and API docs

---

**Multiple client interfaces provide flexibility for different use cases. Choose the right client for your needs! 🚀**
