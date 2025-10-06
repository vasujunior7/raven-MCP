"""LunarCrush Coins Fetcher — Fetches cryptocurrency coin data from LunarCrush API."""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
import aiohttp
import json
from datetime import datetime
from dotenv import load_dotenv

from utils.http import HTTPClient, HTTPConfig
from core.cache_manager import cache_manager, CacheNode

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LunarCrushCoins:
    """Fetches cryptocurrency coin data from LunarCrush API."""
    
    tool_name = "get_crypto_sentiment"
    description = "Fetch cryptocurrency sentiment and market data from LunarCrush"
    parameters = ["limit", "sort", "category"]
    examples = [
        "Get Bitcoin sentiment analysis",
        "Show top 5 trending crypto coins",
        "Fetch crypto market data"
    ]
    
    def __init__(self):
        """Initialize the LunarCrush coins fetcher."""
        self.base_url = "https://lunarcrush.com/api4/public"
        self.api_key = os.getenv('LUNAR_KEY')
        self.timeout = 30
        
        # MCP memory buffer for temporary storage
        self.memory_buffer = {
            "last_fetch_time": None,
            "cached_coins": [],
            "total_coins_fetched": 0,
            "fetch_history": []
        }
        
        # Initialize HTTP client
        config = HTTPConfig(timeout=self.timeout)
        self.http_client = HTTPClient(config)
        
        if not self.api_key:
            logger.error("LUNAR_KEY not found in environment variables")
            raise ValueError("LunarCrush API key is required")
        
        logger.info("LunarCrushCoins initialized with API key and MCP memory buffer")
    
    async def execute(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute the LunarCrush coins fetch with time-bucketed KV caching.
        
        Implements: Time-Bucketed Key-Value Cache
        - Creates hourly time buckets (UTC)
        - 1-hour TTL matching LunarCrush upstream cache
        - Keys: lunarcrush::{coin_symbol}::{hour_bucket}
        
        STRATEGY: Check cache first, then try API, gracefully fallback to demo data if:
        - API key doesn't have required subscription tier
        - Network issues or API errors
        - Any other connectivity problems
        
        Args:
            params: Parsed parameters including limit, sort, etc.
            
        Returns:
            List of coin dictionaries (always succeeds with demo data fallback)
        """
        limit = params.get('limit', 10)
        sort = params.get('sort', 'mc')  # market cap by default
        category = params.get('category', '')
        
        # Create time-bucketed cache key following your specification
        # Format: lunarcrush::{coin_symbol}::{hour_bucket}
        from datetime import datetime
        current_utc = datetime.utcnow()
        hour_bucket = current_utc.strftime("%Y-%m-%dT%H")  # e.g., "2025-10-06T14"
        
        # For bulk queries, use a general symbol or query identifier
        query_identifier = f"{sort}_{category}_{limit}".strip('_')
        cache_key = f"lunarcrush::{query_identifier}::{hour_bucket}"
        
        logger.info(f"🚀 Starting LunarCrush fetch: limit={limit}, sort={sort}, category={category}")
        logger.info(f"🔑 Time-bucket cache key: {cache_key} (Hour: {hour_bucket})")
        
        # STEP 0: Check time-bucketed cache first
        cached_node = cache_manager.get(cache_key)
        if cached_node and cached_node.lunarcrush_data:
            logger.info(f"💾 TIME-BUCKET CACHE HIT: Returning hourly cached LunarCrush data (expires in {cached_node.time_until_expiry():.1f}s)")
            return cached_node.lunarcrush_data.get('coins', [])
        
        logger.info("🔍 Step 1: Testing API connectivity...")
        
        # STEP 1: Try real API first
        try:
            connectivity_result = await self.verify_connectivity()
            
            if connectivity_result.get('tier') == 'premium' and connectivity_result['success']:
                logger.info("💎 Premium API access confirmed - attempting real data fetch...")
                try:
                    coins_data = await self._fetch_coins_list(limit, sort, category)
                    logger.info(f"✅ API FETCH SUCCESSFUL: Retrieved {len(coins_data)} coins from LunarCrush premium API")
                    
                    # Store in time-bucketed cache with 1-hour TTL
                    cache_manager.create_and_store(
                        prompt=cache_key,
                        ttl_seconds=3600,  # 1 hour for time-bucketed data
                        lunarcrush_data={
                            "coins": coins_data, 
                            "source": "api", 
                            "tier": "premium",
                            "cache_type": "time_bucketed",
                            "hour_bucket": hour_bucket,
                            "timestamp": current_utc.isoformat()
                        }
                    )
                    
                    self._update_memory_buffer(coins_data, params)
                    return coins_data
                except Exception as api_error:
                    logger.error(f"❌ API FETCH FAILED: Premium API error - {api_error}")
                    logger.info("🔄 FALLING BACK TO DEMO DATA due to API fetch failure")
            
            elif connectivity_result.get('tier') == 'free' and connectivity_result['success']:
                logger.info("🆓 Free tier API access - attempting limited data fetch...")
                try:
                    coins_data = await self._fetch_coins_list(limit, sort, category)
                    logger.info(f"✅ API FETCH SUCCESSFUL: Retrieved {len(coins_data)} coins from LunarCrush free API")
                    
                    # Store in time-bucketed cache with 1-hour TTL
                    cache_manager.create_and_store(
                        prompt=cache_key,
                        ttl_seconds=3600,  # 1 hour for time-bucketed data
                        lunarcrush_data={
                            "coins": coins_data, 
                            "source": "api", 
                            "tier": "free",
                            "cache_type": "time_bucketed",
                            "hour_bucket": hour_bucket,
                            "timestamp": current_utc.isoformat()
                        }
                    )
                    
                    self._update_memory_buffer(coins_data, params)
                    return coins_data
                except Exception as api_error:
                    logger.error(f"❌ API FETCH FAILED: Free API error - {api_error}")
                    logger.info("🔄 FALLING BACK TO DEMO DATA due to API fetch failure")
            
            else:
                logger.warning("⚠️ API NOT ACCESSIBLE: No valid API tier available")
                logger.info("🔄 FALLING BACK TO DEMO DATA due to API inaccessibility")
        
        except Exception as connectivity_error:
            logger.error(f"❌ CONNECTIVITY CHECK FAILED: {connectivity_error}")
            logger.info("🔄 FALLING BACK TO DEMO DATA due to connectivity issues")
        
        # STEP 2: Always provide demo data as fallback
        logger.info("🎭 USING DEMO DATA: Generating comprehensive demo dataset for development/testing")
        coins_data = self._get_demo_coins_data(limit, sort, category)
        logger.info(f"✅ DEMO DATA GENERATED: Created {len(coins_data)} demo coins with all required fields")
        
        # Store demo data in time-bucketed cache (still use hourly bucket for consistency)
        cache_manager.create_and_store(
            prompt=cache_key,  # Use same time-bucketed key
            ttl_seconds=600,  # 10 minutes for demo data (shorter than 1 hour)
            lunarcrush_data={
                "coins": coins_data, 
                "source": "demo", 
                "tier": "fallback",
                "cache_type": "time_bucketed",
                "hour_bucket": hour_bucket,
                "timestamp": current_utc.isoformat()
            }
        )
        
        # Update memory buffer with demo data
        self._update_memory_buffer(coins_data, params, error="Using demo data - API not accessible")
        
        return coins_data
    
    async def verify_connectivity(self) -> Dict[str, Any]:
        """
        Verify connectivity to LunarCrush API.
        First tries the premium endpoint, then falls back to free tier endpoints.
        
        Returns:
            Dictionary with success status and details
        """
        # Try premium endpoint first
        premium_endpoint = f"{self.base_url}/coins/list/v1"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Testing connectivity to premium endpoint: {premium_endpoint}")
            
            response_data = await self.http_client.get(premium_endpoint, headers=headers)
            
            if response_data:
                logger.info("✅ LunarCrush premium API connectivity verified successfully")
                return {
                    "success": True,
                    "message": "LunarCrush premium API connection verified",
                    "endpoint": premium_endpoint,
                    "tier": "premium",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            error_msg = str(e)
            if "402" in error_msg or "subscription" in error_msg.lower():
                logger.warning(f"Premium endpoint requires subscription, trying free tier alternatives...")
                
                # Try free tier endpoint alternatives
                free_endpoints = [
                    f"{self.base_url}/coins/v1",  # Alternative free endpoint
                    f"{self.base_url}/feeds/v1"   # Public feeds endpoint
                ]
                
                for endpoint in free_endpoints:
                    try:
                        logger.info(f"Testing free tier endpoint: {endpoint}")
                        response_data = await self.http_client.get(endpoint, headers=headers)
                        
                        if response_data:
                            logger.info("✅ LunarCrush free tier API connectivity verified successfully")
                            return {
                                "success": True,
                                "message": "LunarCrush free tier API connection verified",
                                "endpoint": endpoint,
                                "tier": "free",
                                "timestamp": datetime.now().isoformat()
                            }
                    except Exception as free_error:
                        logger.debug(f"Free endpoint {endpoint} failed: {free_error}")
                        continue
                
                # If all endpoints fail, provide mock data option
                logger.warning("All LunarCrush endpoints require subscription. Falling back to demo mode.")
                return {
                    "success": True,
                    "message": "LunarCrush API requires subscription - using demo mode with mock data",
                    "endpoint": "demo_mode",
                    "tier": "demo",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"❌ LunarCrush API connectivity failed: {error_msg}")
                return {
                    "success": False,
                    "message": f"Connection failed: {error_msg}",
                    "endpoint": premium_endpoint,
                    "timestamp": datetime.now().isoformat()
                }
    
    async def _fetch_coins_list(self, limit: int = 10, sort: str = "mc", category: str = "") -> List[Dict[str, Any]]:
        """
        Fetch coins list from LunarCrush API.
        
        This method will attempt to fetch real data but will raise informative exceptions
        for different failure scenarios (subscription issues, network problems, etc.)
        
        Args:
            limit: Number of coins to fetch
            sort: Sort parameter (mc=market cap, v=volume, etc.)
            category: Category filter
            
        Returns:
            List of coin data dictionaries
            
        Raises:
            Exception: With specific error details for different failure scenarios
        """
        endpoint = f"{self.base_url}/coins/list/v1"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build query parameters
        params = {
            "limit": limit,
            "sort": sort
        }
        if category:
            params["category"] = category
        
        try:
            logger.info(f"🌐 Fetching coins from {endpoint} with params: {params}")
            
            # Use HTTP client with parameters
            response_data = await self.http_client.get(endpoint, headers=headers, params=params)
            
            if response_data and 'data' in response_data:
                coins = response_data['data']
                logger.info(f"✅ API returned {len(coins)} coins successfully")
                
                # Format the response with all required Milestone 2 fields
                formatted_coins = []
                for coin in coins[:limit]:  # Ensure we don't exceed the limit
                    formatted_coin = {
                        "id": coin.get("id", coin.get("s", "").lower()),
                        "symbol": coin.get("s", "N/A"),
                        "name": coin.get("n", "N/A"),
                        "price": coin.get("p", 0),
                        "market_cap": coin.get("mc", 0),
                        "percent_change_24h": coin.get("pc", 0),
                        "galaxy_score": coin.get("gs", 0),
                        "alt_rank": coin.get("ar", 0),
                        "sentiment": coin.get("sentiment", "Neutral"),
                        "categories": coin.get("categories", ["General"]),
                        "market_dominance": coin.get("md", 0),
                        "volume_24h": coin.get("v", 0),
                        "social_score": coin.get("ss", 0),
                        "last_updated": datetime.now().isoformat(),
                        "data_source": "api",
                        "api_tier": "premium"
                    }
                    formatted_coins.append(formatted_coin)
                
                logger.info(f"✅ Successfully formatted {len(formatted_coins)} coins from API")
                return formatted_coins
            else:
                logger.warning("⚠️ API returned response but no coins data found")
                raise Exception("API response missing 'data' field - possibly malformed response")
                
        except Exception as e:
            error_msg = str(e)
            
            # Provide specific error handling for different scenarios
            if "402" in error_msg:
                logger.error("💳 Subscription required: API key doesn't have access to premium endpoints")
                raise Exception("API_SUBSCRIPTION_REQUIRED: Premium subscription needed for coins/list/v1 endpoint")
            elif "401" in error_msg:
                logger.error("🔑 Authentication failed: Invalid API key")
                raise Exception("API_AUTH_FAILED: Invalid or expired API key")
            elif "429" in error_msg:
                logger.error("🚦 Rate limit exceeded: Too many requests")
                raise Exception("API_RATE_LIMITED: Request rate limit exceeded")
            elif "timeout" in error_msg.lower():
                logger.error("⏱️ Request timeout: API is not responding")
                raise Exception("API_TIMEOUT: Request timed out")
            else:
                logger.error(f"🔥 General API error: {error_msg}")
                raise Exception(f"API_ERROR: {error_msg}")
    
    async def close(self):
        """Close the HTTP client session."""
        if self.http_client:
            await self.http_client.close()
    
    def _get_demo_coins_data(self, limit: int = 10, sort: str = "mc", category: str = "") -> List[Dict[str, Any]]:
        """
        Generate comprehensive demo data for testing MCP integration.
        This includes all required fields from Milestone 2.
        
        Args:
            limit: Number of coins to return
            sort: Sort parameter (mc=market cap, v=volume, etc.)
            category: Category filter
            
        Returns:
            List of formatted coin data dictionaries
        """
        # Comprehensive demo data with all required fields
        demo_coins = [
            {
                "id": "bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "price": 67234.50,
                "market_cap": 1325678900000,
                "percent_change_24h": 2.45,
                "galaxy_score": 85.2,
                "alt_rank": 1,
                "sentiment": "Bullish",
                "categories": ["Store of Value", "Digital Gold", "Payment"],
                "market_dominance": 45.8,
                "volume_24h": 28450000000,
                "social_score": 92.1,
                "developer_score": 88.5
            },
            {
                "id": "ethereum",
                "symbol": "ETH",
                "name": "Ethereum",
                "price": 2687.32,
                "market_cap": 323456789000,
                "percent_change_24h": 1.87,
                "galaxy_score": 82.7,
                "alt_rank": 2,
                "sentiment": "Bullish",
                "categories": ["Smart Contracts", "DeFi", "NFT"],
                "market_dominance": 18.3,
                "volume_24h": 15230000000,
                "social_score": 89.4,
                "developer_score": 95.2
            },
            {
                "id": "cardano",
                "symbol": "ADA",
                "name": "Cardano",
                "price": 0.372,
                "market_cap": 13127000000,
                "percent_change_24h": -0.85,
                "galaxy_score": 71.3,
                "alt_rank": 8,
                "sentiment": "Neutral",
                "categories": ["Smart Contracts", "Proof of Stake", "Research"],
                "market_dominance": 0.74,
                "volume_24h": 287000000,
                "social_score": 76.8,
                "developer_score": 81.9
            },
            {
                "id": "solana",
                "symbol": "SOL",
                "name": "Solana",
                "price": 143.67,
                "market_cap": 67890123000,
                "percent_change_24h": 4.23,
                "galaxy_score": 78.9,
                "alt_rank": 5,
                "sentiment": "Bullish",
                "categories": ["Smart Contracts", "High Performance", "DeFi"],
                "market_dominance": 2.1,
                "volume_24h": 1890000000,
                "social_score": 84.3,
                "developer_score": 87.1
            },
            {
                "id": "binancecoin",
                "symbol": "BNB",
                "name": "BNB",
                "price": 586.42,
                "market_cap": 85234567000,
                "percent_change_24h": 1.12,
                "galaxy_score": 76.4,
                "alt_rank": 4,
                "sentiment": "Neutral",
                "categories": ["Exchange Token", "DeFi", "BSC"],
                "market_dominance": 2.8,
                "volume_24h": 1234000000,
                "social_score": 79.6,
                "developer_score": 74.3
            },
            {
                "id": "ripple",
                "symbol": "XRP",
                "name": "XRP",
                "price": 0.5234,
                "market_cap": 29876543000,
                "percent_change_24h": -1.45,
                "galaxy_score": 69.2,
                "alt_rank": 6,
                "sentiment": "Bearish",
                "categories": ["Payment", "Cross-border", "Banking"],
                "market_dominance": 1.2,
                "volume_24h": 987000000,
                "social_score": 72.1,
                "developer_score": 68.9
            },
            {
                "id": "dogecoin",
                "symbol": "DOGE",
                "name": "Dogecoin",
                "price": 0.1234,
                "market_cap": 17654321000,
                "percent_change_24h": 8.76,
                "galaxy_score": 64.8,
                "alt_rank": 9,
                "sentiment": "Bullish",
                "categories": ["Meme", "Payment", "Community"],
                "market_dominance": 0.89,
                "volume_24h": 543000000,
                "social_score": 91.2,
                "developer_score": 45.7
            },
            {
                "id": "avalanche",
                "symbol": "AVAX",
                "name": "Avalanche",
                "price": 27.89,
                "market_cap": 11234567000,
                "percent_change_24h": 2.34,
                "galaxy_score": 73.6,
                "alt_rank": 11,
                "sentiment": "Bullish",
                "categories": ["Smart Contracts", "DeFi", "High Throughput"],
                "market_dominance": 0.45,
                "volume_24h": 234000000,
                "social_score": 77.9,
                "developer_score": 83.4
            },
            {
                "id": "chainlink",
                "symbol": "LINK",
                "name": "Chainlink",
                "price": 11.67,
                "market_cap": 7123456000,
                "percent_change_24h": 0.89,
                "galaxy_score": 75.2,
                "alt_rank": 13,
                "sentiment": "Neutral",
                "categories": ["Oracle", "DeFi", "Data"],
                "market_dominance": 0.31,
                "volume_24h": 189000000,
                "social_score": 73.5,
                "developer_score": 89.7
            },
            {
                "id": "polygon",
                "symbol": "MATIC",
                "name": "Polygon",
                "price": 0.4567,
                "market_cap": 4567890000,
                "percent_change_24h": -2.11,
                "galaxy_score": 71.8,
                "alt_rank": 15,
                "sentiment": "Neutral",
                "categories": ["Layer 2", "Scaling", "Ethereum"],
                "market_dominance": 0.19,
                "volume_24h": 156000000,
                "social_score": 76.2,
                "developer_score": 85.3
            }
        ]
        
        # Apply category filter if specified
        if category:
            demo_coins = [coin for coin in demo_coins if category.lower() in [cat.lower() for cat in coin["categories"]]]
        
        # Apply sorting
        if sort == "mc":  # market cap
            demo_coins.sort(key=lambda x: x["market_cap"], reverse=True)
        elif sort == "v":  # volume
            demo_coins.sort(key=lambda x: x["volume_24h"], reverse=True)
        elif sort == "p":  # price
            demo_coins.sort(key=lambda x: x["price"], reverse=True)
        elif sort == "pc":  # price change
            demo_coins.sort(key=lambda x: x["percent_change_24h"], reverse=True)
        elif sort == "gs":  # galaxy score
            demo_coins.sort(key=lambda x: x["galaxy_score"], reverse=True)
        elif sort == "ar":  # alt rank
            demo_coins.sort(key=lambda x: x["alt_rank"])
        
        # Apply limit and add metadata
        limited_coins = demo_coins[:limit]
        
        # Add timestamp and demo flag to each coin
        for coin in limited_coins:
            coin["last_updated"] = datetime.now().isoformat()
            coin["data_source"] = "demo"
            coin["api_tier"] = "demo_mode"
        
        logger.info(f"🎭 DEMO DATA DETAILS: Generated {len(limited_coins)} coins (sorted by {sort}, category: {category or 'all'})")
        logger.info(f"📋 DEMO COINS INCLUDED: {', '.join([coin['symbol'] for coin in limited_coins[:5]])}{'...' if len(limited_coins) > 5 else ''}")
        return limited_coins
    
    def _update_memory_buffer(self, coins_data: List[Dict[str, Any]], params: Dict[str, Any], error: str = None):
        """
        Update the MCP memory buffer with fetch results.
        
        Args:
            coins_data: The fetched coin data
            params: The request parameters
            error: Optional error message
        """
        current_time = datetime.now().isoformat()
        
        # Determine data source for logging
        data_source = coins_data[0].get("data_source", "unknown") if coins_data else "none"
        
        # Update buffer metadata
        self.memory_buffer["last_fetch_time"] = current_time
        self.memory_buffer["cached_coins"] = coins_data
        self.memory_buffer["total_coins_fetched"] += len(coins_data)
        
        # Add to fetch history
        fetch_record = {
            "timestamp": current_time,
            "params": params,
            "coins_count": len(coins_data),
            "error": error,
            "data_source": data_source
        }
        
        self.memory_buffer["fetch_history"].append(fetch_record)
        
        # Keep only last 10 fetch records
        if len(self.memory_buffer["fetch_history"]) > 10:
            self.memory_buffer["fetch_history"] = self.memory_buffer["fetch_history"][-10:]
        
        # Enhanced logging with clear data source indication
        if data_source == "api":
            logger.info(f"📦 MCP BUFFER UPDATED: {len(coins_data)} REAL coins from API stored | Total fetched: {self.memory_buffer['total_coins_fetched']}")
        elif data_source == "demo":
            logger.info(f"📦 MCP BUFFER UPDATED: {len(coins_data)} DEMO coins stored | Total fetched: {self.memory_buffer['total_coins_fetched']}")
        else:
            logger.info(f"📦 MCP BUFFER UPDATED: {len(coins_data)} coins ({data_source}) stored | Total fetched: {self.memory_buffer['total_coins_fetched']}")
    
    def get_memory_buffer_status(self) -> Dict[str, Any]:
        """
        Get the current status of the MCP memory buffer.
        
        Returns:
            Dictionary with buffer status and statistics
        """
        return {
            "buffer_status": {
                "last_fetch_time": self.memory_buffer["last_fetch_time"],
                "cached_coins_count": len(self.memory_buffer["cached_coins"]),
                "total_coins_fetched": self.memory_buffer["total_coins_fetched"],
                "fetch_history_count": len(self.memory_buffer["fetch_history"])
            },
            "recent_fetches": self.memory_buffer["fetch_history"][-3:],  # Last 3 fetches
            "cached_symbols": [coin.get("symbol", "N/A") for coin in self.memory_buffer["cached_coins"][:10]]  # First 10 symbols
        }