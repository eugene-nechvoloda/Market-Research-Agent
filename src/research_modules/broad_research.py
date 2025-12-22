"""Broad market research module using Perplexity and SerpAPI"""
import logging
from typing import Dict, List
from datetime import datetime
from ..api_clients import PerplexityClient, SerpAPIClient

logger = logging.getLogger(__name__)


class BroadResearchModule:
    """Module for conducting broad DAP market research"""

    def __init__(self, perplexity_client: PerplexityClient, serpapi_client: SerpAPIClient):
        self.perplexity = perplexity_client
        self.serpapi = serpapi_client

    def research_market_trends(self) -> Dict:
        """
        Research general DAP market trends and news

        Returns:
            Dictionary containing market research results
        """
        logger.info("Starting broad market research...")

        queries = [
            "Digital Adoption Platform market trends 2025",
            "DAP market size growth rate 2025",
            "Digital adoption platform acquisitions 2025",
            "DAP investment rounds funding 2025",
            "Digital adoption platform industry reports 2025"
        ]

        results = {
            "market_trends": [],
            "market_size_data": [],
            "industry_reports": [],
            "timestamp": datetime.now().isoformat()
        }

        # Use Perplexity for comprehensive market analysis
        for query in queries:
            logger.info(f"Researching: {query}")
            perplexity_result = self.perplexity.search(query, recency_filter="week")

            if perplexity_result.get("choices"):
                content = perplexity_result["choices"][0]["message"]["content"]
                citations = perplexity_result.get("citations", [])

                if "market size" in query.lower() or "growth rate" in query.lower():
                    results["market_size_data"].append({
                        "query": query,
                        "content": content,
                        "citations": citations
                    })
                elif "industry report" in query.lower():
                    results["industry_reports"].append({
                        "query": query,
                        "content": content,
                        "citations": citations
                    })
                else:
                    results["market_trends"].append({
                        "query": query,
                        "content": content,
                        "citations": citations
                    })

        # Use SerpAPI for additional news search
        news_queries = [
            "Digital Adoption Platform news",
            "DAP market news",
            "digital adoption trends"
        ]

        results["recent_news"] = []
        for query in news_queries:
            serpapi_result = self.serpapi.search_news(query, num_results=10, days_back=7)

            if serpapi_result.get("news_results"):
                results["recent_news"].extend([{
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "source": item.get("source"),
                    "date": item.get("date"),
                    "snippet": item.get("snippet")
                } for item in serpapi_result["news_results"]])

        logger.info("Broad market research completed")
        return results

    def research_competitors_general(self, competitors: List[str]) -> Dict:
        """
        Research general news and updates about competitors

        Args:
            competitors: List of competitor names

        Returns:
            Dictionary containing competitor research results
        """
        logger.info(f"Researching competitors: {', '.join(competitors)}")

        results = {}

        for competitor in competitors:
            logger.info(f"Researching {competitor}...")

            competitor_data = {
                "general_news": [],
                "funding_info": [],
                "metrics": [],
                "timestamp": datetime.now().isoformat()
            }

            # General news
            news_query = f"{competitor} digital adoption platform news 2025"
            perplexity_result = self.perplexity.search(news_query, recency_filter="week")

            if perplexity_result.get("choices"):
                content = perplexity_result["choices"][0]["message"]["content"]
                citations = perplexity_result.get("citations", [])
                competitor_data["general_news"].append({
                    "content": content,
                    "citations": citations
                })

            # Funding and metrics
            metrics_queries = [
                f"{competitor} revenue valuation 2025",
                f"{competitor} funding round investment 2025",
                f"{competitor} customer growth metrics"
            ]

            for query in metrics_queries:
                result = self.perplexity.search(query, recency_filter="month")
                if result.get("choices"):
                    competitor_data["metrics"].append({
                        "query": query,
                        "content": result["choices"][0]["message"]["content"],
                        "citations": result.get("citations", [])
                    })

            # SerpAPI news search
            serpapi_news = self.serpapi.search_news(
                f"{competitor} news",
                num_results=5,
                days_back=7
            )

            if serpapi_news.get("news_results"):
                competitor_data["serp_news"] = [{
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "source": item.get("source"),
                    "date": item.get("date"),
                    "snippet": item.get("snippet")
                } for item in serpapi_news["news_results"]]

            results[competitor] = competitor_data

        logger.info("Competitor general research completed")
        return results
