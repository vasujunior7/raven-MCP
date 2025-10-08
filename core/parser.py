"""Query Parser — Natural language query understanding."""

import re
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta

# Import fuzzy matching for typo tolerance
try:
    from fuzzywuzzy import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logging.warning("fuzzywuzzy not available - typo tolerance disabled")

logger = logging.getLogger(__name__)

class QueryParser:
    """Parses natural language queries into structured parameters."""
    
    def __init__(self, config_path: str = "config"):
        """Initialize parser with configuration files."""
        self.config_path = Path(config_path)
        self.keyword_map = self._load_keyword_map()
        self.defaults = self._load_defaults()
        
        # Initialize fuzzy matching if available
        self.fuzzy_enabled = FUZZY_AVAILABLE
        if self.fuzzy_enabled:
            logger.info("Fuzzy matching enabled for typo tolerance")
        else:
            logger.warning("Fuzzy matching disabled - install fuzzywuzzy for better typo handling")
        
        # Regex patterns for common extractions
        self.limit_pattern = re.compile(r'\b(\d+)\b')
        self.time_patterns = {
            'today': re.compile(r'\btoday\b', re.IGNORECASE),
            'tomorrow': re.compile(r'\btomorrow\b', re.IGNORECASE),
            'this_week': re.compile(r'\bthis week\b', re.IGNORECASE),
            'next_week': re.compile(r'\bnext week\b', re.IGNORECASE)
        }
        
        logger.info("QueryParser initialized with enhanced keyword mappings and fuzzy matching")
    
    def _load_keyword_map(self) -> Dict[str, str]:
        """Load keyword to category mapping from config."""
        try:
            keyword_file = self.config_path / "keyword_map.json"
            if keyword_file.exists():
                with open(keyword_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load keyword map: {e}")
        
        # Enhanced keyword mappings for better categorization
        return {
            # Politics & Elections (direct mappings to our supported categories)
            "trump": "politics",
            "election": "politics", 
            "biden": "politics",
            "president": "politics",
            "politics": "politics",
            "political": "politics",
            "poltics": "politics",  # Common typo
            "politcs": "politics",  # Common typo
            "government": "politics",
            "congress": "politics",
            "senate": "politics",
            "vote": "politics",
            "voting": "politics",
            
            # Sports (direct mappings to our supported categories)
            "sports": "sports",
            "sport": "sports",
            "football": "sports",
            "basketball": "sports",
            "cricket": "sports",
            "soccer": "sports",
            "nfl": "sports",
            "nba": "sports",
            "olympics": "sports",
            "championship": "sports",
            "league": "sports",
            "game": "sports",
            "team": "sports",
            "player": "sports",
            "match": "sports",
            
            # Crypto & Finance (direct mappings to our supported categories)
            "crypto": "crypto",
            "cryptp": "crypto",  # Common typo
            "cryto": "crypto",   # Common typo
            "cryptocurrency": "crypto",
            "bitcoin": "crypto",
            "ethereum": "crypto",
            "btc": "crypto",
            "eth": "crypto",
            "blockchain": "crypto",
            "defi": "crypto",
            
            # General event terms (lower priority - should come after specific categories)
            "prediction": "general",
            "event": "general",
            "events": "general",
            
            # Technology (fallback category)
            "technology": "technology",
            "tech": "technology",
            "ai": "technology",
            "artificial": "technology",
            "tesla": "technology",
            "meta": "technology",
            "google": "technology",
            "apple": "technology",
            
            # Economics (fallback category)
            "economics": "economics",
            "economy": "economics",
            "inflation": "economics",
            "recession": "economics",
            "oil": "economics",
            "price": "economics",
            "stock": "economics",
            
            # Environment
            "climate": "environment",
            "environment": "environment",
            "global": "environment",
            "warming": "environment"
        }
    
    def _load_defaults(self) -> Dict[str, Any]:
        """Load default configuration values."""
        try:
            defaults_file = self.config_path / "defaults.json"
            if defaults_file.exists():
                with open(defaults_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load defaults: {e}")
        
        # Default settings
        return {
            "default_limit": 5,
            "max_limit": 50,
            "default_tool": "get_events",
            "default_category": "general"
        }
    
    def parse(self, query: str, explicit_tool: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse a natural language query into structured parameters.
        
        Args:
            query: Natural language query
            explicit_tool: Optional explicit tool name to use
            
        Returns:
            Dictionary with parsed parameters including tool, keyword, limit, etc.
        """
        logger.debug(f"Parsing query: '{query}'")
        
        query_lower = query.lower().strip()
        
        # Determine tool (explicit or inferred)
        tool = explicit_tool or self._infer_tool(query_lower)
        
        # Extract parameters based on tool type
        if tool == "get_events":
            params = self._parse_get_events(query_lower)
        elif tool == "get_crypto_sentiment":
            params = self._parse_get_crypto_sentiment(query_lower)
        else:
            params = self._parse_generic(query_lower)
        
        params["tool"] = tool
        params["original_query"] = query
        
        logger.debug(f"Parsed result: {params}")
        return params
    
    def _infer_tool(self, query: str) -> str:
        """Infer the appropriate tool based on query content."""
        query_lower = query.lower()
        
        # Check for explicit tool mentions first (highest priority)
        if "polymarket" in query_lower:
            return "get_events"
        
        if "lunarcrush" in query_lower:
            return "get_crypto_sentiment"
        
        # Market/prediction/event related queries -> Polymarket (high priority)
        market_keywords = ["event", "prediction", "market", "bet", "odds", "election", "sports", "politics"]
        if any(keyword in query_lower for keyword in market_keywords):
            return "get_events"
        
        # Cryptocurrency/sentiment related queries without events context -> LunarCrush
        crypto_keywords = [
            "crypto", "cryptocurrency", "bitcoin", "ethereum", "altcoin", "sentiment", 
            "trending", "coins", "market cap", "social", "buzz", "influence", "price", "galaxy"
        ]
        
        # Only route to crypto tool if no event/market context
        if (any(keyword in query_lower for keyword in crypto_keywords) and 
            not any(keyword in query_lower for keyword in market_keywords)):
            return "get_crypto_sentiment"
        
        # Default fallback for general queries
        if any(word in query_lower for word in ["fetch", "get", "show", "find", "list"]):
            return "get_events"
        
        return self.defaults["default_tool"]
    
    def _parse_get_events(self, query: str) -> Dict[str, Any]:
        """Parse parameters specific to get_events tool."""
        params = {}
        
        # Extract limit/count
        params["limit"] = self._extract_limit(query)
        
        # Extract keyword/category
        params["keyword"] = self._extract_keyword(query)
        
        # Extract time constraints
        time_filter = self._extract_time_filter(query)
        if time_filter:
            params["time_filter"] = time_filter
        
        return params
    
    def _parse_get_crypto_sentiment(self, query: str) -> Dict[str, Any]:
        """Parse parameters specific to get_crypto_sentiment tool."""
        params = {}
        
        # Extract limit/count
        params["limit"] = self._extract_limit(query)
        
        # Extract sort type
        if "trending" in query:
            params["sort"] = "gs"  # Galaxy Score (trending)
        elif "market cap" in query or "cap" in query:
            params["sort"] = "mc"  # Market Cap
        elif "volume" in query:
            params["sort"] = "v"   # Volume
        else:
            params["sort"] = "gs"  # Default to trending
        
        # Extract category/keyword
        params["keyword"] = self._extract_keyword(query)
        
        return params
    
    def _parse_generic(self, query: str) -> Dict[str, Any]:
        """Parse generic parameters for unknown tools."""
        return {
            "keyword": self._extract_keyword(query),
            "limit": self._extract_limit(query)
        }
    
    def _extract_limit(self, query: str) -> int:
        """Extract numeric limit from query."""
        matches = self.limit_pattern.findall(query)
        if matches:
            limit = int(matches[0])
            # Clamp to reasonable bounds
            return min(limit, self.defaults["max_limit"])
        
        return self.defaults["default_limit"]
    
    def _extract_keyword(self, query: str) -> str:
        """Extract main keyword/category from query with improved detection and fuzzy matching."""
        query_lower = query.lower().strip()
        
        # Step 1: Clean query - handle common phrases
        query_clean = self._normalize_query(query_lower)
        
        # Step 2: Priority matching - check for specific categories first
        category_priorities = ['crypto', 'cryptp', 'cryto', 'politics', 'poltics', 'politcs', 'sports', 'sport']
        
        for priority_keyword in category_priorities:
            if priority_keyword in query_clean:
                category = self.keyword_map.get(priority_keyword, self.defaults["default_category"])
                logger.debug(f"Found priority keyword '{priority_keyword}' → category '{category}'")
                return category
        
        # Step 3: Check for direct keyword matches (exact substring matching)
        for keyword, category in self.keyword_map.items():
            if keyword in query_clean and category in ['crypto', 'politics', 'sports']:
                logger.debug(f"Found exact keyword '{keyword}' → category '{category}'")
                return category
        
        # Step 4: Fuzzy matching for typos and variations
        if FUZZY_AVAILABLE:
            best_match = self._fuzzy_match_category(query_clean)
            if best_match:
                logger.debug(f"Fuzzy matched '{query_clean}' → category '{best_match}'")
                return best_match
        
        # Step 5: Word-by-word analysis with priority
        words = query_clean.split()
        for word in words:
            word_clean = re.sub(r'[^\w]', '', word)
            if word_clean in self.keyword_map:
                category = self.keyword_map[word_clean]
                # Prioritize our main categories
                if category in ['crypto', 'politics', 'sports']:
                    logger.debug(f"Found priority word '{word_clean}' → category '{category}'")
                    return category
            
            # Fuzzy match individual words
            if FUZZY_AVAILABLE and len(word_clean) > 3:
                fuzzy_category = self._fuzzy_match_word(word_clean)
                if fuzzy_category:
                    logger.debug(f"Fuzzy matched word '{word_clean}' → category '{fuzzy_category}'")
                    return fuzzy_category
        
        # Step 6: Fallback to any keyword match
        for keyword, category in self.keyword_map.items():
            if keyword in query_clean:
                logger.debug(f"Found fallback keyword '{keyword}' → category '{category}'")
                return category
        
        # Step 7: Default fallback
        logger.debug(f"No specific keyword found in '{query}', using default category")
        return self.defaults["default_category"]
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query by handling common phrases and patterns."""
        # Handle common conversation patterns
        patterns = [
            (r'\b(fetch|get|show|give)\s+me\s+', ''),  # "fetch me crypto" -> "crypto"
            (r'\b(find|list|display)\s+', ''),         # "find politics" -> "politics"
            (r'\bevents?\s+for\s+', ''),               # "events for sports" -> "sports"
            (r'\b(some|any)\s+', ''),                  # "some crypto events" -> "crypto events"
        ]
        
        normalized = query
        for pattern, replacement in patterns:
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized.strip()
    
    def _fuzzy_match_category(self, query: str) -> Optional[str]:
        """Use fuzzy matching to find the best category match."""
        if not FUZZY_AVAILABLE:
            return None
        
        # Define our target categories for fuzzy matching
        target_categories = ['sports', 'politics', 'crypto']
        
        # Try fuzzy matching against category names
        for category in target_categories:
            if fuzz.partial_ratio(category, query) > 80:  # High threshold for category names
                return category
        
        # Try fuzzy matching against all keywords
        keywords = list(self.keyword_map.keys())
        best_matches = process.extractBests(query, keywords, score_cutoff=75, limit=3)
        
        for match, score in best_matches:
            category = self.keyword_map[match]
            if category in target_categories:  # Only return supported categories
                logger.debug(f"Fuzzy match: '{query}' → '{match}' (score: {score}) → '{category}'")
                return category
        
        return None
    
    def _fuzzy_match_word(self, word: str) -> Optional[str]:
        """Fuzzy match a single word against keywords."""
        if not FUZZY_AVAILABLE or len(word) < 4:
            return None
        
        # Target our supported categories
        target_categories = ['sports', 'politics', 'crypto']
        
        # Get keywords for supported categories only
        relevant_keywords = {k: v for k, v in self.keyword_map.items() if v in target_categories}
        
        best_match = process.extractOne(word, relevant_keywords.keys(), score_cutoff=80)
        if best_match:
            keyword, score = best_match
            category = relevant_keywords[keyword]
            logger.debug(f"Fuzzy word match: '{word}' → '{keyword}' (score: {score}) → '{category}'")
            return category
        
        return None
    
    def _extract_time_filter(self, query: str) -> Optional[str]:
        """Extract time-based filters from query."""
        for time_key, pattern in self.time_patterns.items():
            if pattern.search(query):
                logger.debug(f"Found time filter: {time_key}")
                return time_key
        
        return None
    
    def get_time_range(self, time_filter: str) -> Dict[str, datetime]:
        """Convert time filter to actual datetime range."""
        now = datetime.now()
        
        if time_filter == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif time_filter == "tomorrow":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            end = start + timedelta(days=1)
        elif time_filter == "this_week":
            days_since_monday = now.weekday()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
            end = start + timedelta(days=7)
        elif time_filter == "next_week":
            days_since_monday = now.weekday()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday) + timedelta(days=7)
            end = start + timedelta(days=7)
        else:
            return {}
        
        return {"start": start, "end": end}