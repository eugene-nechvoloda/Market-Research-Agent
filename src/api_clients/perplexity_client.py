"""Perplexity API client for web searches"""
import os
import requests
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PerplexityClient:
    """Client for interacting with Perplexity API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai"

        if not self.api_key:
            raise ValueError("Perplexity API key not provided")

    def search(self, query: str, recency_filter: Optional[str] = None) -> Dict:
        """
        Perform a search using Perplexity API

        Args:
            query: Search query
            recency_filter: Optional filter like "week", "month", etc.

        Returns:
            Search results dictionary
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a research assistant. Provide factual, sourced information with URLs."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "return_citations": True,
                "search_recency_filter": recency_filter or "month"
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Perplexity search completed for query: {query}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Perplexity API error: {str(e)}")
            return {"error": str(e), "content": None}

    def search_multiple(self, queries: List[str], recency_filter: Optional[str] = None) -> List[Dict]:
        """
        Perform multiple searches

        Args:
            queries: List of search queries
            recency_filter: Optional recency filter

        Returns:
            List of search results
        """
        results = []
        for query in queries:
            result = self.search(query, recency_filter)
            results.append({
                "query": query,
                "result": result
            })
        return results
