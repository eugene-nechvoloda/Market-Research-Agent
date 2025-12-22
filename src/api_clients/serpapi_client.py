"""SerpAPI client for Google search results"""
import os
import requests
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SerpAPIClient:
    """Client for interacting with SerpAPI"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.base_url = "https://serpapi.com/search"

        if not self.api_key:
            raise ValueError("SerpAPI key not provided")

    def search(
        self,
        query: str,
        num_results: int = 10,
        time_filter: Optional[str] = None
    ) -> Dict:
        """
        Perform a Google search using SerpAPI

        Args:
            query: Search query
            num_results: Number of results to return
            time_filter: Time filter (e.g., "qdr:w" for past week, "qdr:m" for past month)

        Returns:
            Search results dictionary
        """
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "engine": "google"
            }

            if time_filter:
                params["tbs"] = time_filter

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            result = response.json()
            logger.info(f"SerpAPI search completed for query: {query}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"SerpAPI error: {str(e)}")
            return {"error": str(e), "organic_results": []}

    def search_news(
        self,
        query: str,
        num_results: int = 10,
        days_back: int = 7
    ) -> Dict:
        """
        Search for recent news articles

        Args:
            query: Search query
            num_results: Number of results
            days_back: How many days back to search

        Returns:
            News search results
        """
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "engine": "google",
                "tbm": "nws"  # News search
            }

            # Add time filter
            if days_back <= 1:
                params["tbs"] = "qdr:d"  # Past day
            elif days_back <= 7:
                params["tbs"] = "qdr:w"  # Past week
            elif days_back <= 30:
                params["tbs"] = "qdr:m"  # Past month

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            result = response.json()
            logger.info(f"SerpAPI news search completed for query: {query}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"SerpAPI news search error: {str(e)}")
            return {"error": str(e), "news_results": []}

    def search_multiple(
        self,
        queries: List[str],
        num_results: int = 10,
        time_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Perform multiple searches

        Args:
            queries: List of search queries
            num_results: Number of results per query
            time_filter: Optional time filter

        Returns:
            List of search results
        """
        results = []
        for query in queries:
            result = self.search(query, num_results, time_filter)
            results.append({
                "query": query,
                "result": result
            })
        return results
