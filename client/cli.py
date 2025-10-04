"""CLI Client for MCP Server."""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import MCPServer
from utils.formatter import ResponseFormatter
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MCPCLIClient:
    """Command-line interface for the MCP Server."""
    
    def __init__(self):
        self.server = MCPServer()
        self.formatter = ResponseFormatter()
        logger.info("MCP CLI Client initialized")
    
    async def run_query(self, query: str, output_format: str = "table") -> None:
        """Run a single query and display results."""
        print(f"\n🧠 Processing: '{query}'")
        print("=" * 60)
        
        try:
            # Process query through MCP server
            result = await self.server.process_query(query)
            
            if result["success"]:
                results = result["results"]
                
                if not results:
                    print("❌ No results found.")
                    return
                
                print(f"✅ Found {len(results)} results:\n")
                
                # Format output based on requested format
                if output_format == "table":
                    formatted = self.formatter.format_table(results)
                elif output_format == "cards":
                    formatted = self.formatter.format_cards(results)
                elif output_format == "json":
                    formatted = self.formatter.format_json(results)
                elif output_format == "summary":
                    formatted = self.formatter.format_summary(results, query)
                else:
                    formatted = self.formatter.format_table(results)  # Default
                
                print(formatted)
                
            else:
                print(f"❌ Error: {result['error']}")
        
        except Exception as e:
            logger.error(f"CLI error: {e}")
            print(f"❌ Unexpected error: {e}")
    
    async def interactive_mode(self):
        """Run in interactive mode for continuous queries."""
        print("🧠 MCP Server - Interactive Mode")
        print("=" * 50)
        print("Enter natural language queries (type 'quit' to exit)")
        print("Commands:")
        print("  /format <table|cards|json|summary> - Change output format")
        print("  /tools - List available tools")
        print("  /help - Show this help")
        print()
        
        output_format = "table"
        
        while True:
            try:
                query = input(">>> ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                # Handle special commands
                if query.startswith('/'):
                    if query == '/help':
                        self._show_help()
                    elif query == '/tools':
                        await self._show_tools()
                    elif query.startswith('/format '):
                        new_format = query.split(' ', 1)[1].strip()
                        if new_format in ['table', 'cards', 'json', 'summary']:
                            output_format = new_format
                            print(f"📋 Output format changed to: {output_format}")
                        else:
                            print("❌ Invalid format. Use: table, cards, json, or summary")
                    else:
                        print("❌ Unknown command. Type /help for available commands.")
                    continue
                
                # Process normal query
                await self.run_query(query, output_format)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Interactive mode error: {e}")
                print(f"❌ Error: {e}")
    
    def _show_help(self):
        """Display help information."""
        help_text = """
🧠 MCP Server CLI Help

Natural Language Queries:
  "Fetch me sports events"
  "Show 3 Trump election markets"
  "Get crypto events today"
  "Find AI technology predictions"

Commands:
  /format <type>  - Change output format (table, cards, json, summary)
  /tools          - List available tools
  /help           - Show this help
  quit, exit, q   - Exit the program

Output Formats:
  table   - Tabular format (default)
  cards   - Card-based detailed view
  json    - Raw JSON output
  summary - Brief summary with stats
        """
        print(help_text)
    
    async def _show_tools(self):
        """Display available tools."""
        try:
            tools_info = await self.server.list_available_tools()
            
            print("\n🔧 Available Tools:")
            print("-" * 30)
            
            for tool_name, tool_info in tools_info["available_tools"].items():
                print(f"📌 {tool_name}")
                print(f"   Description: {tool_info['description']}")
                if tool_info.get('examples'):
                    print(f"   Examples: {', '.join(tool_info['examples'][:2])}")
                print()
            
            print(f"Total tools: {tools_info['count']}")
        
        except Exception as e:
            print(f"❌ Error listing tools: {e}")

async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Server CLI - Natural Language Query Interface"
    )
    parser.add_argument(
        "query", 
        nargs="*", 
        help="Natural language query to process"
    )
    parser.add_argument(
        "--format", 
        choices=["table", "cards", "json", "summary"],
        default="table",
        help="Output format (default: table)"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    # Initialize CLI client
    client = MCPCLIClient()
    
    if args.interactive or not args.query:
        # Interactive mode
        await client.interactive_mode()
    else:
        # Single query mode
        query = " ".join(args.query)
        await client.run_query(query, args.format)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)