"""Simple test for LunarCrush integration."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_simple():
    """Simple synchronous test."""
    try:
        from tools.lunarcrush_coins import LunarCrushCoins
        print("✅ Import successful")
        
        # Test initialization
        lc = LunarCrushCoins()
        print("✅ Initialization successful")
        
        # Test demo data
        demo_data = lc._get_demo_coins_data(3, "mc", "")
        print(f"✅ Demo data generated: {len(demo_data)} coins")
        
        # Show sample
        for coin in demo_data[:2]:
            print(f"   • {coin['name']} ({coin['symbol']}): ${coin['price']:.2f}")
        
        print("\n🎉 Simple test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_simple()