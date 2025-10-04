#!/usr/bin/env python3
"""Test runner for all MCP server tests."""

import sys
import os
import asyncio

# Add parent directory to path so we can import from the main project
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def main():
    """Main test runner menu."""
    print("🧠 MCP Server Test Suite")
    print("=" * 50)
    print()
    print("Available tests:")
    print("1. Architecture Demo - Show system architecture")
    print("2. Endpoints Test - Test all MCP server endpoints")
    print("3. Quick Test - Simple MCP tools endpoint test")
    print("4. Integration Test - Test MCP + Raven client integration")
    print("5. Detailed Test - Comprehensive integration test with debugging")
    print("6. MCP+LLM Test - Full system test including LLM")
    print("7. Single LLM Test - Test one LLM query")
    print("8. Complete Test - Full end-to-end test")
    print()
    print("Usage examples:")
    print("  python run_tests.py 1    # Run architecture demo")
    print("  python run_tests.py 6    # Run MCP+LLM test")
    print("  python run_tests.py all  # Run all tests")
    print()
    
    if len(sys.argv) < 2:
        print("Please specify a test number or 'all'")
        return
    
    choice = sys.argv[1].lower()
    
    if choice == "1":
        os.system("python architecture_demo.py")
    elif choice == "2":
        os.system("python test_endpoints.py")
    elif choice == "3":
        os.system("python quick_test.py")
    elif choice == "4":
        os.system("python test_integration.py")
    elif choice == "5":
        os.system("python test_detailed.py")
    elif choice == "6":
        os.system("python test_mcp_llm.py")
    elif choice == "7":
        os.system("python test_single_llm.py")
    elif choice == "8":
        os.system("python test_complete.py")
    elif choice == "all":
        print("Running all tests...")
        print("\n" + "="*60)
        os.system("python test_mcp_llm.py")
    else:
        print(f"Unknown test: {choice}")

if __name__ == "__main__":
    main()