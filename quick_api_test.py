import asyncio
from tools.polymarket_fetcher import PolymarketFetcher

async def quick_test():
    fetcher = PolymarketFetcher()
    results = await fetcher.execute({'keyword': 'sports', 'limit': 1})
    
    print("🏆 REAL API VERIFICATION:")
    print("=" * 40)
    
    if results:
        event = results[0]
        print(f"✅ Title: {event.get('title', 'N/A')}")
        print(f"💰 Volume: ${event.get('volume', 0):,.2f}")
        print(f"🆔 ID: {event.get('id', 'N/A')}")
        print(f"🔗 URL: {event.get('url', 'N/A')}")
        print(f"🏷️ Source: {event.get('source', 'N/A')}")
        
        # Check for real data indicators
        volume = event.get('volume', 0)
        event_id = event.get('id', '')
        url = event.get('url', '')
        
        if volume > 0 and event_id and 'polymarket.com' in url:
            print("\n✅ CONFIRMED: This is REAL Polymarket data!")
            print("   - Has real trading volume")
            print("   - Has valid event ID")
            print("   - Has official Polymarket URL")
        else:
            print("\n⚠️ Potential demo data - missing real indicators")
    else:
        print("❌ No results returned")

asyncio.run(quick_test())