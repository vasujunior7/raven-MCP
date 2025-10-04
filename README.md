# 🧠 MCP Server — End-to-End Architecture

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](tests/)
[![LLM Integration](https://img.shields.io/badge/LLM-Raven%20Model-purple.svg)](raven_client.py)

A modular **Model Context Protocol (MCP) Server** that converts natural language queries into structured tool invocations, executes them against external APIs (like Polymarket), and returns normalized JSON responses. **Fully integrated with custom LLM (Raven Reasoning Model) for intelligent query processing.**

## ✨ Key Features

- 🧠 **LLM Integration**: Full integration with Raven Reasoning Model for intelligent analysis
- 🗣️ **Natural Language Processing**: Convert free-form queries into structured tool parameters
- 🔧 **Pluggable Tool Architecture**: Easy addition of new data sources and APIs
- 👥 **Multiple Client Interfaces**: CLI, VSCode MCP integration, HTTP REST API
- 🔄 **Async Architecture**: High-performance async/await throughout
- 🛡️ **Robust Error Handling**: Retry logic, timeout management, and graceful degradation
- ⚙️ **Configurable System**: Keyword mapping, filters, and category-based organization
- 🧪 **Comprehensive Testing**: Full test suite with debugging capabilities
- 📊 **OpenAI Compatible**: Function calling format for seamless LLM integration

## 🚀 Current Status

✅ **Production Ready** - All components implemented and tested

| Component             | Status      | Description                           |
| --------------------- | ----------- | ------------------------------------- |
| **MCP Server**        | ✅ Complete | Core server with all modules          |
| **HTTP Server**       | ✅ Complete | REST API wrapper with all endpoints   |
| **LLM Integration**   | ✅ Complete | Raven Reasoning Model integration     |
| **Tool System**       | ✅ Complete | Polymarket API integration            |
| **Client Interfaces** | ✅ Complete | CLI and MCP protocol clients          |
| **Testing Suite**     | ✅ Complete | Comprehensive test coverage           |
| **Documentation**     | ✅ Complete | Full documentation for all components |

## 🎯 Features

- **Natural Language Processing**: Convert free-form queries into structured tool parameters
- **Pluggable Tool Architecture**: Easy addition of new data sources and APIs
- **Multiple Client Interfaces**: CLI, VSCode integration, and web dashboard support
- **Robust Error Handling**: Retry logic, timeout management, and graceful degradation
- **Configurable Filtering**: Keyword mapping, time filters, and category-based organization
- **Production Ready**: Async architecture, logging, and monitoring capabilities

## 🏗️ Architecture

```
User Query → MCP Client → JSON Request → MCP Server
                                           ↓
┌─────────────────────────────────────────────────┐
│ Input Understanding Layer (parser)              │
│  • Parse NL query → keyword + limit             │
├─────────────────────────────────────────────────┤
│ Tool Invocation Layer (router)                  │
│  • get_events(keyword, limit)                   │
├─────────────────────────────────────────────────┤
│ Execution & Post-Processing Layer (executor)    │
│  • Fetch External APIs                          │
│  • Filter + Clean JSON                          │
└─────────────────────────────────────────────────┘
                          ↓
              [Normalized JSON Response]
```

## 📁 Project Structure

```
mcp_server/
├── main.py                 # Main server entry point
├── core/                   # Core architectural components
│   ├── parser.py           # Natural language understanding
│   ├── router.py           # Tool routing and discovery
│   ├── executor.py         # Tool execution and API calls
│   └── postprocess.py      # Response cleaning and normalization
├── tools/                  # Pluggable tool implementations
│   └── polymarket_fetcher.py  # Polymarket API integration
├── config/                 # Configuration files
│   ├── keyword_map.json    # NL keyword to category mapping
│   ├── defaults.json       # Default settings
│   └── categories.yaml     # Event categorization rules
├── client/                 # Client interfaces
│   └── cli.py             # Command-line interface
├── tests/                  # Test suite and verification scripts
│   ├── run_tests.py       # Test runner with menu
│   ├── test_mcp_llm.py    # Main integration test
│   ├── test_detailed.py   # Detailed debugging test
│   └── README.md          # Test documentation
├── utils/                  # Utility modules
│   ├── logger.py          # Logging configuration
│   ├── http.py            # HTTP client with retry logic
│   └── formatter.py       # Response formatting
└── requirements.txt        # Python dependencies
```

## 🚀 Quick Start

### Installation

1. **Clone and navigate to the project:**

   ```bash
   cd MCP-server
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your LLM credentials
   ```

### Running the Server

**HTTP Server Mode (Recommended):**

```bash
python server.py --port 8001
```

**Direct MCP Server:**

```bash
python main.py
```

### Using the System

**Interactive CLI Mode:**

```bash
python client/cli.py --interactive
```

**Single Query:**

```bash
python client/cli.py "Show me 3 Trump election events"
```

**LLM Integration (Raven Model):**

```bash
python raven_client.py
# Ask: "What are the latest Trump election prediction markets?"
```

**REST API:**

```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me 5 crypto predictions"}'
```

## 💬 Example Queries

The system understands natural language queries and automatically extracts parameters:

```bash
# Sports events
"Fetch me sports events"
"Show 3 basketball games"

# Political predictions
"Give me Trump election markets"
"Find 5 political events today"

# Cryptocurrency
"Get crypto events"
"Show Bitcoin price predictions"

# Technology
"Find AI technology events"
"Show 3 tech predictions this week"
```

## 🔧 Query Processing Flow

1. **Input Understanding**: `"Show 3 Trump election events"`

   - Extracts: `limit=3`, `keyword="politics"`, `tool="get_events"`

2. **Tool Routing**: Routes to `PolymarketFetcher`

3. **Execution**: Fetches from Polymarket API with filtering

4. **Post-Processing**:

   - Cleans and validates data
   - Applies keyword filtering
   - Enriches with metadata (tags, volume, dates)
   - Normalizes JSON structure

5. **Response**: Returns structured JSON:
   ```json
   [
     {
       "title": "Will Donald Trump win the 2024 US Presidential Election?",
       "endDate": "2025-11-05T23:59:59Z",
       "volume": 150000.0,
       "tags": ["politics", "election"],
       "source": "polymarket"
     }
   ]
   ```

## 🛠️ CLI Commands

**Interactive Mode Commands:**

```bash
>>> Show me sports events                    # Natural language query
>>> /format cards                           # Change output format
>>> /tools                                  # List available tools
>>> /help                                   # Show help
>>> quit                                    # Exit
```

**Output Formats:**

- `table` - Tabular format (default)
- `cards` - Detailed card view
- `json` - Raw JSON output
- `summary` - Brief summary with statistics

## 🔌 Adding New Tools

Create a new tool in the `tools/` directory:

```python
class CustomTool:
    tool_name = "custom_tool"
    description = "Description of what this tool does"

    async def execute(self, params):
        # Tool implementation
        return results
```

The router automatically discovers and registers new tools.

## ⚙️ Configuration

**Keyword Mapping** (`config/keyword_map.json`):

```json
{
  "trump": "politics",
  "sports": "sports",
  "bitcoin": "crypto"
}
```

**Default Settings** (`config/defaults.json`):

```json
{
  "default_limit": 5,
  "max_limit": 50,
  "timeout": 30
}
```

## 📚 Documentation

### Component Documentation

Each component has detailed documentation in its respective directory:

| Component                 | Documentation                          | Description                             |
| ------------------------- | -------------------------------------- | --------------------------------------- |
| **🧩 Core Architecture**  | [`core/README.md`](core/README.md)     | Parser, router, executor, postprocessor |
| **🔧 Tools & Extensions** | [`tools/README.md`](tools/README.md)   | Available tools and development guide   |
| **👥 Client Interfaces**  | [`client/README.md`](client/README.md) | CLI, MCP protocol, custom clients       |
| **⚙️ Configuration**      | [`config/README.md`](config/README.md) | Keyword mapping, defaults, categories   |
| **🧪 Testing Suite**      | [`tests/README.md`](tests/README.md)   | Test documentation and usage            |

### Quick Navigation

- **Getting Started**: See [Quick Start](#-quick-start) section above
- **Adding Tools**: Read [`tools/README.md`](tools/README.md)
- **Testing**: Read [`tests/README.md`](tests/README.md) and run `cd tests && python run_tests.py`
- **LLM Integration**: See [Testing](#-testing) section for Raven model setup
- **Configuration**: Read [`config/README.md`](config/README.md)

### API Reference

#### REST API Endpoints

| Endpoint     | Method | Description                    | Example                        |
| ------------ | ------ | ------------------------------ | ------------------------------ |
| `/health`    | GET    | Server health check            | `GET /health`                  |
| `/tools`     | GET    | List available tools           | `GET /tools`                   |
| `/mcp/tools` | GET    | OpenAI tool definitions        | `GET /mcp/tools`               |
| `/query`     | POST   | Process natural language query | `POST /query {"query": "..."}` |

#### Response Formats

**Query Response:**

```json
{
  "success": true,
  "results": [...],
  "count": 3,
  "query_info": {
    "keyword": "politics",
    "limit": 3,
    "tool_used": "polymarket_fetcher"
  }
}
```

**Tool Definitions Response:**

```json
{
  "success": true,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_prediction_markets",
        "description": "Get prediction market data...",
        "parameters": {...}
      }
    }
  ]
}
```

## 🎯 Use Cases

- **Market Research**: Query prediction markets for trend analysis
- **Content Curation**: Find relevant events for news or analysis
- **Dashboard Feeds**: Populate dashboards with real-time market data
- **Research Tools**: Academic or financial research data gathering
- **Automated Monitoring**: Track specific topics or market movements

## 🔮 Future Expansions

The pluggable architecture supports easy addition of:

- **LunarCrush API**: Social sentiment and Galaxy scores
- **Twitter API**: Real-time public opinion analysis
- **Custom ML Models**: Forecasting and reasoning capabilities
- **Additional Markets**: Other prediction platforms
- **Time Series Analysis**: Historical trend analysis

## 📊 System Benefits

- ✅ **Modular Design**: Easy to extend and maintain
- ✅ **Natural Language Interface**: No API knowledge required
- ✅ **Multiple Output Formats**: Adaptable to different clients
- ✅ **Robust Error Handling**: Production-ready reliability
- ✅ **Configurable Filtering**: Flexible query interpretation
- ✅ **Async Architecture**: High performance and scalability

## � Testing

The project includes a comprehensive test suite in the `tests/` folder:

### Quick Testing

```bash
# Start the MCP server first
python server.py --port 8001

# Run the main integration test
cd tests
python test_mcp_llm.py
```

### Test Runner

```bash
cd tests

# Show available tests
python run_tests.py

# Run specific test
python run_tests.py 6    # MCP+LLM integration test
python run_tests.py 1    # Architecture demo
```

### Available Tests

- **`test_mcp_llm.py`** - ⭐ Main integration test (MCP + LLM)
- **`test_detailed.py`** - Detailed debugging test
- **`test_endpoints.py`** - REST API endpoint tests
- **`architecture_demo.py`** - System architecture demo

See `tests/README.md` for detailed testing documentation.

## �🤝 Contributing

1. Add new tools to `tools/` directory
2. Update keyword mappings in `config/keyword_map.json`
3. Add configuration options to `config/defaults.json`
4. Test with the CLI interface

---

**Built for extensibility, designed for simplicity, optimized for intelligence. 🧠**
# Raven-mcp
