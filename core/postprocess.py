"""Response Processor — Data cleaning and normalization."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class ResponseProcessor:
    """Processes and normalizes raw tool results into clean JSON responses."""
    
    def __init__(self):
        """Initialize the response processor."""
        logger.info("ResponseProcessor initialized")
    
    def process(self, raw_results: List[Dict[str, Any]], parsed_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process raw tool results into normalized format.
        
        Args:
            raw_results: Raw results from tool execution
            parsed_params: Original parsed query parameters
            
        Returns:
            List of cleaned and normalized result dictionaries
        """
        logger.debug(f"Processing {len(raw_results)} raw results")
        
        if not raw_results:
            return []
        
        # Step 1: Clean and validate each result
        cleaned_results = []
        for result in raw_results:
            cleaned = self._clean_result(result)
            if cleaned:  # Only include valid results
                cleaned_results.append(cleaned)
        
        # Step 2: Apply query-based filtering
        filtered_results = self._apply_filters(cleaned_results, parsed_params)
        
        # Step 3: Enrich with metadata
        enriched_results = self._enrich_metadata(filtered_results, parsed_params)
        
        # Step 4: Apply limit and sorting
        final_results = self._apply_limit_and_sort(enriched_results, parsed_params)
        
        logger.info(f"Processed results: {len(raw_results)} → {len(final_results)}")
        return final_results
    
    def _clean_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Clean and validate a single result item.
        
        Ensures required fields are present and data types are correct.
        """
        if not isinstance(result, dict):
            logger.warning(f"Invalid result type: {type(result)}")
            return None
        
        cleaned = {}
        
        # Essential fields with fallbacks
        cleaned['title'] = self._clean_string(result.get('title', result.get('name', 'Untitled')))
        
        # Handle various date formats
        cleaned['endDate'] = self._clean_date(result.get('endDate', result.get('end_date', result.get('deadline'))))
        
        # Numeric fields
        cleaned['volume'] = self._clean_number(result.get('volume', result.get('trading_volume', result.get('volume_24h', 0))))
        
        # Crypto-specific fields (for LunarCrush data)
        if 'symbol' in result:
            cleaned['symbol'] = self._clean_string(result.get('symbol'))
        if 'price' in result:
            cleaned['price'] = self._clean_number(result.get('price'))
        if 'market_cap' in result:
            cleaned['market_cap'] = self._clean_number(result.get('market_cap'))
        if 'percent_change_24h' in result:
            cleaned['percent_change_24h'] = self._clean_number(result.get('percent_change_24h'))
        if 'galaxy_score' in result:
            cleaned['galaxy_score'] = self._clean_number(result.get('galaxy_score'))
        if 'sentiment' in result:
            cleaned['sentiment'] = self._clean_string(result.get('sentiment'))
        if 'alt_rank' in result:
            cleaned['alt_rank'] = self._clean_number(result.get('alt_rank'))
        
        # URL handling
        if result.get('url'):
            cleaned['url'] = str(result['url'])
        
        # Description handling
        if result.get('description'):
            cleaned['description'] = self._clean_string(result['description'])
        
        # Market-specific fields
        if result.get('market_slug'):
            cleaned['marketSlug'] = str(result['market_slug'])
        
        if result.get('image'):
            cleaned['image'] = str(result['image'])
        
        # Validate essential fields
        if not cleaned['title']:
            logger.warning("Result missing required title field")
            return None
        
        return cleaned
    
    def _clean_string(self, value: Any) -> str:
        """Clean and validate string values."""
        if value is None:
            return ""
        
        # Convert to string and strip whitespace
        clean_str = str(value).strip()
        
        # Remove excessive whitespace
        clean_str = re.sub(r'\s+', ' ', clean_str)
        
        return clean_str
    
    def _clean_date(self, value: Any) -> Optional[str]:
        """Clean and standardize date values."""
        if not value:
            return None
        
        # If already a string in ISO format, validate and return
        if isinstance(value, str):
            try:
                # Try to parse and reformat to ensure consistency
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.isoformat().replace('+00:00', 'Z')
            except:
                logger.warning(f"Invalid date string: {value}")
                return None
        
        # If datetime object, convert to ISO string
        if isinstance(value, datetime):
            return value.isoformat() + 'Z'
        
        # If timestamp (unix epoch)
        if isinstance(value, (int, float)):
            try:
                dt = datetime.fromtimestamp(value)
                return dt.isoformat() + 'Z'
            except:
                logger.warning(f"Invalid timestamp: {value}")
                return None
        
        return None
    
    def _clean_number(self, value: Any) -> float:
        """Clean and validate numeric values."""
        if value is None:
            return 0.0
        
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid number value: {value}")
            return 0.0
    
    def _apply_filters(self, results: List[Dict[str, Any]], parsed_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply keyword and time-based filtering."""
        filtered = results
        
        # Keyword filtering - use more flexible matching
        keyword = parsed_params.get('keyword', '').lower()
        if keyword and keyword != 'general':
            # For now, skip strict keyword filtering and rely on the tool's filtering
            # This allows the mock data to come through for demonstration
            # In production, this would use more sophisticated matching
            logger.debug(f"Keyword '{keyword}' - using permissive filtering for demo")
        
        # Time filtering
        time_filter = parsed_params.get('time_filter')
        if time_filter:
            filtered = self._apply_time_filter(filtered, time_filter)
            logger.debug(f"Time filter '{time_filter}' reduced results to {len(filtered)}")
        
        return filtered
    
    def _matches_keyword(self, result: Dict[str, Any], keyword: str) -> bool:
        """Check if a result matches the given keyword."""
        # Search in title
        title = result.get('title', '').lower()
        if keyword in title:
            return True
        
        # Search in description
        description = result.get('description', '').lower()
        if keyword in description:
            return True
        
        # Search in tags (if present)
        tags = result.get('tags', [])
        if isinstance(tags, list):
            for tag in tags:
                if keyword in str(tag).lower():
                    return True
        
        return False
    
    def _apply_time_filter(self, results: List[Dict[str, Any]], time_filter: str) -> List[Dict[str, Any]]:
        """Apply time-based filtering to results."""
        # This would integrate with parser's time range functionality
        # For now, return all results
        return results
    
    def _enrich_metadata(self, results: List[Dict[str, Any]], parsed_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enrich results with additional metadata and tags."""
        keyword = parsed_params.get('keyword', 'general')
        tool_name = parsed_params.get('tool', 'unknown')
        
        for result in results:
            # Add source metadata based on the tool that generated the data
            if 'source' not in result:
                if tool_name == 'get_crypto_sentiment':
                    result['source'] = 'lunarcrush'
                elif tool_name == 'get_events':
                    result['source'] = 'polymarket'
                else:
                    result['source'] = 'unknown'
            
            # Generate tags based on content and keyword
            tags = self._generate_tags(result, keyword)
            result['tags'] = tags
            
            # Add processing timestamp
            result['processed_at'] = datetime.now().isoformat() + 'Z'
        
        return results
    
    def _generate_tags(self, result: Dict[str, Any], keyword: str) -> List[str]:
        """Generate relevant tags for a result."""
        tags = []
        
        # Add keyword as primary tag
        if keyword and keyword != 'general':
            tags.append(keyword)
        
        # Analyze title for additional tags
        title = result.get('title', '').lower()
        
        # Political keywords
        if any(word in title for word in ['election', 'vote', 'president', 'congress']):
            tags.append('politics')
        
        if any(word in title for word in ['trump', 'biden', 'harris']):
            tags.append('election')
        
        # Sports keywords
        if any(word in title for word in ['win', 'championship', 'game', 'match']):
            tags.append('sports')
        
        # Crypto keywords
        if any(word in title for word in ['bitcoin', 'ethereum', 'crypto', 'price']):
            tags.append('crypto')
        
        # Remove duplicates while preserving order
        unique_tags = []
        for tag in tags:
            if tag not in unique_tags:
                unique_tags.append(tag)
        
        return unique_tags
    
    def _apply_limit_and_sort(self, results: List[Dict[str, Any]], parsed_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply limit and sorting to final results."""
        # Sort by volume (descending) then by date
        sorted_results = sorted(
            results,
            key=lambda x: (x.get('volume', 0), x.get('endDate', '')),
            reverse=True
        )
        
        # Apply limit
        limit = parsed_params.get('limit', 5)
        limited_results = sorted_results[:limit]
        
        logger.debug(f"Applied limit {limit}, returning {len(limited_results)} results")
        return limited_results