"""LLM Reasoning Module for enhanced query processing."""

import os
import logging
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class RavenReasoner:
    """Uses Raven Reasoning Model for enhanced query understanding and analysis."""
    
    def __init__(self):
        """Initialize the Raven Reasoning Model client."""
        self.api_key = os.getenv('RAVEN_REASONING_MODEL_API_KEY')
        self.api_url = os.getenv('RAVEN_REASONING_MODEL_API_URL')
        self.model_name = os.getenv('RAVEN_REASONING_MODEL_DEPLOYMENT_NAME', 'raven-model')
        
        if not self.api_key or not self.api_url:
            logger.warning("Raven model credentials not found, using fallback mode")
            self.client = None
        else:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_url
            )
            logger.info("Raven Reasoning Model initialized successfully")
    
    async def enhance_query_understanding(self, query: str, parsed_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to enhance query understanding and extract better parameters.
        
        Args:
            query: Original natural language query
            parsed_params: Basic parsed parameters
            
        Returns:
            Enhanced parameters with LLM insights
        """
        if not self.client:
            logger.debug("LLM not available, returning original params")
            return parsed_params
        
        try:
            prompt = f"""
Analyze this prediction market query and enhance the parameters:

Query: "{query}"
Current params: {parsed_params}

Please provide enhanced parameters in JSON format with:
1. Better keyword extraction (politics, sports, crypto, technology, environment, economics, healthcare)
2. Improved limit reasoning
3. Time context understanding
4. Market intent analysis
5. Risk assessment level (low/medium/high)

Respond with only valid JSON:
"""

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert in prediction markets and query analysis. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            llm_response = response.choices[0].message.content.strip()
            logger.debug(f"LLM response: {llm_response}")
            
            # Parse LLM response
            import json
            try:
                enhanced_params = json.loads(llm_response)
                
                # Merge with original params, prioritizing LLM insights
                result = {**parsed_params, **enhanced_params}
                result['llm_enhanced'] = True
                result['original_query'] = query
                
                logger.info(f"Query enhanced by LLM: {query} -> {result.get('keyword', 'unknown')}")
                return result
                
            except json.JSONDecodeError:
                logger.warning("LLM response was not valid JSON, using original params")
                return parsed_params
                
        except Exception as e:
            logger.error(f"LLM enhancement failed: {e}")
            return parsed_params
    
    async def analyze_results(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use LLM to analyze and provide insights on the results.
        
        Args:
            query: Original query
            results: Market results
            
        Returns:
            Analysis and insights
        """
        if not self.client or not results:
            return {"analysis": "No analysis available"}
        
        try:
            # Prepare results summary for LLM
            results_summary = []
            for result in results[:5]:  # Limit to top 5 for token efficiency
                summary = {
                    "title": result.get("title", ""),
                    "volume": result.get("volume", 0),
                    "end_date": result.get("endDate", ""),
                    "tags": result.get("tags", [])
                }
                results_summary.append(summary)
            
            prompt = f"""
Analyze these prediction market results for the query: "{query}"

Results: {results_summary}

Provide insights including:
1. Market sentiment analysis
2. Risk assessment
3. Key trends identified
4. Notable patterns in volume or timing
5. Recommended next actions

Respond with JSON containing your analysis:
"""

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a prediction market analyst providing insights on market data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=600
            )
            
            llm_response = response.choices[0].message.content.strip()
            
            # Parse LLM analysis
            import json
            try:
                analysis = json.loads(llm_response)
                analysis['llm_generated'] = True
                return analysis
            except json.JSONDecodeError:
                return {"analysis": llm_response, "llm_generated": True}
                
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {"analysis": "Analysis unavailable", "error": str(e)}
    
    async def suggest_related_queries(self, query: str, results: List[Dict[str, Any]]) -> List[str]:
        """
        Generate related query suggestions based on current query and results.
        
        Args:
            query: Original query
            results: Current results
            
        Returns:
            List of suggested related queries
        """
        if not self.client:
            return []
        
        try:
            prompt = f"""
Based on this prediction market query and results, suggest 3-5 related queries that users might find interesting:

Original query: "{query}"
Number of results: {len(results)}
Sample titles: {[r.get('title', '')[:50] + '...' for r in results[:3]]}

Provide suggestions as a JSON array of strings:
"""

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant suggesting related prediction market queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=300
            )
            
            llm_response = response.choices[0].message.content.strip()
            
            import json
            try:
                suggestions = json.loads(llm_response)
                if isinstance(suggestions, list):
                    return suggestions[:5]  # Limit to 5 suggestions
                return []
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            logger.error(f"Query suggestion failed: {e}")
            return []

# Global reasoner instance
reasoner = RavenReasoner()