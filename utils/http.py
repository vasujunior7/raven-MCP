"""HTTP Client utility for MCP Server."""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HTTPConfig:
    """Configuration for HTTP client."""
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    user_agent: str = "MCP-Server/1.0"

class HTTPClient:
    """
    Async HTTP client with retry logic and error handling.
    
    Provides a robust HTTP interface for external API calls with
    configurable timeouts, retries, and response handling.
    """
    
    def __init__(self, config: Optional[HTTPConfig] = None):
        """Initialize HTTP client with configuration."""
        self.config = config or HTTPConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"HTTPClient initialized with timeout={self.config.timeout}s")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
    
    async def start_session(self):
        """Start the HTTP session."""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {"User-Agent": self.config.user_agent}
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
            logger.debug("HTTP session started")
    
    async def close_session(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("HTTP session closed")
    
    async def close(self):
        """Alias for close_session for consistency."""
        await self.close_session()
    
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, 
                  headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Perform GET request with retry logic.
        
        Args:
            url: Target URL
            params: Query parameters
            headers: Additional headers
            
        Returns:
            JSON response as dictionary
            
        Raises:
            HTTPError: If request fails after all retries
        """
        return await self._request("GET", url, params=params, headers=headers)
    
    async def post(self, url: str, data: Optional[Union[Dict[str, Any], str]] = None,
                   json_data: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Perform POST request with retry logic.
        
        Args:
            url: Target URL
            data: Form data or raw string
            json_data: JSON data
            headers: Additional headers
            
        Returns:
            JSON response as dictionary
        """
        return await self._request("POST", url, data=data, json=json_data, headers=headers)
    
    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        Internal method to perform HTTP request with retry logic.
        """
        await self.start_session()
        
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    logger.debug(f"{method} {url} -> {response.status}")
                    
                    if response.status == 200:
                        try:
                            return await response.json()
                        except aiohttp.ContentTypeError:
                            # Handle non-JSON responses
                            text = await response.text()
                            return {"response": text}
                    
                    elif response.status in [429, 500, 502, 503, 504]:
                        # Retryable errors
                        if attempt < self.config.max_retries - 1:
                            wait_time = self.config.retry_delay * (2 ** attempt)
                            logger.warning(f"Retryable error {response.status}, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    # Non-retryable error or final attempt
                    error_text = await response.text()
                    raise HTTPError(f"HTTP {response.status}: {error_text}")
            
            except asyncio.TimeoutError:
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"Request timeout, retrying ({attempt + 1}/{self.config.max_retries})")
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                raise HTTPError("Request timed out after all retries")
            
            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"Client error: {e}, retrying ({attempt + 1}/{self.config.max_retries})")
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                raise HTTPError(f"HTTP client error: {str(e)}")
        
        raise HTTPError("Request failed after all retries")

class HTTPError(Exception):
    """Custom exception for HTTP-related errors."""
    pass

# Convenience functions for one-off requests
async def get_json(url: str, params: Optional[Dict[str, Any]] = None, 
                   config: Optional[HTTPConfig] = None) -> Dict[str, Any]:
    """Convenience function for single GET request."""
    async with HTTPClient(config) as client:
        return await client.get(url, params=params)

async def post_json(url: str, json_data: Optional[Dict[str, Any]] = None,
                    config: Optional[HTTPConfig] = None) -> Dict[str, Any]:
    """Convenience function for single POST request."""
    async with HTTPClient(config) as client:
        return await client.post(url, json_data=json_data)