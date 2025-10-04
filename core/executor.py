"""Tool Executor — Executes tools with error handling and retries."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ToolExecutor:
    """Executes tools with parsed parameters and handles results."""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize executor with configuration.
        
        Args:
            timeout: Maximum execution time per tool in seconds
            max_retries: Maximum retry attempts for failed executions
        """
        self.timeout = timeout
        self.max_retries = max_retries
        
        logger.info(f"ToolExecutor initialized (timeout={timeout}s, retries={max_retries})")
    
    async def execute(self, tool_instance: Any, parsed_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute a tool with the given parameters.
        
        Args:
            tool_instance: Tool object to execute
            parsed_params: Parameters from query parser
            
        Returns:
            List of result dictionaries from tool execution
            
        Raises:
            Exception: If execution fails after all retries
        """
        tool_name = getattr(tool_instance, 'tool_name', 'unknown')
        logger.info(f"Executing tool '{tool_name}' with params: {parsed_params}")
        
        start_time = datetime.now()
        
        for attempt in range(self.max_retries):
            try:
                # Execute tool with timeout
                result = await asyncio.wait_for(
                    self._execute_tool(tool_instance, parsed_params),
                    timeout=self.timeout
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Tool '{tool_name}' executed successfully in {execution_time:.2f}s")
                
                return result
                
            except asyncio.TimeoutError:
                logger.warning(f"Tool '{tool_name}' timed out (attempt {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Tool execution timed out after {self.timeout}s")
                    
            except Exception as e:
                logger.warning(f"Tool '{tool_name}' failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Tool execution failed: {str(e)}")
                
                # Wait before retry (exponential backoff)
                await asyncio.sleep(2 ** attempt)
        
        return []  # Should not reach here
    
    async def _execute_tool(self, tool_instance: Any, parsed_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Internal method to execute a specific tool.
        
        Handles both sync and async tool implementations.
        """
        try:
            # Check if tool has async execute method
            if hasattr(tool_instance, 'execute') and callable(tool_instance.execute):
                result = tool_instance.execute(parsed_params)
                
                # Handle async results
                if asyncio.iscoroutine(result):
                    result = await result
                
                # Ensure result is a list
                if not isinstance(result, list):
                    result = [result] if result is not None else []
                
                return result
            else:
                raise AttributeError(f"Tool does not have an 'execute' method")
                
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            raise
    
    async def execute_multiple(self, tool_executions: List[tuple]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Execute multiple tools concurrently.
        
        Args:
            tool_executions: List of (tool_instance, parsed_params) tuples
            
        Returns:
            Dictionary mapping tool names to their results
        """
        tasks = []
        tool_names = []
        
        for tool_instance, parsed_params in tool_executions:
            tool_name = getattr(tool_instance, 'tool_name', 'unknown')
            task = self.execute(tool_instance, parsed_params)
            tasks.append(task)
            tool_names.append(tool_name)
        
        logger.info(f"Executing {len(tasks)} tools concurrently")
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            combined_results = {}
            for tool_name, result in zip(tool_names, results):
                if isinstance(result, Exception):
                    logger.error(f"Tool '{tool_name}' failed: {result}")
                    combined_results[tool_name] = []
                else:
                    combined_results[tool_name] = result
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Concurrent execution failed: {e}")
            raise
    
    def validate_tool(self, tool_instance: Any) -> bool:
        """
        Validate that a tool instance meets the required interface.
        
        Args:
            tool_instance: Tool object to validate
            
        Returns:
            True if tool is valid, False otherwise
        """
        required_attributes = ['tool_name', 'execute']
        
        for attr in required_attributes:
            if not hasattr(tool_instance, attr):
                logger.error(f"Tool missing required attribute: {attr}")
                return False
        
        if not callable(tool_instance.execute):
            logger.error("Tool 'execute' attribute is not callable")
            return False
        
        return True
    
    async def health_check_tool(self, tool_instance: Any) -> Dict[str, Any]:
        """
        Perform a health check on a specific tool.
        
        Returns:
            Health status information
        """
        tool_name = getattr(tool_instance, 'tool_name', 'unknown')
        
        try:
            # Validate tool interface
            if not self.validate_tool(tool_instance):
                return {
                    "tool": tool_name,
                    "status": "unhealthy",
                    "reason": "Invalid tool interface"
                }
            
            # Check if tool has a health_check method
            if hasattr(tool_instance, 'health_check'):
                health_result = tool_instance.health_check()
                if asyncio.iscoroutine(health_result):
                    health_result = await health_result
                
                return {
                    "tool": tool_name,
                    "status": "healthy",
                    "details": health_result
                }
            
            return {
                "tool": tool_name,
                "status": "healthy",
                "reason": "Basic validation passed"
            }
            
        except Exception as e:
            return {
                "tool": tool_name,
                "status": "unhealthy",
                "reason": str(e)
            }