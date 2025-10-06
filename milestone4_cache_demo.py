#!/usr/bin/env python3
"""
Cache Performance Demo Script for Milestone 4
Demonstrates cache hit/miss behavior, TTL management, and performance improvements.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import cache manager and tools
from core.cache_manager import cache_manager, CacheNode
from tools.lunarcrush_coins import LunarCrushCoins
from tools.polymarket_fetcher import PolymarketFetcher
from tools.combined_reasoning import CombinedMCPReasoning
from core.enhanced_router import EnhancedMCPRouter

async def demonstrate_cache_performance():
    """Comprehensive cache performance demonstration."""
    
    print("🚀 " + "="*80)
    print("🚀 MILESTONE 4: CACHE GRAPH + SUBGRAPH IMPLEMENTATION DEMO")
    print("🚀 " + "="*80)
    print()
    
    # Initialize tools
    lunarcrush_tool = LunarCrushCoins()
    polymarket_tool = PolymarketFetcher()
    combined_tool = CombinedMCPReasoning(polymarket_tool, lunarcrush_tool)
    router = EnhancedMCPRouter()
    
    # Register tools with router
    router.register_tool(lunarcrush_tool)
    router.register_tool(polymarket_tool)
    router.register_tool(combined_tool)
    
    print("🔧 All tools initialized and registered with router")
    print()
    
    # Demo 1: Cache Miss -> Cache Hit Demonstration
    print("📊 DEMO 1: CACHE HIT/MISS BEHAVIOR")
    print("=" * 50)
    
    test_queries = [
        "Get top 5 Bitcoin data",
        "Show Trump election markets",
        "What position should I take on crypto markets?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🎯 Test {i}: '{query}'")
        print("-" * 40)
        
        # First call - should be cache MISS
        print("First call (expecting CACHE MISS):")
        start_time = time.time()
        result1 = await router.execute_intelligent_query(query)
        duration1 = time.time() - start_time
        print(f"⏱️  Duration: {duration1:.3f}s")
        
        # Immediate second call - should be cache HIT
        print("\nImmediate second call (expecting CACHE HIT):")
        start_time = time.time()
        result2 = await router.execute_intelligent_query(query)
        duration2 = time.time() - start_time
        print(f"⏱️  Duration: {duration2:.3f}s")
        
        # Performance improvement
        if duration1 > 0:
            improvement = ((duration1 - duration2) / duration1) * 100
            print(f"🚀 Performance improvement: {improvement:.1f}%")
        
        print()
    
    # Demo 2: Cache Statistics and Management
    print("\n📈 DEMO 2: CACHE STATISTICS AND MANAGEMENT")
    print("=" * 50)
    
    # Display cache statistics
    stats = cache_manager.get_stats()
    print("📊 Current Cache Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()
    
    # List cache entries
    entries = cache_manager.list_entries(include_expired=False)
    print(f"💾 Active Cache Entries ({len(entries)}):")
    for entry in entries:
        print(f"   🔑 {entry['key']}: {entry['prompt']} ({entry['time_until_expiry']}s left)")
    print()
    
    # Demo 3: TTL Expiration Behavior
    print("⏰ DEMO 3: TTL EXPIRATION BEHAVIOR")
    print("=" * 50)
    
    # Create a test cache entry with very short TTL
    test_key = cache_manager.create_and_store(
        prompt="short_ttl_test",
        ttl_seconds=3,  # 3 seconds TTL
        derived_data={"test": "This will expire soon"}
    )
    
    print(f"📝 Created test cache entry with 3s TTL: {test_key}")
    
    # Check immediately
    node = cache_manager.get(test_key)
    if node:
        print(f"✅ Immediate retrieval successful (expires in {node.time_until_expiry():.1f}s)")
    
    # Wait 2 seconds
    print("⏳ Waiting 2 seconds...")
    await asyncio.sleep(2)
    
    node = cache_manager.get(test_key)
    if node:
        print(f"✅ After 2s: Still valid (expires in {node.time_until_expiry():.1f}s)")
    
    # Wait another 2 seconds (total 4s, should be expired)
    print("⏳ Waiting another 2 seconds (total 4s)...")
    await asyncio.sleep(2)
    
    node = cache_manager.get(test_key)
    if node:
        print(f"✅ After 4s: Still valid (expires in {node.time_until_expiry():.1f}s)")
    else:
        print("❌ After 4s: Entry expired and removed from cache")
    
    print()
    
    # Demo 4: Cache Key Generation and Collision Avoidance
    print("🔑 DEMO 4: CACHE KEY GENERATION")
    print("=" * 50)
    
    test_cases = [
        ("bitcoin data", ["lunarcrush"], {"limit": 5}),
        ("bitcoin data", ["lunarcrush"], {"limit": 10}),  # Different params
        ("Bitcoin Data", ["lunarcrush"], {"limit": 5}),   # Case difference
        ("bitcoin data", ["polymarket"], {"limit": 5}),   # Different data type
    ]
    
    print("🧪 Testing cache key generation for similar queries:")
    keys = []
    for i, (prompt, data_types, kwargs) in enumerate(test_cases, 1):
        key = cache_manager.generate_cache_key(prompt, data_types, **kwargs)
        keys.append(key)
        print(f"   {i}. '{prompt}' + {data_types} + {kwargs} → {key}")
    
    # Check for uniqueness
    unique_keys = set(keys)
    print(f"\n🎯 Generated {len(keys)} keys, {len(unique_keys)} unique")
    if len(keys) == len(unique_keys):
        print("✅ All keys are unique - no collisions detected")
    else:
        print("⚠️  Key collision detected!")
    
    print()
    
    # Demo 5: Cache Cleanup and Memory Management
    print("🧹 DEMO 5: CACHE CLEANUP AND MEMORY MANAGEMENT")
    print("=" * 50)
    
    # Show current state
    stats_before = cache_manager.get_stats()
    print(f"📊 Before cleanup: {stats_before['active_entries']} entries")
    
    # Create some test entries with different TTLs
    for i in range(5):
        cache_manager.create_and_store(
            prompt=f"test_cleanup_{i}",
            ttl_seconds=1,  # Very short TTL
            derived_data={"test": f"cleanup_test_{i}"}
        )
    
    stats_after_create = cache_manager.get_stats()
    print(f"📊 After creating test entries: {stats_after_create['active_entries']} entries")
    
    # Wait for expiration
    print("⏳ Waiting 2 seconds for entries to expire...")
    await asyncio.sleep(2)
    
    # Run cleanup
    expired_count = cache_manager.cleanup_expired()
    print(f"🧹 Cleanup removed {expired_count} expired entries")
    
    stats_after_cleanup = cache_manager.get_stats()
    print(f"📊 After cleanup: {stats_after_cleanup['active_entries']} entries")
    
    print()
    
    # Demo 6: Performance Comparison
    print("🏁 DEMO 6: PERFORMANCE COMPARISON")
    print("=" * 50)
    
    # Clear cache to start fresh
    cache_manager.clear()
    print("🧹 Cache cleared for performance test")
    
    test_query = "What's the best position for Bitcoin markets?"
    
    # Multiple consecutive calls
    durations = []
    for i in range(5):
        start_time = time.time()
        result = await router.execute_intelligent_query(test_query)
        duration = time.time() - start_time
        durations.append(duration)
        
        cache_status = "MISS" if i == 0 else "HIT"
        print(f"   Call {i+1}: {duration:.3f}s (Cache {cache_status})")
    
    # Calculate performance metrics
    first_call = durations[0]
    avg_cached = sum(durations[1:]) / len(durations[1:]) if len(durations) > 1 else 0
    
    print(f"\n📊 Performance Summary:")
    print(f"   First call (cache miss): {first_call:.3f}s")
    print(f"   Average cached calls: {avg_cached:.3f}s")
    if first_call > 0 and avg_cached > 0:
        speedup = first_call / avg_cached
        print(f"   Speedup factor: {speedup:.1f}x")
        print(f"   Time savings: {((first_call - avg_cached) / first_call * 100):.1f}%")
    
    print()
    
    # Final cache statistics
    print("📊 FINAL CACHE STATISTICS")
    print("=" * 50)
    
    final_stats = cache_manager.get_stats()
    print("Cache Performance Metrics:")
    for key, value in final_stats.items():
        print(f"   {key}: {value}")
    
    print()
    print("💾 Cache Entries Summary:")
    final_entries = cache_manager.list_entries(include_expired=False)
    for entry in final_entries:
        data_types_str = ", ".join(entry['data_types'])
        print(f"   🔑 {entry['key'][:8]}... | {entry['prompt'][:30]}... | Types: {data_types_str} | TTL: {entry['time_until_expiry']:.1f}s")
    
    print()
    print("✅ " + "="*80)
    print("✅ MILESTONE 4 CACHE IMPLEMENTATION DEMO COMPLETED SUCCESSFULLY")
    print("✅ " + "="*80)
    
    return {
        "demo_completed": True,
        "final_stats": final_stats,
        "cache_entries": len(final_entries),
        "performance_improvement": f"{((first_call - avg_cached) / first_call * 100):.1f}%" if first_call > 0 and avg_cached > 0 else "N/A"
    }

def main():
    """Main demo function."""
    try:
        result = asyncio.run(demonstrate_cache_performance())
        print(f"\n🎉 Demo completed with result: {result}")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.exception("Demo execution failed")

if __name__ == "__main__":
    main()