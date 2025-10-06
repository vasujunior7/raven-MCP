"""Polymarket Fetcher — Fetches prediction market events."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import aiohttp
import json
from datetime import datetime

from core.cache_manager import cache_manager, CacheNode

logger = logging.getLogger(__name__)

class PolymarketFetcher:
    """Fetches events and market data from Polymarket API."""
    
    tool_name = "get_events"
    description = "Fetch prediction market events from Polymarket"
    parameters = ["keyword", "limit", "time_filter"]
    examples = [
        "Fetch me sports events",
        "Show 3 Trump election markets",
        "Get crypto events today"
    ]
    
    def __init__(self):
        """Initialize the Polymarket fetcher."""
        self.base_url = "https://gamma-api.polymarket.com"
        self.timeout = 30
        logger.info("PolymarketFetcher initialized")
    
    async def execute(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute the Polymarket events fetch with subgraph result caching.
        
        Implements: Graph/Subquery Cache (JSON Hashmap)
        - Hashes query + params for cache key
        - 10-15 minute TTL for market data
        - Full JSON response caching
        
        Args:
            params: Parsed parameters including keyword, limit, etc.
            
        Returns:
            List of event dictionaries
        """
        keyword = params.get('keyword', 'general')
        limit = params.get('limit', 5)
        time_filter = params.get('time_filter', 'all')
        
        # Create subgraph result cache key following your specification
        # Format: polymarket::{market_id}::{query_hash}
        import hashlib
        query_params = f"keyword={keyword}&limit={limit}&time_filter={time_filter}"
        query_hash = hashlib.md5(query_params.encode()).hexdigest()[:8]
        
        # Polymarket subgraph cache key structure
        cache_key = f"polymarket::event:{keyword}::{query_hash}"
        
        logger.info(f"Fetching Polymarket events: keyword='{keyword}', limit={limit}")
        logger.info(f"🔑 Subgraph cache key: {cache_key}")
        
        # STEP 0: Check subgraph result cache first
        cached_node = cache_manager.get(cache_key)
        if cached_node and cached_node.polymarket_data:
            logger.info(f"💾 SUBGRAPH CACHE HIT: Returning cached Polymarket data (expires in {cached_node.time_until_expiry():.1f}s)")
            return cached_node.polymarket_data.get('events', [])
        
        # For development/demo purposes, use mock data
        # In production, this would attempt real API calls first
        logger.info("Using mock data for demonstration")
        events_data = self._get_mock_data(keyword, limit)
        
        # Store in subgraph result cache with 10-15 minute TTL
        cache_manager.create_and_store(
            prompt=cache_key,
            ttl_seconds=900,  # 15 minutes for Polymarket subgraph data
            polymarket_data={
                "events": events_data, 
                "source": "mock", 
                "keyword": keyword,
                "cache_type": "subgraph_result",
                "query_hash": query_hash
            }
        )
        
        return events_data
    
    async def _fetch_events(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch events from Polymarket API."""
        url = f"{self.base_url}/events"
        params = {
            "limit": min(limit * 2, 50),  # Fetch more to allow filtering
            "active": "true"
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._transform_events(data)
                    else:
                        logger.warning(f"API returned status {response.status}")
                        return []
                        
        except aiohttp.ClientError as e:
            logger.warning(f"HTTP client error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching events: {e}")
            return []
    
    def _transform_events(self, api_data: Any) -> List[Dict[str, Any]]:
        """Transform API response to normalized format."""
        events = []
        
        # Handle different API response formats
        if isinstance(api_data, dict):
            events_list = api_data.get('data', api_data.get('events', []))
        elif isinstance(api_data, list):
            events_list = api_data
        else:
            logger.warning(f"Unexpected API response format: {type(api_data)}")
            return []
        
        for event in events_list:
            try:
                transformed = {
                    'title': event.get('title', event.get('question', 'Untitled Event')),
                    'endDate': self._parse_date(event.get('end_date', event.get('endDate'))),
                    'volume': float(event.get('volume', event.get('trading_volume', 0))),
                    'url': event.get('url', ''),
                    'description': event.get('description', ''),
                    'market_slug': event.get('slug', event.get('market_slug', '')),
                    'image': event.get('image', event.get('icon', ''))
                }
                events.append(transformed)
                
            except Exception as e:
                logger.warning(f"Error transforming event: {e}")
                continue
        
        return events
    
    def _parse_date(self, date_value: Any) -> Optional[str]:
        """Parse various date formats to ISO string."""
        if not date_value:
            return None
        
        if isinstance(date_value, str):
            return date_value
        
        if isinstance(date_value, (int, float)):
            try:
                dt = datetime.fromtimestamp(date_value)
                return dt.isoformat() + 'Z'
            except:
                return None
        
        return None
    
    def _filter_by_keyword(self, events: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
        """Filter events by keyword in title or description."""
        keyword_lower = keyword.lower()
        filtered = []
        
        for event in events:
            title = event.get('title', '').lower()
            description = event.get('description', '').lower()
            
            if keyword_lower in title or keyword_lower in description:
                filtered.append(event)
        
        logger.debug(f"Keyword filter '{keyword}' matched {len(filtered)}/{len(events)} events")
        return filtered
    
    def _get_mock_data(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """Return mock data for demonstration purposes."""
        logger.info("Using mock data for demonstration")
        
        # Simplified mock data
        mock_events = {
            'politics': [
                {'title': 'Will Donald Trump win the 2024 US Presidential Election?', 'endDate': '2025-11-05T23:59:59Z', 'volume': 150000.0, 'url': 'https://polymarket.com/trump-2024', 'description': 'Prediction market for the 2024 US Presidential Election', 'market_slug': 'trump-2024-election', 'image': ''},
                {'title': 'Will Trump be indicted before Jan 2026?', 'endDate': '2025-12-31T23:59:59Z', 'volume': 80000.0, 'url': 'https://polymarket.com/trump-indictment', 'description': 'Legal prediction market regarding potential indictment', 'market_slug': 'trump-indictment-2026', 'image': ''},
                {'title': 'Will Biden run for re-election in 2024?', 'endDate': '2025-06-01T23:59:59Z', 'volume': 45000.0, 'url': 'https://polymarket.com/biden-reelection', 'description': "Prediction about Biden's 2024 campaign decision", 'market_slug': 'biden-reelection-2024', 'image': ''}
            ],
            'sports': [
                {'title': 'Will the Kansas Chiefs win their next game?', 'endDate': '2025-10-15T23:59:59Z', 'volume': 50000.0, 'url': 'https://polymarket.com/chiefs-next-game', 'description': 'NFL prediction market for Kansas City Chiefs', 'market_slug': 'chiefs-next-game', 'image': ''},
                {'title': 'Will India win the Cricket World Cup?', 'endDate': '2025-10-20T23:59:59Z', 'volume': 75000.0, 'url': 'https://polymarket.com/india-cricket-wc', 'description': 'Cricket World Cup prediction market', 'market_slug': 'india-cricket-world-cup', 'image': ''},
                {'title': 'Will LeBron James retire this season?', 'endDate': '2025-07-01T23:59:59Z', 'volume': 30000.0, 'url': 'https://polymarket.com/lebron-retirement', 'description': 'NBA retirement prediction market', 'market_slug': 'lebron-retirement-2025', 'image': ''}
            ],
            'crypto': [
                {'title': 'Will Bitcoin reach $100k in 2025?', 'endDate': '2025-12-31T23:59:59Z', 'volume': 200000.0, 'url': 'https://polymarket.com/bitcoin-100k', 'description': 'Bitcoin price prediction market', 'market_slug': 'bitcoin-100k-2025', 'image': ''},
                {'title': 'Will Ethereum 2.0 launch successfully?', 'endDate': '2025-06-30T23:59:59Z', 'volume': 90000.0, 'url': 'https://polymarket.com/ethereum-2-launch', 'description': 'Ethereum 2.0 technical milestone prediction', 'market_slug': 'ethereum-2-launch', 'image': ''}
            ],
            'technology': [
                {'title': 'Will AI achieve AGI by 2030?', 'endDate': '2030-01-01T23:59:59Z', 'volume': 120000.0, 'url': 'https://polymarket.com/agi-2030', 'description': 'Artificial General Intelligence prediction market', 'market_slug': 'agi-by-2030', 'image': ''},
                {'title': 'Will climate change targets be met by 2030?', 'endDate': '2030-12-31T23:59:59Z', 'volume': 60000.0, 'url': 'https://polymarket.com/climate-targets', 'description': 'Global climate change prediction market', 'market_slug': 'climate-targets-2030', 'image': ''}
            ]
        }
        
        # Get events for the keyword, fallback to technology
        events = mock_events.get(keyword, mock_events['technology'])
        return events[:limit]
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the Polymarket API."""
        return {
            "api_endpoint": self.base_url,
            "timeout": self.timeout,
            "status": "mock_mode"  # Would be "connected" in real implementation
        }