#!/usr/bin/env python3
"""
Test script to verify Polymarket data is coming from real API, not demo data.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.polymarket_fetcher import PolymarketFetcher
import aiohttp

async def test_real_api_calls():
    """Test that we're getting real data from Polymarket API."""
    
    print("🔍 Testing Polymarket API Integration")
    print("=" * 60)
    
    fetcher = PolymarketFetcher()
    
    # Test 1: Direct API call verification
    print("\n1️⃣ Testing direct API endpoint access...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test direct API call
            url = "https://gamma-api.polymarket.com/events"
            params = {"limit": 1, "closed": "false"}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Direct API call successful - Status: {response.status}")
                    print(f"📊 Received {len(data) if isinstance(data, list) else len(data.get('data', []))} events")
                    
                    # Show sample data structure
                    sample = data[0] if isinstance(data, list) and data else data.get('data', [{}])[0] if data.get('data') else {}
                    if sample:
                        print(f"📝 Sample event title: {sample.get('question', sample.get('title', 'N/A'))}")
                        print(f"🏷️ Sample event ID: {sample.get('id', 'N/A')}")
                        print(f"💰 Sample volume: ${sample.get('volume', 0)}")
                else:
                    print(f"❌ Direct API call failed - Status: {response.status}")
                    
    except Exception as e:
        print(f"❌ Direct API test failed: {str(e)}")
    
    # Test 2: Using our fetcher tool
    print("\n2️⃣ Testing through our Polymarket fetcher...")
    
    try:
        # Clear any cached data first
        from core.cache_manager import cache_manager
        cache_manager.clear_all()
        print("🗑️ Cleared all cache to ensure fresh API calls")
        
        # Test sports events
        params = {'keyword': 'sports', 'limit': 2, 'offset': 0}
        
        print(f"🔄 Fetching sports events with params: {params}")
        results = await fetcher.execute(params)
        
        print(f"✅ Fetcher returned {len(results)} results")
        
        # Analyze results for demo vs real data indicators
        for i, event in enumerate(results[:2], 1):
            print(f"\n📊 Event #{i}:")
            print(f"   Title: {event.get('title', 'N/A')}")
            print(f"   ID: {event.get('id', 'N/A')}")
            print(f"   Volume: ${event.get('volume', 0):,.2f}")
            print(f"   URL: {event.get('url', 'N/A')}")
            print(f"   End Date: {event.get('endDate', 'N/A')}")
            print(f"   Source: {event.get('source', 'N/A')}")
            
            # Check for demo data indicators
            title = str(event.get('title', '')).lower()
            if any(word in title for word in ['demo', 'mock', 'test', 'sample']):
                print("   ⚠️ POTENTIAL DEMO DATA DETECTED")
            else:
                print("   ✅ Appears to be real market data")
                
    except Exception as e:
        print(f"❌ Fetcher test failed: {str(e)}")
    
    # Test 3: Check for demo mode indicators in logs
    print("\n3️⃣ Checking for demo mode indicators...")
    
    # Check if there are any demo/mock references in the fetcher
    print("🔍 Checking fetcher configuration...")
    print(f"   Base URL: {fetcher.base_url}")
    print(f"   Timeout: {fetcher.timeout}s")
    
    # Health check
    health = fetcher.health_check()
    print(f"   Health status: {health}")

if __name__ == "__main__":
    asyncio.run(test_real_api_calls())