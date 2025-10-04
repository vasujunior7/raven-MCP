# ⚙️ MCP Server Configuration

This directory contains configuration files that control the behavior of the MCP Server's natural language processing, tool routing, and response formatting.

## 📋 Configuration Files

| File                   | Purpose                          | Format | Usage                            |
| ---------------------- | -------------------------------- | ------ | -------------------------------- |
| **`keyword_map.json`** | Natural language keyword mapping | JSON   | Query parsing and categorization |
| **`defaults.json`**    | Default system settings          | JSON   | System behavior and limits       |
| **`categories.yaml`**  | Event categorization rules       | YAML   | Content classification           |

## 🧠 Keyword Mapping (`keyword_map.json`)

### Purpose

Maps natural language keywords to standardized categories, enabling the parser to understand user intent and route queries to appropriate tools.

### Structure

```json
{
  "keyword": "category",
  "keyword_phrase": "category",
  "synonym_group": "primary_category"
}
```

### Example Configuration

```json
{
  "trump": "politics",
  "biden": "politics",
  "election": "politics",
  "presidential": "politics",
  "democrat": "politics",
  "republican": "politics",

  "bitcoin": "crypto",
  "ethereum": "crypto",
  "cryptocurrency": "crypto",
  "defi": "crypto",
  "nft": "crypto",

  "sports": "sports",
  "football": "sports",
  "basketball": "sports",
  "soccer": "sports",
  "olympics": "sports",

  "technology": "tech",
  "ai": "tech",
  "artificial intelligence": "tech",
  "machine learning": "tech",
  "blockchain": "tech"
}
```

### Usage in Query Processing

```python
# User query: "Show me Trump election markets"
# Keyword extraction: ["trump", "election", "markets"]
# Category mapping: "trump" → "politics", "election" → "politics"
# Result category: "politics"
```

### Adding New Keywords

1. **Identify Category**: Determine which category the keyword belongs to
2. **Add Mapping**: Add the keyword-to-category mapping
3. **Test**: Verify the keyword is properly recognized
4. **Document**: Update this README with new keyword groups

Example:

```json
{
  "climate": "environment",
  "global warming": "environment",
  "carbon": "environment",
  "renewable energy": "environment"
}
```

## 🎛️ Default Settings (`defaults.json`)

### Purpose

Defines default system behaviors, limits, timeouts, and other operational parameters.

### Structure

```json
{
  "parser": {
    "default_limit": 5,
    "max_limit": 50,
    "default_category": "general"
  },
  "executor": {
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1.0
  },
  "server": {
    "host": "localhost",
    "port": 8000,
    "debug": false
  }
}
```

### Complete Configuration Example

```json
{
  "parser": {
    "default_limit": 5,
    "max_limit": 50,
    "min_limit": 1,
    "default_category": "general",
    "enable_fuzzy_matching": true,
    "fuzzy_threshold": 0.8
  },
  "router": {
    "tool_selection_strategy": "best_match",
    "enable_fallback": true,
    "confidence_threshold": 0.7
  },
  "executor": {
    "default_timeout": 30,
    "max_timeout": 120,
    "max_retries": 3,
    "retry_delay": 1.0,
    "retry_backoff": "exponential",
    "max_concurrent": 10
  },
  "postprocessor": {
    "enable_filtering": true,
    "quality_threshold": 0.5,
    "enable_enrichment": true,
    "add_metadata": true
  },
  "server": {
    "host": "localhost",
    "port": 8000,
    "debug": false,
    "cors_enabled": true,
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 60
    }
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/mcp_server.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```

### Configuration Sections

#### Parser Settings

- **`default_limit`**: Default number of results to return
- **`max_limit`**: Maximum allowed results per query
- **`default_category`**: Fallback category for unrecognized queries
- **`enable_fuzzy_matching`**: Enable fuzzy keyword matching
- **`fuzzy_threshold`**: Minimum similarity score for fuzzy matches

#### Router Settings

- **`tool_selection_strategy`**: How to select tools ("best_match", "round_robin", "random")
- **`enable_fallback`**: Whether to use fallback tools when primary fails
- **`confidence_threshold`**: Minimum confidence for tool selection

#### Executor Settings

- **`default_timeout`**: Default timeout for tool execution
- **`max_retries`**: Maximum retry attempts for failed executions
- **`retry_delay`**: Base delay between retries (seconds)
- **`retry_backoff`**: Retry strategy ("linear", "exponential")

#### Server Settings

- **`host`**: Server bind address
- **`port`**: Server port number
- **`debug`**: Enable debug mode
- **`cors_enabled`**: Enable CORS for web clients

## 📊 Categories Configuration (`categories.yaml`)

### Purpose

Defines hierarchical categorization rules for content classification and organization.

### Structure

```yaml
categories:
  politics:
    description: "Political events and elections"
    keywords: ["election", "politics", "government"]
    subcategories:
      elections:
        description: "Electoral processes and campaigns"
        keywords: ["election", "campaign", "voting"]
      policy:
        description: "Government policies and legislation"
        keywords: ["policy", "law", "regulation"]

  crypto:
    description: "Cryptocurrency and blockchain"
    keywords: ["bitcoin", "crypto", "blockchain"]
    subcategories:
      defi:
        description: "Decentralized finance"
        keywords: ["defi", "yield", "liquidity"]
```

### Complete Categories Example

```yaml
categories:
  politics:
    description: "Political events, elections, and governance"
    keywords: ["election", "politics", "government", "policy"]
    color: "#FF6B6B"
    icon: "🏛️"
    subcategories:
      elections:
        description: "Electoral processes and campaigns"
        keywords: ["election", "campaign", "voting", "candidate"]
      policy:
        description: "Government policies and legislation"
        keywords: ["policy", "law", "regulation", "bill"]
      international:
        description: "International relations and diplomacy"
        keywords: ["international", "diplomacy", "treaty", "summit"]

  crypto:
    description: "Cryptocurrency, blockchain, and digital assets"
    keywords: ["bitcoin", "crypto", "blockchain", "ethereum"]
    color: "#4ECDC4"
    icon: "₿"
    subcategories:
      defi:
        description: "Decentralized finance protocols and yields"
        keywords: ["defi", "yield", "liquidity", "protocol"]
      nft:
        description: "Non-fungible tokens and digital collectibles"
        keywords: ["nft", "collectible", "digital art", "opensea"]

  sports:
    description: "Sports events, betting, and competitions"
    keywords: ["sports", "game", "match", "tournament"]
    color: "#45B7D1"
    icon: "⚽"
    subcategories:
      football:
        description: "American football events and betting"
        keywords: ["football", "nfl", "super bowl"]
      basketball:
        description: "Basketball games and tournaments"
        keywords: ["basketball", "nba", "march madness"]

  technology:
    description: "Technology trends, AI, and innovation"
    keywords: ["technology", "tech", "ai", "innovation"]
    color: "#96CEB4"
    icon: "🚀"
    subcategories:
      ai:
        description: "Artificial intelligence and machine learning"
        keywords: ["ai", "machine learning", "neural network"]
      startup:
        description: "Startup companies and venture capital"
        keywords: ["startup", "venture", "ipo", "funding"]
```

### Usage in Classification

```python
# Content: "Will OpenAI release GPT-5 in 2025?"
# Keywords: ["openai", "gpt-5", "ai", "release"]
# Category match: "technology" → "ai"
# Classification: {"category": "technology", "subcategory": "ai"}
```

## 🔧 Configuration Management

### Loading Configuration

```python
import json
import yaml
from pathlib import Path

class ConfigManager:
    def __init__(self, config_dir: Path = Path("config")):
        self.config_dir = config_dir
        self.keyword_map = self.load_keyword_map()
        self.defaults = self.load_defaults()
        self.categories = self.load_categories()

    def load_keyword_map(self) -> dict:
        with open(self.config_dir / "keyword_map.json") as f:
            return json.load(f)

    def load_defaults(self) -> dict:
        with open(self.config_dir / "defaults.json") as f:
            return json.load(f)

    def load_categories(self) -> dict:
        with open(self.config_dir / "categories.yaml") as f:
            return yaml.safe_load(f)
```

### Environment Overrides

Configuration can be overridden with environment variables:

```bash
# Override default port
export MCP_SERVER_PORT=8001

# Override debug mode
export MCP_DEBUG=true

# Override timeout
export MCP_EXECUTOR_TIMEOUT=60
```

### Dynamic Configuration

```python
# Update configuration at runtime
config_manager.update_defaults({
    "executor": {
        "timeout": 60,
        "max_retries": 5
    }
})

# Add new keyword mappings
config_manager.add_keywords({
    "web3": "crypto",
    "metaverse": "tech"
})
```

## 🧪 Configuration Testing

### Validation Scripts

```python
# config/validate_config.py
def validate_keyword_map(keyword_map: dict) -> bool:
    """Validate keyword mapping configuration."""
    for keyword, category in keyword_map.items():
        if not isinstance(keyword, str) or not isinstance(category, str):
            return False
        if len(keyword.strip()) == 0 or len(category.strip()) == 0:
            return False
    return True

def validate_defaults(defaults: dict) -> bool:
    """Validate default settings configuration."""
    required_sections = ["parser", "executor", "server"]
    for section in required_sections:
        if section not in defaults:
            return False
    return True
```

### Configuration Tests

```bash
# Test configuration validity
python config/validate_config.py

# Test keyword mapping
python -c "
from core.parser import QueryParser
parser = QueryParser()
result = parser.parse_query('Trump election markets')
print(f'Category: {result[\"keyword\"]}')
"
```

## 🔄 Configuration Updates

### Version Control

Keep configuration in version control but allow local overrides:

```
config/
├── keyword_map.json          # Tracked
├── defaults.json             # Tracked
├── categories.yaml           # Tracked
├── keyword_map.local.json    # Ignored (.gitignore)
├── defaults.local.json       # Ignored (.gitignore)
└── categories.local.yaml     # Ignored (.gitignore)
```

### Migration Scripts

```python
# config/migrate_config.py
def migrate_v1_to_v2(old_config: dict) -> dict:
    """Migrate configuration from v1 to v2 format."""
    new_config = old_config.copy()

    # Add new required fields
    if "postprocessor" not in new_config:
        new_config["postprocessor"] = {
            "enable_filtering": True,
            "quality_threshold": 0.5
        }

    return new_config
```

### Hot Reloading

```python
import watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigReloader(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.json') or event.src_path.endswith('.yaml'):
            print(f"Reloading configuration: {event.src_path}")
            # Reload configuration
            config_manager.reload()
```

## 🔮 Advanced Configuration

### Environment-Specific Configs

```
config/
├── base/                     # Base configuration
│   ├── keyword_map.json
│   └── defaults.json
├── development/              # Development overrides
│   └── defaults.json
├── production/               # Production overrides
│   └── defaults.json
└── testing/                  # Testing overrides
    └── defaults.json
```

### Feature Flags

```json
{
  "features": {
    "experimental_parser": false,
    "advanced_routing": true,
    "ml_categorization": false,
    "async_processing": true
  }
}
```

### Custom Validators

```python
class ConfigValidator:
    def validate_timeout(self, timeout: int) -> bool:
        return 1 <= timeout <= 300

    def validate_limit(self, limit: int) -> bool:
        return 1 <= limit <= 100

    def validate_category(self, category: str) -> bool:
        return category in self.valid_categories
```

## 🤝 Contributing

### Adding New Configuration

1. **Define Schema**: Document the configuration structure
2. **Add Validation**: Implement validation functions
3. **Update Defaults**: Provide sensible default values
4. **Add Tests**: Test configuration loading and validation
5. **Document**: Update this README with new options

### Configuration Best Practices

- **Sensible Defaults**: Provide defaults that work out of the box
- **Validation**: Validate configuration on startup
- **Documentation**: Document all configuration options
- **Environment Support**: Support environment variable overrides
- **Backward Compatibility**: Maintain compatibility across versions

---

**Proper configuration enables the MCP Server to adapt to different use cases and environments. Configure once, run everywhere! ⚙️**
