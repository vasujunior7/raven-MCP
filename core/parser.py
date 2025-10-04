"""Query Parser — Natural language query understanding."""

import re
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class QueryParser:
    """Parses natural language queries into structured parameters."""
    
    def __init__(self, config_path: str = "config"):
        """Initialize parser with configuration files."""
        self.config_path = Path(config_path)
        self.keyword_map = self._load_keyword_map()
        self.defaults = self._load_defaults()
        
        # Regex patterns for common extractions
        self.limit_pattern = re.compile(r'\b(\d+)\b')
        self.time_patterns = {
            'today': re.compile(r'\btoday\b', re.IGNORECASE),
            'tomorrow': re.compile(r'\btomorrow\b', re.IGNORECASE),
            'this_week': re.compile(r'\bthis week\b', re.IGNORECASE),
            'next_week': re.compile(r'\bnext week\b', re.IGNORECASE)
        }
        
        logger.info("QueryParser initialized with keyword mappings and patterns")
    
    def _load_keyword_map(self) -> Dict[str, str]:
        """Load keyword to category mapping from config."""
        try:
            keyword_file = self.config_path / "keyword_map.json"
            if keyword_file.exists():
                with open(keyword_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load keyword map: {e}")
        
        # Default keyword mappings
        return {
            "trump": "politics",
            "election": "politics", 
            "biden": "politics",
            "president": "politics",
            "sports": "sports",
            "football": "sports",
            "basketball": "sports",
            "cricket": "sports",
            "soccer": "sports",
            "crypto": "crypto",
            "bitcoin": "crypto",
            "ethereum": "crypto",
            "technology": "technology",
            "ai": "technology",
            "climate": "environment"
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
        else:
            params = self._parse_generic(query_lower)
        
        params["tool"] = tool
        params["original_query"] = query
        
        logger.debug(f"Parsed result: {params}")
        return params
    
    def _infer_tool(self, query: str) -> str:
        """Infer the appropriate tool based on query content."""
        # Simple rule-based tool inference
        if any(word in query for word in ["fetch", "get", "show", "find", "list"]):
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
        """Extract main keyword/category from query."""
        # Check for direct keyword matches
        for keyword, category in self.keyword_map.items():
            if keyword in query:
                logger.debug(f"Found keyword '{keyword}' → category '{category}'")
                return category
        
        # Extract potential keywords using simple heuristics
        words = query.split()
        for word in words:
            word_clean = re.sub(r'[^\w]', '', word).lower()
            if word_clean in self.keyword_map:
                return self.keyword_map[word_clean]
        
        return self.defaults["default_category"]
    
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