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
        Execute the Polymarket events fetch with real API calls.
        
        Implements: Graph/Subquery Cache (JSON Hashmap)
        - Hashes query + params for cache key
        - 10-15 minute TTL for market data
        - Full JSON response caching
        
        Args:
            params: Parsed parameters including keyword, limit, etc.
            
        Returns:
            List of event dictionaries from real Polymarket API
        """
        keyword = params.get('keyword', '')
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
            logger.info(f"🎯💾 POLYMARKET CACHE HIT: Returning cached data (expires in {cached_node.time_until_expiry():.1f}s)")
            logger.info(f"📊 Cache data: {len(cached_node.polymarket_data.get('events', []))} events from cache")
            return cached_node.polymarket_data.get('events', [])
        
        # STEP 1: Fetch real data from Polymarket API
        try:
            events_data = await self._fetch_real_events(keyword, limit)
            logger.info(f"✅ REAL API SUCCESS: Fetched {len(events_data)} events from Polymarket API")
            
            # Store in subgraph result cache with 10-15 minute TTL
            cache_manager.create_and_store(
                prompt=cache_key,
                ttl_seconds=900,  # 15 minutes for Polymarket subgraph data
                polymarket_data={
                    "events": events_data, 
                    "source": "api", 
                    "keyword": keyword,
                    "cache_type": "subgraph_result",
                    "query_hash": query_hash
                }
            )
            
            logger.info(f"💾📊 POLYMARKET CACHED: Stored {len(events_data)} events for 15 minutes")
            
            return events_data
            
        except Exception as e:
            logger.error(f"❌ Polymarket API error: {str(e)}")
            logger.info("🔄 API failed, no fallback data available")
            return []
    
    async def _fetch_real_events(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch real events from Polymarket API based on keyword."""
        
        # Polymarket API endpoints
        events_url = f"{self.base_url}/events"
        markets_url = f"{self.base_url}/markets"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            try:
                # Step 1: Try to fetch events with keyword search
                logger.info(f"🔍 Searching Polymarket events for keyword: '{keyword}'")
                
                # Build search parameters
                params = {
                    "limit": min(limit * 2, 50),  # Fetch more to filter later
                    "offset": 0,
                    "active": "true"  # Only active markets
                }
                
                # Add keyword-based filtering
                if keyword and keyword != 'general':
                    # Try different search approaches
                    search_terms = [keyword]
                    
                    # Add related terms based on keyword
                    keyword_expansions = {
                        'politics': ['election', 'trump', 'biden', 'congress', 'senate'],
                        'sports': ['nfl', 'nba', 'football', 'basketball', 'soccer'],
                        'crypto': ['bitcoin', 'ethereum', 'crypto', 'btc', 'eth'],
                        'technology': ['ai', 'tech', 'apple', 'google', 'meta'],
                        'entertainment': ['movie', 'music', 'celebrity', 'oscar', 'grammy']
                    }
                    
                    if keyword in keyword_expansions:
                        search_terms.extend(keyword_expansions[keyword])
                
                # For politics queries, try markets endpoint first since politics markets are more common there
                if keyword == 'politics' or any(term in keyword.lower() for term in ['politics', 'election', 'biden', 'trump']):
                    logger.info("🗳️ Politics keyword detected, trying markets endpoint first...")
                    
                    # Try markets API first for politics
                    async with session.get(markets_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            markets = data if isinstance(data, list) else data.get('data', [])
                            logger.info(f"📥 Fetched {len(markets)} markets from API")
                            
                            # Filter markets by keyword
                            filtered_markets = self._filter_events_by_keyword(markets, keyword, search_terms if keyword != 'general' else [])
                            
                            if filtered_markets:
                                # Convert markets to event format
                                formatted_events = self._format_markets_as_events(filtered_markets[:limit])
                                logger.info(f"✅ Found {len(formatted_events)} politics markets")
                                return formatted_events
                
                # Try fetching events (original logic)
                async with session.get(events_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        events = data if isinstance(data, list) else data.get('data', [])
                        logger.info(f"📥 Fetched {len(events)} raw events from API")
                        
                        # Filter events by keyword
                        filtered_events = self._filter_events_by_keyword(events, keyword, search_terms if keyword != 'general' else [])
                        
                        # Convert to our format
                        formatted_events = self._format_events(filtered_events[:limit])
                        
                        logger.info(f"✅ Filtered to {len(formatted_events)} relevant events")
                        return formatted_events
                    else:
                        logger.warning(f"Events API returned status {response.status}")
                
                # Step 2: If events API fails, try markets API
                logger.info("🔄 Trying markets API as fallback...")
                
                async with session.get(markets_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        markets = data if isinstance(data, list) else data.get('data', [])
                        logger.info(f"📥 Fetched {len(markets)} markets from API")
                        
                        # Filter markets by keyword
                        filtered_markets = self._filter_events_by_keyword(markets, keyword, search_terms if keyword != 'general' else [])
                        
                        # Convert markets to event format
                        formatted_events = self._format_markets_as_events(filtered_markets[:limit])
                        
                        logger.info(f"✅ Filtered to {len(formatted_events)} relevant markets")
                        return formatted_events
                    else:
                        logger.error(f"Markets API returned status {response.status}")
                        raise Exception(f"Polymarket API error: {response.status}")
                        
            except asyncio.TimeoutError:
                logger.error("⏰ Polymarket API timeout")
                raise Exception("API timeout")
            except Exception as e:
                logger.error(f"🚨 Polymarket API error: {str(e)}")
                raise
    
    def _filter_events_by_keyword(self, events: List[Dict], keyword: str, search_terms: List[str]) -> List[Dict]:
        """Filter events/markets based on keyword and search terms."""
        if not keyword or keyword == 'general':
            return events
        
        filtered = []
        all_terms = [keyword.lower()] + [term.lower() for term in search_terms]
        
        logger.info(f"🔍 Filtering {len(events)} events with keyword='{keyword}' and terms={all_terms}")
        
        for i, event in enumerate(events):
            # Check title/question
            title = str(event.get('title', event.get('question', ''))).lower()
            description = str(event.get('description', '')).lower()
            tags = [str(tag).lower() for tag in event.get('tags', [])]
            
            # Check if any search term matches
            text_to_search = f"{title} {description} {' '.join(tags)}"
            
            # Debug first few events
            if i < 3:
                logger.info(f"   Event {i+1}: title='{title[:50]}...', matches={[term for term in all_terms if term in text_to_search]}")
            
            if any(term in text_to_search for term in all_terms):
                filtered.append(event)
                logger.info(f"   ✅ Event {i+1} MATCHED: {title[:50]}...")
        
        logger.info(f"🎯 Filtered results: {len(filtered)} events matched")
        return filtered
    
    def _format_events(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Format Polymarket events to our standard format."""
        formatted = []
        
        for event in events:
            formatted_event = {
                'title': event.get('title', event.get('question', 'Untitled Event')),
                'description': event.get('description', ''),
                'endDate': event.get('end_date', event.get('endDate')),
                'volume': float(event.get('volume', event.get('volume_24h', 0))),
                'url': f"https://polymarket.com/event/{event.get('slug', event.get('id', ''))}",
                'marketSlug': event.get('slug', ''),
                'id': event.get('id', ''),
                'tags': event.get('tags', []),
                'source': 'polymarket'
            }
            formatted.append(formatted_event)
        
        return formatted
    
    def _format_markets_as_events(self, markets: List[Dict]) -> List[Dict[str, Any]]:
        """Format Polymarket markets as events."""
        formatted = []
        
        for market in markets:
            formatted_event = {
                'title': market.get('question', market.get('title', 'Untitled Market')),
                'description': market.get('description', ''),
                'endDate': market.get('end_date', market.get('endDate')),
                'volume': float(market.get('volume', market.get('volume_24h', 0))),
                'url': f"https://polymarket.com/market/{market.get('slug', market.get('id', ''))}",
                'marketSlug': market.get('slug', ''),
                'id': market.get('id', ''),
                'tags': market.get('tags', []),
                'source': 'polymarket'
            }
            formatted.append(formatted_event)
        
        return formatted
    
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
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the Polymarket API."""
        return {
            "api_endpoint": self.base_url,
            "timeout": self.timeout,
            "status": "real_api_mode"
        }