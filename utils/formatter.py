"""Response formatter utility for MCP Server."""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class ResponseFormatter:
    """
    Formats responses for different output types and clients.
    
    Supports console tables, JSON formatting, and structured display
    for various client interfaces (CLI, web, etc.).
    """
    
    def __init__(self):
        """Initialize the response formatter."""
        logger.debug("ResponseFormatter initialized")
    
    def format_table(self, results: List[Dict[str, Any]], 
                    columns: Optional[List[str]] = None,
                    max_width: int = 80) -> str:
        """
        Format results as a console table.
        
        Args:
            results: List of result dictionaries
            columns: Specific columns to display
            max_width: Maximum width for content columns
            
        Returns:
            Formatted table string
        """
        if not results:
            return "No results found."
        
        # Determine columns to display
        if not columns:
            columns = self._get_display_columns(results)
        
        # Calculate column widths
        col_widths = self._calculate_column_widths(results, columns, max_width)
        
        # Build table
        table_lines = []
        
        # Header
        header = " | ".join(col.title().ljust(col_widths[col]) for col in columns)
        table_lines.append(header)
        table_lines.append("-" * len(header))
        
        # Rows
        for result in results:
            row_parts = []
            for col in columns:
                value = self._format_cell_value(result.get(col, ""), col)
                truncated = self._truncate_text(str(value), col_widths[col])
                row_parts.append(truncated.ljust(col_widths[col]))
            
            table_lines.append(" | ".join(row_parts))
        
        return "\n".join(table_lines)
    
    def format_json(self, data: Any, pretty: bool = True) -> str:
        """
        Format data as JSON string.
        
        Args:
            data: Data to format
            pretty: Whether to pretty-print with indentation
            
        Returns:
            JSON string
        """
        try:
            if pretty:
                return json.dumps(data, indent=2, default=self._json_serializer, ensure_ascii=False)
            else:
                return json.dumps(data, default=self._json_serializer, ensure_ascii=False)
        except Exception as e:
            logger.error(f"JSON formatting error: {e}")
            return str(data)
    
    def format_summary(self, results: List[Dict[str, Any]], 
                      query: str = "") -> str:
        """
        Format a summary of results.
        
        Args:
            results: List of result dictionaries
            query: Original query string
            
        Returns:
            Formatted summary string
        """
        summary_lines = []
        
        if query:
            summary_lines.append(f"Query: '{query}'")
        
        summary_lines.append(f"Results: {len(results)} found")
        
        if results:
            # Show basic stats
            total_volume = sum(result.get('volume', 0) for result in results)
            summary_lines.append(f"Total Volume: {self._format_number(total_volume)}")
            
            # Show categories/tags
            all_tags = []
            for result in results:
                tags = result.get('tags', [])
                if isinstance(tags, list):
                    all_tags.extend(tags)
            
            unique_tags = list(set(all_tags))
            if unique_tags:
                summary_lines.append(f"Categories: {', '.join(unique_tags[:5])}")
        
        return "\n".join(summary_lines)
    
    def format_cards(self, results: List[Dict[str, Any]]) -> str:
        """
        Format results as individual cards.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            Formatted cards string
        """
        if not results:
            return "No results found."
        
        card_lines = []
        
        for i, result in enumerate(results, 1):
            card_lines.append(f"━━━ Result {i} ━━━")
            card_lines.append(f"Title: {result.get('title', 'Untitled')}")
            
            # Crypto-specific card formatting
            if result.get('symbol'):
                card_lines.append(f"Symbol: {result['symbol']}")
            
            if result.get('price'):
                formatted_price = self._format_cell_value(result['price'], 'price')
                card_lines.append(f"Price: {formatted_price}")
            
            if result.get('market_cap'):
                formatted_mcap = self._format_cell_value(result['market_cap'], 'market_cap')
                card_lines.append(f"Market Cap: {formatted_mcap}")
            
            if result.get('galaxy_score'):
                formatted_score = self._format_cell_value(result['galaxy_score'], 'galaxy_score')
                card_lines.append(f"Galaxy Score: {formatted_score}")
            
            if result.get('sentiment'):
                formatted_sentiment = self._format_cell_value(result['sentiment'], 'sentiment')
                card_lines.append(f"Sentiment: {formatted_sentiment}")
            
            if result.get('percent_change_24h'):
                change = result['percent_change_24h']
                change_emoji = "📈" if change >= 0 else "📉"
                card_lines.append(f"24h Change: {change_emoji} {change:+.2f}%")
            
            # Standard fields for non-crypto data
            if result.get('endDate'):
                formatted_date = self._format_date(result['endDate'])
                card_lines.append(f"End Date: {formatted_date}")
            
            if result.get('volume'):
                formatted_volume = self._format_number(result['volume'])
                card_lines.append(f"Volume: {formatted_volume}")
            
            if result.get('tags'):
                tags = result['tags']
                if isinstance(tags, list):
                    card_lines.append(f"Tags: {', '.join(tags)}")
            
            if result.get('description'):
                description = self._truncate_text(result['description'], 100)
                card_lines.append(f"Description: {description}")
            
            card_lines.append("")  # Empty line between cards
        
        return "\n".join(card_lines)
    
    def _get_display_columns(self, results: List[Dict[str, Any]]) -> List[str]:
        """Determine which columns to display based on available data."""
        if not results:
            return []
        
        # Check what kind of data we have
        first_result = results[0]
        
        # Crypto/LunarCrush data detection
        crypto_fields = ['symbol', 'price', 'galaxy_score', 'sentiment', 'market_cap']
        if any(field in first_result for field in crypto_fields):
            # This is crypto sentiment data - show crypto-specific columns
            priority_columns = ['title', 'symbol', 'price', 'galaxy_score', 'sentiment', 'market_cap']
        else:
            # Default columns for markets/events
            priority_columns = ['title', 'endDate', 'volume', 'tags']
        
        # Find available columns
        all_columns = set()
        for result in results:
            all_columns.update(result.keys())
        
        # Return priority columns that exist in data
        display_columns = []
        for col in priority_columns:
            if col in all_columns:
                display_columns.append(col)
        
        # Add other important columns
        for col in ['url', 'description']:
            if col in all_columns and col not in display_columns and len(display_columns) < 6:
                display_columns.append(col)
        
        return display_columns[:6]  # Limit to 6 columns for crypto data
    
    def _calculate_column_widths(self, results: List[Dict[str, Any]], 
                                columns: List[str], max_width: int) -> Dict[str, int]:
        """Calculate optimal column widths for table display."""
        col_widths = {}
        
        # Start with minimum widths
        for col in columns:
            col_widths[col] = max(len(col), 8)  # At least column name length or 8
        
        # Adjust based on content
        for result in results:
            for col in columns:
                value = str(result.get(col, ""))
                col_widths[col] = max(col_widths[col], min(len(value), 30))
        
        # Distribute remaining width
        total_width = sum(col_widths.values()) + (len(columns) - 1) * 3  # 3 for " | "
        
        if total_width > max_width:
            # Reduce widths proportionally
            excess = total_width - max_width
            reduction_per_col = excess // len(columns)
            
            for col in columns:
                col_widths[col] = max(col_widths[col] - reduction_per_col, 8)
        
        return col_widths
    
    def _format_cell_value(self, value: Any, column: str) -> str:
        """Format a cell value based on its type and column."""
        if value is None:
            return ""
        
        # Crypto-specific formatting
        if column == 'price':
            try:
                price = float(value)
                if price >= 1:
                    return f"${price:,.2f}"
                else:
                    return f"${price:.4f}"
            except (ValueError, TypeError):
                return str(value)
        elif column == 'galaxy_score':
            try:
                score = float(value)
                return f"{score:.1f}⭐"
            except (ValueError, TypeError):
                return str(value)
        elif column == 'market_cap':
            return self._format_number(value, prefix="$")
        elif column == 'sentiment':
            # Add emoji to sentiment
            sentiment_str = str(value).lower()
            if 'bullish' in sentiment_str:
                return f"📈 {value}"
            elif 'bearish' in sentiment_str:
                return f"📉 {value}"
            elif 'neutral' in sentiment_str:
                return f"➖ {value}"
            else:
                return str(value)
        elif column == 'symbol':
            return f"({value})"
        # Generic formatting
        elif column == 'volume':
            return self._format_number(value)
        elif column == 'endDate':
            return self._format_date(value)
        elif column == 'tags' and isinstance(value, list):
            return ", ".join(str(tag) for tag in value[:3])  # Show first 3 tags
        else:
            return str(value)
    
    def _format_number(self, value: Any, prefix: str = "") -> str:
        """Format numeric values with appropriate units."""
        try:
            num = float(value)
            if num >= 1_000_000_000:
                return f"{prefix}{num/1_000_000_000:.1f}B"
            elif num >= 1_000_000:
                return f"{prefix}{num/1_000_000:.1f}M"
            elif num >= 1_000:
                return f"{prefix}{num/1_000:.1f}K"
            else:
                return f"{prefix}{num:.0f}"
        except (ValueError, TypeError):
            return str(value)
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        try:
            # Parse ISO date
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except:
            return str(date_str)
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to fit in specified length."""
        if len(text) <= max_length:
            return text
        
        if max_length <= 3:
            return "..."
        
        return text[:max_length-3] + "..."
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime and other objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

# Global formatter instance
formatter = ResponseFormatter()