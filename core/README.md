# 🧩 MCP Server Core Architecture

This directory contains the core architectural components that power the MCP Server's natural language understanding and tool execution capabilities.

## 📋 Core Components

| Component         | File             | Purpose                        | Responsibilities                    |
| ----------------- | ---------------- | ------------------------------ | ----------------------------------- |
| **Parser**        | `parser.py`      | Natural Language Understanding | Query parsing, parameter extraction |
| **Router**        | `router.py`      | Tool Discovery & Routing       | Tool selection, capability matching |
| **Executor**      | `executor.py`    | Tool Execution Engine          | Async execution, error handling     |
| **Postprocessor** | `postprocess.py` | Response Processing            | Data cleaning, normalization        |

## 🔄 Processing Pipeline

```
User Query → Parser → Router → Executor → Postprocessor → Response
     ↓          ↓        ↓         ↓           ↓
"Show 3 Trump" → Extract → Select → Execute → Clean → JSON
  politics      params   tool     tool      data    output
```

## 🧠 Parser (`parser.py`)

### Purpose

Converts natural language queries into structured parameters that tools can understand.

### Key Features

- **Keyword Extraction**: Maps natural language to tool parameters
- **Parameter Detection**: Identifies limits, filters, and constraints
- **Category Mapping**: Uses configurable keyword-to-category mapping
- **Intelligent Defaults**: Applies sensible defaults when parameters are missing

### Example

```python
from core.parser import QueryParser

parser = QueryParser()
result = parser.parse_query("Show me 5 Trump election markets")

# Result:
{
    "keyword": "politics",
    "limit": 5,
    "original_query": "Show me 5 Trump election markets",
    "extracted_terms": ["trump", "election", "markets"],
    "tool_hint": "prediction_markets"
}
```

### Configuration

Uses `config/keyword_map.json` for keyword-to-category mapping:

```json
{
  "trump": "politics",
  "biden": "politics",
  "sports": "sports",
  "bitcoin": "crypto"
}
```

## 🧭 Router (`router.py`)

### Purpose

Determines which tool should handle a parsed query based on capabilities and context.

### Key Features

- **Tool Discovery**: Automatically finds available tools
- **Capability Matching**: Matches query requirements to tool capabilities
- **Load Balancing**: Can distribute load across multiple tool instances
- **Fallback Logic**: Handles cases where no perfect match exists

### Example

```python
from core.router import ToolRouter

router = ToolRouter()
tool_selection = router.route_query({
    "keyword": "politics",
    "limit": 5,
    "tool_hint": "prediction_markets"
})

# Result:
{
    "selected_tool": "polymarket_fetcher",
    "confidence": 0.95,
    "reasoning": "High match for prediction markets + politics",
    "fallback_tools": ["news_fetcher", "twitter_analyzer"]
}
```

### Tool Registration

Tools are automatically discovered and registered:

```python
# Automatic discovery from /tools directory
router.discover_tools()

# Manual registration (if needed)
router.register_tool("custom_tool", CustomTool())
```

## ⚡ Executor (`executor.py`)

### Purpose

Executes selected tools with proper error handling, timeouts, and retry logic.

### Key Features

- **Async Execution**: Non-blocking tool execution
- **Timeout Management**: Configurable timeouts per tool
- **Retry Logic**: Automatic retries with exponential backoff
- **Error Handling**: Graceful failure and error reporting
- **Resource Management**: Connection pooling and cleanup

### Example

```python
from core.executor import ToolExecutor

executor = ToolExecutor()
result = await executor.execute_tool(
    tool_name="polymarket_fetcher",
    parameters={"keyword": "politics", "limit": 5},
    timeout=30
)

# Result:
{
    "success": True,
    "results": [...],
    "execution_time": 2.3,
    "tool_used": "polymarket_fetcher",
    "retry_count": 0
}
```

### Configuration

```python
# config/defaults.json
{
    "executor": {
        "default_timeout": 30,
        "max_retries": 3,
        "retry_delay": 1.0,
        "max_concurrent": 10
    }
}
```

## 🧹 Postprocessor (`postprocess.py`)

### Purpose

Cleans, validates, and normalizes raw tool outputs into consistent response formats.

### Key Features

- **Data Validation**: Ensures response format consistency
- **Content Filtering**: Removes inappropriate or irrelevant content
- **Enrichment**: Adds metadata, tags, and computed fields
- **Format Standardization**: Converts various formats to standard JSON
- **Quality Control**: Validates data quality and completeness

### Example

```python
from core.postprocess import ResponseProcessor

processor = ResponseProcessor()
cleaned_response = processor.process_response(
    raw_data=tool_output,
    query_context={"keyword": "politics", "limit": 5}
)

# Result:
{
    "success": True,
    "results": [
        {
            "id": "standardized_id",
            "title": "Clean Title",
            "category": "politics",
            "tags": ["election", "politics"],
            "metadata": {
                "processed_at": "2025-10-04T15:30:00Z",
                "quality_score": 0.92
            }
        }
    ],
    "count": 1,
    "processing_info": {
        "filters_applied": ["keyword_filter", "quality_filter"],
        "original_count": 3,
        "filtered_count": 1
    }
}
```

### Processing Steps

1. **Validation**: Check required fields and data types
2. **Filtering**: Apply keyword and quality filters
3. **Enrichment**: Add tags, categories, and metadata
4. **Normalization**: Standardize field names and formats
5. **Quality Scoring**: Assign relevance and quality scores

## 🔧 Architecture Patterns

### Dependency Injection

Components can be easily swapped or extended:

```python
# Custom parser implementation
class CustomParser(QueryParser):
    def parse_query(self, query: str) -> dict:
        # Custom parsing logic
        return enhanced_parsing_result

# Use custom parser
server = MCPServer(parser=CustomParser())
```

### Plugin Architecture

New components can be added without modifying core code:

```python
# Register custom postprocessor
server.register_postprocessor("custom", CustomPostprocessor())
```

### Configuration-Driven

All components use external configuration:

```python
# Components automatically load config
parser = QueryParser()  # Loads config/keyword_map.json
executor = ToolExecutor()  # Loads config/defaults.json
```

## 🧪 Testing Core Components

### Unit Testing

Each component has comprehensive unit tests:

```bash
# Test individual components
python -m pytest tests/core/test_parser.py
python -m pytest tests/core/test_router.py
python -m pytest tests/core/test_executor.py
python -m pytest tests/core/test_postprocess.py
```

### Integration Testing

Test component interactions:

```python
# Full pipeline test
async def test_full_pipeline():
    parser = QueryParser()
    router = ToolRouter()
    executor = ToolExecutor()
    processor = ResponseProcessor()

    # Parse query
    parsed = parser.parse_query("Show 3 Trump markets")

    # Route to tool
    routing = router.route_query(parsed)

    # Execute tool
    result = await executor.execute_tool(
        routing["selected_tool"],
        parsed
    )

    # Process response
    final = processor.process_response(result, parsed)

    assert final["success"] == True
    assert len(final["results"]) <= 3
```

## 🔮 Extension Points

### Custom Parsers

Add domain-specific parsing logic:

```python
class FinancialParser(QueryParser):
    def extract_financial_terms(self, query: str):
        # Extract stock symbols, financial metrics, etc.
        pass
```

### Custom Routers

Implement sophisticated routing strategies:

```python
class MLRouter(ToolRouter):
    def route_query(self, parsed_query: dict):
        # Use ML model to predict best tool
        prediction = self.ml_model.predict(parsed_query)
        return self.select_tool_from_prediction(prediction)
```

### Custom Executors

Add specialized execution capabilities:

```python
class CachedExecutor(ToolExecutor):
    async def execute_tool(self, tool_name: str, params: dict):
        # Check cache first
        cached = await self.cache.get(tool_name, params)
        if cached:
            return cached

        # Execute and cache result
        result = await super().execute_tool(tool_name, params)
        await self.cache.set(tool_name, params, result)
        return result
```

## 📊 Performance Considerations

### Async Architecture

All components support async operations for maximum performance:

```python
# Concurrent execution
results = await asyncio.gather(
    executor.execute_tool("tool1", params1),
    executor.execute_tool("tool2", params2),
    executor.execute_tool("tool3", params3)
)
```

### Caching Strategy

Components support multiple caching layers:

- **Parser Cache**: Parsed query results
- **Router Cache**: Tool selection decisions
- **Executor Cache**: Tool execution results
- **Postprocessor Cache**: Processed responses

### Resource Management

Proper resource cleanup and connection pooling:

```python
async with ToolExecutor() as executor:
    result = await executor.execute_tool("tool", params)
    # Automatic cleanup
```

## 🤝 Contributing

### Adding New Components

1. Implement the component interface
2. Add comprehensive unit tests
3. Update integration tests
4. Document the component API
5. Add configuration examples

### Modifying Existing Components

1. Maintain backward compatibility
2. Add deprecation warnings for breaking changes
3. Update all related tests
4. Document migration paths

---

**The core architecture is designed for extensibility, performance, and maintainability. Each component can be independently tested, configured, and extended! 🚀**
