"""Combined MCP Reasoning Tool — Orchestrates multiple data sources for intelligent market analysis."""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.cache_manager import cache_manager, CacheNode

# Skip LLM reasoner import for now - use built-in analysis instead
# from utils.llm_reasoner import LLMReasoner

logger = logging.getLogger(__name__)

class CombinedMCPReasoning:
    """
    Combined MCP Reasoning Tool that orchestrates multiple data sources
    for intelligent market position recommendations.
    
    This tool implements Milestone 3 functionality:
    1. Detects position/market queries
    2. Routes to multiple tools (Polymarket + LunarCrush)  
    3. Merges contexts intelligently
    4. Applies reasoning model for recommendations
    """
    
    tool_name = "combined_reasoning"
    description = "Analyze market positions by combining Polymarket and LunarCrush data with AI reasoning"
    parameters = ["query", "keyword", "context"]
    examples = [
        "What will be better to take a position in this market?",
        "Should I go long or short on Trump market?", 
        "What's the best position for crypto prediction markets?",
        "Analyze Bitcoin sentiment vs prediction market data"
    ]
    
    def __init__(self, polymarket_tool=None, lunarcrush_tool=None):
        """
        Initialize the combined reasoning tool.
        
        Args:
            polymarket_tool: Instance of PolymarketFetcher
            lunarcrush_tool: Instance of LunarCrushCoins
        """
        self.polymarket_tool = polymarket_tool
        self.lunarcrush_tool = lunarcrush_tool
        # Skip LLM reasoner for now - use built-in analysis
        # self.llm_reasoner = LLMReasoner()
        
        # Position/market query patterns
        self.position_patterns = [
            r"take position", r"better.*position", r"go long", r"go short",
            r"better.*market", r"position.*market", r"long.*short",
            r"buy.*sell", r"bull.*bear", r"invest.*trade"
        ]
        
        logger.info("CombinedMCPReasoning initialized with built-in analysis (no external LLM required)")
    
    def should_use_combined_reasoning(self, query: str) -> bool:
        """
        Check if query should trigger combined reasoning.
        
        Args:
            query: User query string
            
        Returns:
            True if query matches position/market patterns
        """
        query_lower = query.lower()
        
        for pattern in self.position_patterns:
            if re.search(pattern, query_lower):
                logger.info(f"🎯 Position query detected: '{pattern}' in '{query}'")
                return True
        
        return False
    
    def extract_keyword(self, query: str) -> str:
        """
        Extract the main keyword/topic from the query.
        
        Args:
            query: User query string
            
        Returns:
            Extracted keyword for tool queries
        """
        # Common market keywords
        market_keywords = {
            "trump": "Trump", "election": "election", "bitcoin": "Bitcoin", 
            "crypto": "crypto", "eth": "Ethereum", "btc": "Bitcoin",
            "politics": "politics", "sports": "sports", "tech": "technology"
        }
        
        query_lower = query.lower()
        
        # Check for known keywords
        for keyword, formatted in market_keywords.items():
            if keyword in query_lower:
                logger.info(f"🔍 Extracted keyword: '{formatted}' from query")
                return formatted
        
        # Extract potential market name between quotes or after "in"
        import re
        
        # Look for "in the X market" or "X market"
        market_match = re.search(r'(?:in (?:the )?)?(\w+)(?:\s+market)?', query_lower)
        if market_match:
            keyword = market_match.group(1).title()
            logger.info(f"🔍 Extracted keyword from pattern: '{keyword}'")
            return keyword
        
        # Default fallback
        logger.info("🔍 Using default keyword: 'general'")
        return "general"
    
    async def execute(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute combined reasoning analysis with intelligent caching.
        
        Args:
            params: Parameters including query, keyword, etc.
            
        Returns:
            List containing reasoning analysis and recommendations
        """
        query = params.get('query', '')
        explicit_keyword = params.get('keyword', '')
        
        # Generate cache key for this reasoning request
        keyword = explicit_keyword or self.extract_keyword(query)
        
        # Create reasoning cache key with query hash
        import hashlib
        query_hash = hashlib.md5(f"{query}:{keyword}".encode()).hexdigest()[:8]
        cache_key = f"reasoning::{keyword}::{query_hash}"
        
        logger.info(f"🚀 Starting combined MCP reasoning for: '{query}'")
        logger.info(f"🔑 Reasoning cache key: {cache_key}")
        
        # STEP 0: Check reasoning cache first
        cached_node = cache_manager.get(cache_key)
        if cached_node and cached_node.derived_data:
            logger.info(f"💾 REASONING CACHE HIT: Returning cached analysis (expires in {cached_node.time_until_expiry():.1f}s)")
            return cached_node.derived_data.get('reasoning_result', [])
        
        # Check if this should use combined reasoning
        if not self.should_use_combined_reasoning(query):
            logger.info("❌ Query doesn't match position patterns - skipping combined reasoning")
            return [{"info": "Query doesn't require combined market analysis"}]
        
        try:
            # Step 1: Fetch Polymarket data
            logger.info(f"📊 Step 1: Fetching Polymarket data for '{keyword}'...")
            polymarket_data = await self._fetch_polymarket_data(keyword)
            
            # Step 2: Fetch LunarCrush data  
            logger.info(f"🌕 Step 2: Fetching LunarCrush data for '{keyword}'...")
            lunarcrush_data = await self._fetch_lunarcrush_data(keyword)
            
            # Step 3: Merge contexts
            logger.info("🧩 Step 3: Merging data contexts...")
            merged_context = self._merge_contexts(polymarket_data, lunarcrush_data, keyword)
            
            # Step 4: Apply reasoning model
            logger.info("🧠 Step 4: Applying AI reasoning model...")
            reasoning_result = await self._apply_reasoning_model(merged_context, query)
            
            # Store result in reasoning cache with appropriate TTL
            cache_manager.create_and_store(
                prompt=cache_key,
                ttl_seconds=600,  # 10 minutes for reasoning results
                polymarket_data={"events": polymarket_data.get('events', [])},
                lunarcrush_data={"coins": lunarcrush_data.get('coins', [])},
                derived_data={
                    "reasoning_result": reasoning_result,
                    "merged_context": merged_context,
                    "keyword": keyword,
                    "query": query,
                    "cache_type": "reasoning_analysis",
                    "query_hash": query_hash
                }
            )
            
            logger.info("✅ Combined MCP reasoning completed successfully")
            return reasoning_result
            
        except Exception as e:
            logger.error(f"❌ Combined reasoning failed: {str(e)}")
            return [{"error": f"Combined reasoning failed: {str(e)}"}]
    
    async def _fetch_polymarket_data(self, keyword: str) -> Dict[str, Any]:
        """Fetch relevant Polymarket event data."""
        if not self.polymarket_tool:
            logger.warning("⚠️ Polymarket tool not available - using mock data")
            return self._get_mock_polymarket_data(keyword)
        
        try:
            # Use Polymarket tool to fetch events
            polymarket_params = {"keyword": keyword, "limit": 5, "time_filter": "recent"}
            events = await self.polymarket_tool.execute(polymarket_params)
            
            logger.info(f"📊 Fetched {len(events)} Polymarket events")
            return {
                "source": "polymarket_api",
                "keyword": keyword,
                "events": events,
                "event_count": len(events)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Polymarket fetch failed: {e} - using mock data")
            return self._get_mock_polymarket_data(keyword)
    
    async def _fetch_lunarcrush_data(self, keyword: str) -> Dict[str, Any]:
        """Fetch relevant LunarCrush sentiment/coin data."""
        if not self.lunarcrush_tool:
            logger.warning("⚠️ LunarCrush tool not available - using mock data")
            return self._get_mock_lunarcrush_data(keyword)
        
        try:
            # Use LunarCrush tool to fetch coin data
            lunar_params = {"limit": 10, "sort": "gs", "category": ""}
            coins = await self.lunarcrush_tool.execute(lunar_params)
            
            # Filter for relevant coins based on keyword
            relevant_coins = self._filter_relevant_coins(coins, keyword)
            
            logger.info(f"🌕 Fetched {len(relevant_coins)} relevant LunarCrush coins")
            return {
                "source": "lunarcrush_api", 
                "keyword": keyword,
                "coins": relevant_coins,
                "coin_count": len(relevant_coins)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ LunarCrush fetch failed: {e} - using mock data")
            return self._get_mock_lunarcrush_data(keyword)
    
    def _filter_relevant_coins(self, coins: List[Dict], keyword: str) -> List[Dict]:
        """Filter coins relevant to the keyword."""
        keyword_lower = keyword.lower()
        relevant = []
        
        for coin in coins:
            name = coin.get("name", "").lower()
            symbol = coin.get("symbol", "").lower()
            categories = [cat.lower() for cat in coin.get("categories", [])]
            
            # Check if coin is relevant to keyword
            if (keyword_lower in name or keyword_lower in symbol or 
                any(keyword_lower in cat for cat in categories) or
                keyword_lower == "crypto" or keyword_lower == "general"):
                relevant.append(coin)
        
        return relevant[:5]  # Limit to top 5 relevant coins
    
    def _merge_contexts(self, polymarket_data: Dict, lunarcrush_data: Dict, keyword: str) -> Dict[str, Any]:
        """
        Merge Polymarket and LunarCrush data into unified context.
        
        Args:
            polymarket_data: Polymarket events data
            lunarcrush_data: LunarCrush sentiment data  
            keyword: Search keyword
            
        Returns:
            Unified context for reasoning
        """
        merged = {
            "analysis_timestamp": datetime.now().isoformat(),
            "keyword": keyword,
            "data_sources": {
                "polymarket": polymarket_data.get("source", "mock"),
                "lunarcrush": lunarcrush_data.get("source", "mock")
            },
            "market_context": {
                "events": polymarket_data.get("events", []),
                "event_count": polymarket_data.get("event_count", 0)
            },
            "sentiment_context": {
                "coins": lunarcrush_data.get("coins", []),
                "coin_count": lunarcrush_data.get("coin_count", 0)
            },
            "summary": {}
        }
        
        # Calculate summary metrics
        merged["summary"] = self._calculate_summary_metrics(merged)
        
        logger.info(f"🧩 Merged context: {merged['market_context']['event_count']} events + {merged['sentiment_context']['coin_count']} coins")
        return merged
    
    def _calculate_summary_metrics(self, context: Dict) -> Dict[str, Any]:
        """Calculate summary metrics from merged context."""
        events = context["market_context"]["events"]
        coins = context["sentiment_context"]["coins"]
        
        summary = {
            "market_signals": {},
            "sentiment_signals": {},
            "overall_signal": "neutral"
        }
        
        # Analyze market signals from events
        if events:
            total_volume = sum(event.get("volume", 0) for event in events)
            avg_price = sum(event.get("price", 0.5) for event in events) / len(events)
            
            summary["market_signals"] = {
                "total_volume": total_volume,
                "average_price": avg_price,
                "event_count": len(events),
                "bullish_events": sum(1 for e in events if e.get("price", 0.5) > 0.6),
                "bearish_events": sum(1 for e in events if e.get("price", 0.5) < 0.4)
            }
        
        # Analyze sentiment signals from coins
        if coins:
            avg_sentiment_score = sum(coin.get("galaxy_score", 50) for coin in coins) / len(coins)
            avg_price_change = sum(coin.get("percent_change_24h", 0) for coin in coins) / len(coins)
            
            summary["sentiment_signals"] = {
                "average_galaxy_score": avg_sentiment_score,
                "average_price_change_24h": avg_price_change,
                "coin_count": len(coins),
                "bullish_coins": sum(1 for c in coins if c.get("percent_change_24h", 0) > 0),
                "bearish_coins": sum(1 for c in coins if c.get("percent_change_24h", 0) < 0)
            }
        
        # Determine overall signal
        if summary["market_signals"].get("average_price", 0.5) > 0.6 and summary["sentiment_signals"].get("average_price_change_24h", 0) > 0:
            summary["overall_signal"] = "bullish"
        elif summary["market_signals"].get("average_price", 0.5) < 0.4 and summary["sentiment_signals"].get("average_price_change_24h", 0) < 0:
            summary["overall_signal"] = "bearish"
        
        return summary
    
    async def _apply_reasoning_model(self, context: Dict, original_query: str) -> List[Dict[str, Any]]:
        """Apply built-in reasoning analysis to the merged context."""
        
        logger.info("🧠 Applying built-in reasoning analysis (no external LLM required)")
        
        try:
            # Use built-in analysis instead of LLM
            analysis_result = self._built_in_analysis(context, original_query)
            
            # Structure the response
            result = {
                "reasoning_analysis": analysis_result["analysis_text"],
                "context_summary": context["summary"],
                "recommendation": analysis_result["recommendation"],
                "confidence": analysis_result["confidence"],
                "data_sources": context["data_sources"],
                "analysis_timestamp": context["analysis_timestamp"],
                "analysis_method": "built_in_rules"
            }
            
            return [result]
            
        except Exception as e:
            logger.error(f"❌ Built-in reasoning failed: {e}")
            # Provide fallback analysis
            return [self._fallback_analysis(context, original_query)]
    
    def _built_in_analysis(self, context: Dict, query: str) -> Dict[str, Any]:
        """
        Built-in analysis engine that doesn't require external LLM.
        Uses rule-based analysis of market and sentiment data.
        """
        summary = context["summary"]
        keyword = context["keyword"]
        
        market_signals = summary.get("market_signals", {})
        sentiment_signals = summary.get("sentiment_signals", {})
        
        # Analyze market data
        market_score = 0
        market_reasoning = []
        
        if market_signals:
            avg_price = market_signals.get("average_price", 0.5)
            total_volume = market_signals.get("total_volume", 0)
            bullish_events = market_signals.get("bullish_events", 0)
            bearish_events = market_signals.get("bearish_events", 0)
            
            if avg_price > 0.6:
                market_score += 2
                market_reasoning.append(f"Prediction markets show bullish sentiment (avg price: {avg_price:.2f})")
            elif avg_price < 0.4:
                market_score -= 2
                market_reasoning.append(f"Prediction markets show bearish sentiment (avg price: {avg_price:.2f})")
            else:
                market_reasoning.append(f"Prediction markets show neutral sentiment (avg price: {avg_price:.2f})")
            
            if total_volume > 500000:
                market_score += 1
                market_reasoning.append(f"High market volume indicates strong interest (${total_volume:,.0f})")
            
            if bullish_events > bearish_events:
                market_score += 1
                market_reasoning.append(f"More bullish than bearish events ({bullish_events} vs {bearish_events})")
            elif bearish_events > bullish_events:
                market_score -= 1
                market_reasoning.append(f"More bearish than bullish events ({bearish_events} vs {bullish_events})")
        
        # Analyze sentiment data
        sentiment_score = 0
        sentiment_reasoning = []
        
        if sentiment_signals:
            avg_galaxy_score = sentiment_signals.get("average_galaxy_score", 50)
            avg_price_change = sentiment_signals.get("average_price_change_24h", 0)
            bullish_coins = sentiment_signals.get("bullish_coins", 0)
            bearish_coins = sentiment_signals.get("bearish_coins", 0)
            
            if avg_galaxy_score > 75:
                sentiment_score += 2
                sentiment_reasoning.append(f"High galaxy score indicates strong sentiment (avg: {avg_galaxy_score:.1f})")
            elif avg_galaxy_score < 50:
                sentiment_score -= 1
                sentiment_reasoning.append(f"Low galaxy score indicates weak sentiment (avg: {avg_galaxy_score:.1f})")
            else:
                sentiment_reasoning.append(f"Moderate galaxy score (avg: {avg_galaxy_score:.1f})")
            
            if avg_price_change > 2:
                sentiment_score += 2
                sentiment_reasoning.append(f"Strong positive price momentum (+{avg_price_change:.2f}%)")
            elif avg_price_change > 0:
                sentiment_score += 1
                sentiment_reasoning.append(f"Positive price momentum (+{avg_price_change:.2f}%)")
            elif avg_price_change < -2:
                sentiment_score -= 2
                sentiment_reasoning.append(f"Strong negative price momentum ({avg_price_change:.2f}%)")
            elif avg_price_change < 0:
                sentiment_score -= 1
                sentiment_reasoning.append(f"Negative price momentum ({avg_price_change:.2f}%)")
            
            if bullish_coins > bearish_coins:
                sentiment_score += 1
                sentiment_reasoning.append(f"More coins trending up than down ({bullish_coins} vs {bearish_coins})")
            elif bearish_coins > bullish_coins:
                sentiment_score -= 1
                sentiment_reasoning.append(f"More coins trending down than up ({bearish_coins} vs {bullish_coins})")
        
        # Combine scores and determine recommendation
        total_score = market_score + sentiment_score
        
        if total_score >= 3:
            position = "LONG"
            rationale = f"Strong bullish signals from both prediction markets and sentiment data (score: +{total_score})"
        elif total_score >= 1:
            position = "LONG"
            rationale = f"Moderate bullish signals (score: +{total_score})"
        elif total_score <= -3:
            position = "SHORT"
            rationale = f"Strong bearish signals from both prediction markets and sentiment data (score: {total_score})"
        elif total_score <= -1:
            position = "SHORT"
            rationale = f"Moderate bearish signals (score: {total_score})"
        else:
            position = "NEUTRAL"
            rationale = f"Mixed signals, no clear direction (score: {total_score})"
        
        # Determine confidence
        data_quality = len(market_reasoning) + len(sentiment_reasoning)
        if data_quality >= 6:
            confidence = "HIGH"
        elif data_quality >= 3:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        # Build comprehensive analysis text
        analysis_parts = [
            f"MARKET POSITION ANALYSIS FOR {keyword.upper()}:",
            "",
            "PREDICTION MARKET SIGNALS:",
        ]
        analysis_parts.extend([f"• {reason}" for reason in market_reasoning])
        analysis_parts.extend([
            "",
            "SENTIMENT SIGNALS:",
        ])
        analysis_parts.extend([f"• {reason}" for reason in sentiment_reasoning])
        analysis_parts.extend([
            "",
            f"COMBINED ANALYSIS SCORE: {total_score}",
            f"RECOMMENDATION: {position}",
            f"RATIONALE: {rationale}",
            f"CONFIDENCE: {confidence}"
        ])
        
        analysis_text = "\n".join(analysis_parts)
        
        return {
            "analysis_text": analysis_text,
            "recommendation": {
                "position": position,
                "rationale": rationale,
                "keyword": keyword,
                "score": total_score
            },
            "confidence": confidence,
            "market_score": market_score,
            "sentiment_score": sentiment_score
        }
    
    def _calculate_confidence(self, context: Dict) -> str:
        """Calculate confidence level based on data quality."""
        event_count = context["market_context"]["event_count"]
        coin_count = context["sentiment_context"]["coin_count"]
        
        if event_count >= 3 and coin_count >= 3:
            return "HIGH"
        elif event_count >= 1 and coin_count >= 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _fallback_analysis(self, context: Dict, query: str) -> Dict[str, Any]:
        """Provide fallback analysis when LLM reasoning fails."""
        summary = context["summary"]
        overall_signal = summary.get("overall_signal", "neutral")
        
        return {
            "reasoning_analysis": f"Based on available data for '{context['keyword']}', the market shows {overall_signal} signals.",
            "recommendation": {
                "position": overall_signal.upper() if overall_signal != "neutral" else "NEUTRAL",
                "rationale": f"Analysis based on {context['market_context']['event_count']} market events and {context['sentiment_context']['coin_count']} sentiment indicators.",
                "keyword": context["keyword"]
            },
            "confidence": self._calculate_confidence(context),
            "data_sources": context["data_sources"],
            "analysis_timestamp": context["analysis_timestamp"],
            "note": "Fallback analysis - LLM reasoning not available"
        }
    
    # Mock data methods for testing
    def _get_mock_polymarket_data(self, keyword: str) -> Dict[str, Any]:
        """Generate mock Polymarket data for testing."""
        mock_events = [
            {
                "title": f"{keyword} Election Outcome",
                "price": 0.65,
                "volume": 1250000,
                "status": "active",
                "category": "politics"
            },
            {
                "title": f"{keyword} Market Prediction", 
                "price": 0.58,
                "volume": 890000,
                "status": "active",
                "category": "general"
            }
        ]
        
        return {
            "source": "mock",
            "keyword": keyword,
            "events": mock_events,
            "event_count": len(mock_events)
        }
    
    def _get_mock_lunarcrush_data(self, keyword: str) -> Dict[str, Any]:
        """Generate mock LunarCrush data for testing."""
        mock_coins = [
            {
                "name": "Bitcoin",
                "symbol": "BTC", 
                "galaxy_score": 85.2,
                "percent_change_24h": 2.45,
                "sentiment": "Bullish"
            },
            {
                "name": "Ethereum",
                "symbol": "ETH",
                "galaxy_score": 82.7, 
                "percent_change_24h": 1.87,
                "sentiment": "Bullish"
            }
        ]
        
        return {
            "source": "mock",
            "keyword": keyword,
            "coins": mock_coins,
            "coin_count": len(mock_coins)
        }