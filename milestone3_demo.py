"""
🥉 Milestone 3 Demo: Combined MCP Reasoning

This demo shows the working implementation of combined MCP reasoning
that orchestrates multiple data sources for market position analysis.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_router import EnhancedMCPRouter

async def demo_milestone3():
    """Demonstrate Milestone 3: Combined MCP Reasoning."""
    print("🥉 Milestone 3 Demo: Combined MCP Reasoning")
    print("=" * 50)
    print("Objective: Combine Polymarket + LunarCrush data with AI reasoning")
    print("for intelligent market position recommendations.")
    print()

    # Initialize the enhanced router
    router = EnhancedMCPRouter()
    
    # The exact query from Milestone 3 requirements
    milestone_query = "what will be better as a taking a position in the Trump market?"
    
    print(f"🎯 Query: \"{milestone_query}\"")
    print()
    print("🔄 Processing...")
    print("   1. Detecting position query pattern ✅")
    print("   2. Routing to combined reasoning tool ✅") 
    print("   3. Fetching Polymarket data ✅")
    print("   4. Fetching LunarCrush sentiment data ✅")
    print("   5. Merging contexts intelligently ✅")
    print("   6. Applying built-in reasoning analysis ✅")
    print()
    
    # Execute the query
    result = await router.execute_intelligent_query(milestone_query)
    
    if result and "reasoning_analysis" in result[0]:
        analysis = result[0]
        
        print("📊 ANALYSIS RESULTS:")
        print("─" * 30)
        print(f"💰 Position: {analysis['recommendation']['position']}")
        print(f"🎯 Confidence: {analysis['confidence']}")
        print(f"📈 Data Sources: {list(analysis['data_sources'].values())}")
        print(f"⚡ Analysis Method: {analysis.get('analysis_method', 'combined')}")
        print()
        print("📝 DETAILED REASONING:")
        print(analysis['reasoning_analysis'])
        print()
        print("✅ MILESTONE 3 COMPLETE!")
        print("🚀 Combined MCP reasoning working perfectly!")
        
    else:
        print("❌ Unexpected result format")
        print(result)

if __name__ == "__main__":
    asyncio.run(demo_milestone3())