# 🧪 MCP Server Test Suite

This directory contains comprehensive tests for the MCP Server architecture, including integration tests, endpoint validation, and LLM integration verification.

## 📋 Test Overview

### 🎯 Main Integration Tests

| Test File                | Description                                             | Usage                       |
| ------------------------ | ------------------------------------------------------- | --------------------------- |
| **`test_mcp_llm.py`**    | ⭐ **Primary integration test** - Full MCP + LLM system | `python test_mcp_llm.py`    |
| **`test_detailed.py`**   | Detailed debugging with step-by-step verification       | `python test_detailed.py`   |
| **`test_single_llm.py`** | Single query test for LLM integration                   | `python test_single_llm.py` |

### 🔧 Component Tests

| Test File                 | Description                           | Usage                        |
| ------------------------- | ------------------------------------- | ---------------------------- |
| **`test_endpoints.py`**   | REST API endpoint validation          | `python test_endpoints.py`   |
| **`test_integration.py`** | Raven client + MCP server integration | `python test_integration.py` |
| **`quick_test.py`**       | Simple MCP tools endpoint test        | `python quick_test.py`       |

### 📊 System Tests

| Test File                  | Description                       | Usage                         |
| -------------------------- | --------------------------------- | ----------------------------- |
| **`test_complete.py`**     | Full end-to-end system test       | `python test_complete.py`     |
| **`architecture_demo.py`** | System architecture demonstration | `python architecture_demo.py` |

## 🚀 Quick Start

### 1. Start the MCP Server

```bash
# From project root
python server.py --port 8001
```

### 2. Run Tests

```bash
# Navigate to tests directory
cd tests

# Use the interactive test runner
python run_tests.py

# Or run specific tests
python test_mcp_llm.py      # Main integration test
python test_detailed.py     # Detailed debugging
python architecture_demo.py # System overview
```

### 3. Test Runner Menu

```bash
python run_tests.py

# Available options:
# 1. Architecture Demo - Show system architecture
# 2. Endpoints Test - Test all MCP server endpoints
# 3. Quick Test - Simple MCP tools endpoint test
# 4. Integration Test - Test MCP + Raven client integration
# 5. Detailed Test - Comprehensive integration test with debugging
# 6. MCP+LLM Test - Full system test including LLM
# 7. Single LLM Test - Test one LLM query
# 8. Complete Test - Full end-to-end test
```

## 🎯 Test Scenarios

### ✅ What Gets Tested

1. **MCP Server Health**

   - Server startup and initialization
   - Health endpoint (`/health`)
   - Available tools endpoint (`/tools`)

2. **Tool Definition Architecture**

   - Dynamic tool definition serving (`/mcp/tools`)
   - OpenAI-compatible function format
   - Proper client-server separation

3. **Raven LLM Integration**

   - Client initialization with custom model
   - Tool definition fetching from server
   - Query processing and response generation

4. **End-to-End Workflow**
   - Natural language query → MCP tool call → LLM analysis
   - Prediction market data retrieval
   - Intelligent response generation

### 🧪 Sample Test Output

```bash
🧠 MCP Server + LLM System Integration Test
============================================================
🧪 Testing MCP Server Endpoints
==================================================
1️⃣ Testing Health Endpoint...
   ✅ Health: {'status': 'healthy', 'components': {...}}

2️⃣ Testing Tools Endpoint...
   ✅ Available tools: ['get_events']

3️⃣ Testing MCP Tools Endpoint (OpenAI Format)...
   ✅ OpenAI tools available: 2
      - mcp_get_events
      - get_prediction_markets

🧠 Testing Raven Client Integration
==================================================
   ✅ Raven client initialized
   ✅ Fetched 2 tool definitions
   ✅ MCP call successful: 2 results

🎉 ALL TESTS PASSED!
```

## 🔧 Configuration Requirements

### Environment Setup

Ensure your `.env` file contains:

```properties
RAVEN_REASONING_MODEL_API_KEY=your_api_key_here
RAVEN_REASONING_MODEL_API_URL=your_api_url_here
RAVEN_REASONING_MODEL_DEPLOYMENT_NAME=your_model_name
```

### Dependencies

All test dependencies are included in the main `requirements.txt`:

```bash
pip install -r ../requirements.txt
```

## 🐛 Troubleshooting

### Common Issues

1. **Server Connection Errors**

   ```bash
   # Ensure MCP server is running
   python ../server.py --port 8001

   # Check if port is available
   netstat -ano | findstr :8001
   ```

2. **Import Errors**

   ```bash
   # Tests automatically add parent directory to path
   # No additional setup needed
   ```

3. **LLM API Errors**
   ```bash
   # Check .env file for proper credentials
   # Verify your Raven model endpoint is accessible
   ```

### Test-Specific Debugging

- **`test_mcp_llm.py`** - Most comprehensive, use this first
- **`test_detailed.py`** - Includes debugging output for troubleshooting
- **`quick_test.py`** - Minimal test for basic connectivity

## 📊 Test Architecture

```
tests/
├── run_tests.py          # Interactive test runner
├── test_mcp_llm.py       # 🎯 Primary integration test
├── test_detailed.py      # 🔍 Debugging version
├── test_endpoints.py     # 🌐 API endpoint tests
├── test_integration.py   # 🔗 Client integration
├── test_single_llm.py    # 🧠 Single LLM query
├── test_complete.py      # 🎪 Full system test
├── quick_test.py         # ⚡ Quick connectivity
└── architecture_demo.py  # 📋 System overview
```

## 🎯 Testing Strategy

### Development Workflow

1. **Start with Quick Test**: Verify basic connectivity
2. **Run Main Integration**: Use `test_mcp_llm.py` for full verification
3. **Debug Issues**: Use `test_detailed.py` for troubleshooting
4. **Verify Components**: Run specific component tests as needed

### Continuous Integration

For automated testing:

```bash
# Run all critical tests
python test_mcp_llm.py && echo "Integration tests passed"
```

## 🚀 Adding New Tests

1. Create test file in `tests/` directory
2. Add parent directory to Python path:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
   ```
3. Import project modules normally
4. Add test to `run_tests.py` menu

## 📈 Test Coverage

- ✅ **Server Initialization**: Health checks and startup
- ✅ **API Endpoints**: All REST endpoints tested
- ✅ **Tool Architecture**: Dynamic tool definition serving
- ✅ **LLM Integration**: Full Raven model integration
- ✅ **Error Handling**: Graceful failure scenarios
- ✅ **End-to-End**: Complete workflow verification

---

**Ready to test? Start with:** `python run_tests.py` 🚀
tests/
├── run_tests.py # Test runner menu
├── test_mcp_llm.py # 🌟 Main integration test
├── test_detailed.py # Detailed debugging test
├── test_single_llm.py # Single query test
├── test_endpoints.py # API endpoint tests
├── test_integration.py # Client integration test
├── test_complete.py # Full E2E test
├── quick_test.py # Simple endpoint test
├── architecture_demo.py # System demo
└── README.md # This file

```

The tests validate the complete MCP architecture:
- **MCP Server** provides tool definitions via REST API
- **Raven Client** fetches tools dynamically (not hardcoded)
- **LLM Integration** works with custom Raven Reasoning Model
- **End-to-End Flow** processes queries through the complete pipeline
```
