# 🧠 Raven MCP Server

A sophisticated Model Context Protocol (MCP) server providing natural language access to Polymarket prediction markets and cryptocurrency data with enhanced typo tolerance and fuzzy matching.

## ✨ Features

### 🎯 **Natural Language Processing**
- **Typo Tolerance**: Handles common misspellings like "cryptp" → "crypto", "poltics" → "politics"
- **Fuzzy Matching**: Uses advanced string matching for better understanding
- **Phrase Normalization**: Converts "fetch me crypto events" → "crypto events"
- **Smart Routing**: Prioritizes explicit tool mentions and context

### 📊 **Data Sources**
- **Polymarket API**: Real-time prediction market data with tag-based filtering
- **Sports Markets**: Tag ID `100381` - MLB, NBA, NFL events with real trading volumes
- **Politics Markets**: Tag ID `21` - Election and political prediction markets  
- **Crypto Markets**: Tag ID `15` - Cryptocurrency-related prediction markets

### 🔧 **Technical Features**
- **Pagination Support**: `limit` and `offset` parameters for large datasets
- **Caching System**: 15-minute TTL for optimal performance
- **Error Handling**: Graceful fallbacks and comprehensive error messages
- **MCP Inspector Compatible**: Full support for hosted testing

## 🚀 Quick Start

### Local CLI Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Test basic functionality
python client/cli.py "sports events limit 3"
python client/cli.py "fetch me poltics events"  # Handles typos!
python client/cli.py "crypto events limit 2 offset 5"

# Test parser improvements
python test_parser_improvements.py
```

### 🔍 MCP Inspector Setup

#### Option 1: Direct Python Execution
```bash
# Install MCP dependencies
pip install mcp

# Run MCP server for Inspector
python mcp_server.py
```

#### Option 2: Package.json Configuration
Add to your MCP Inspector configuration:
```json
{
  "mcpServers": {
    "raven-mcp": {
      "command": "python",
      "args": ["path/to/raven-mcp/mcp_server.py"],
      "env": {}
    }
  }
}
```

#### Option 3: NPM-style (if using Node.js tools)
```bash
npm install  # Installs package.json
npm start    # Runs MCP server
```

## 📖 Usage Examples

### 🎯 **Supported Query Patterns**

#### Sports Events
```bash
# Perfect spelling
"sports events limit 5"
"get sports events"
"show me NBA games"

# Natural language variations  
"fetch me sports events"
"give me some sports events"
"find sports events today"
```

#### Politics Markets
```bash
# Perfect spelling
"politics events limit 3"
"political prediction markets"

# Typo tolerance
"poltics events"           # ✅ Works!
"politcs events"          # ✅ Works!
"fetch me poltics events" # ✅ Works!
```

#### Crypto Markets
```bash
# Perfect spelling
"crypto events"
"cryptocurrency markets"

# Typo tolerance  
"cryptp events"           # ✅ Works!
"cryto events limit 5"    # ✅ Works!
"fetch me cryptp events"  # ✅ Works!
```

### 📊 **Sample Outputs**

#### Sports Events Response
```
✅ Found 3 results:

Title        | Enddate     | Volume   | Tags     | Url                   
-------------|-------------|----------|----------|-----------------------
Phillies ... | 2025-10-09  | 144.1K   | sports   | https://polymarket...
Blue Jays... | 2025-10-08  | 4.0K     | sports   | https://polymarket...
Brewers v... | 2025-10-08  | 91.4K    | sports   | https://polymarket...
```

#### Politics Events Response  
```
✅ Found 2 results:

Title              | Enddate  | Volume   | Tags       | Url                
-------------------|----------|----------|------------|--------------------
Election Outcome   | 2025-... | 125.5K   | politics   | https://polymarket...
Senate Control     | 2025-... | 89.2K    | politics   | https://polymarket...
```

## 🛠️ **MCP Inspector Integration**

### Available Tools
- **`get_events`**: Fetch prediction market events with natural language queries

### Tool Parameters
```json
{
  "query": "string (required) - Natural language query", 
  "keyword": "enum [sports, politics, crypto] - Category filter",
  "limit": "integer (1-50, default: 5) - Results count",
  "offset": "integer (min: 0, default: 0) - Pagination offset"
}
```

### Example MCP Calls
```json
// Basic sports query
{
  "name": "get_events",
  "arguments": {
    "query": "sports events",
    "limit": 3
  }
}

// Politics with pagination  
{
  "name": "get_events", 
  "arguments": {
    "query": "politics events",
    "keyword": "politics",
    "limit": 5,
    "offset": 10
  }
}

// Typo tolerance test
{
  "name": "get_events",
  "arguments": {
    "query": "fetch me cryptp events"
  }
}
```

## 🔧 **Configuration**

### Keyword Mappings (`config/keyword_map.json`)
```json
{
  "politics": "politics",
  "poltics": "politics",    // Typo support
  "politcs": "politics",    // Typo support
  "crypto": "crypto", 
  "cryptp": "crypto",       // Typo support
  "cryto": "crypto",        // Typo support
  "sports": "sports"
}
```

### API Configuration
- **Polymarket Base URL**: `https://gamma-api.polymarket.com`
- **Cache TTL**: 15 minutes for market data
- **Request Timeout**: 30 seconds
- **Pagination**: Up to 50 results per request

## 📈 **Performance Features**

### Caching Strategy
- **Subgraph Cache**: `polymarket::tag:{category}::{query_hash}`
- **TTL**: 900 seconds (15 minutes) 
- **Smart Invalidation**: Respects pagination parameters

### Error Handling
- **API Fallbacks**: Events → Markets API if events fail
- **Graceful Degradation**: Returns empty results instead of errors
- **Typo Recovery**: Fuzzy matching with 80% confidence threshold

## 🧪 **Testing**

### Parser Testing
```bash
# Test typo tolerance and fuzzy matching
python test_parser_improvements.py

# Test specific cases
python -c "from core.parser import QueryParser; parser = QueryParser(); print(parser.parse('fetch me cryptp events'))"
```

### API Testing  
```bash
# Test real API integration
python verify_real_api.py
python quick_api_test.py
```

### Manual CLI Testing
```bash
# Test various input patterns
python client/cli.py "fetch me cryptp events"    # Typo tolerance
python client/cli.py "sports events limit 2"     # Basic functionality  
python client/cli.py "poltics prediction"        # Complex typo handling
```

## 🚨 **Troubleshooting**

### Common Issues

1. **"Unsupported category" errors**: 
   - ✅ **Fixed!** Enhanced parser now handles typos and variations

2. **Wrong tool routing (crypto → LunarCrush)**:
   - ✅ **Fixed!** Improved priority matching and explicit tool detection

3. **MCP Inspector connection issues**:
   - Ensure `pip install mcp` is completed
   - Check Python path in MCP configuration
   - Verify no port conflicts

### Debug Commands
```bash
# Check parser behavior
python -c "from core.parser import QueryParser; parser = QueryParser(); print(parser._extract_keyword('your query here'))"

# Verify API connectivity  
python -c "import asyncio; from tools.polymarket_fetcher import PolymarketFetcher; asyncio.run(PolymarketFetcher().execute({'keyword': 'sports', 'limit': 1}))"
```

## 📝 **API Reference**

### Endpoints Used
- `GET /events?tag_id={id}&limit={n}&offset={n}&closed=false&order=id&ascending=false`
- `GET /markets?tag_id={id}&limit={n}&offset={n}&closed=false&order=id&ascending=false`
- `GET /tags` (for tag discovery)
- `GET /sports` (for sports tag metadata)

### Tag IDs
- **Sports**: `100381`
- **Politics**: `21` 
- **Crypto**: `15`

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Test your changes: `python test_parser_improvements.py`
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Open Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 **Acknowledgments**

- **Polymarket API**: For real-time prediction market data
- **FuzzyWuzzy**: For excellent fuzzy string matching
- **MCP Protocol**: For standardized AI tool integration

---

**🎯 Ready to explore prediction markets with natural language? Start with: `python client/cli.py "sports events limit 3"`**