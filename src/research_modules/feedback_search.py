"""User feedback search module for review platforms and social media"""
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
from ..api_clients import PerplexityClient, SerpAPIClient

logger = logging.getLogger(__name__)


class FeedbackSearchModule:
    """Module for searching and analyzing user feedback"""

    def __init__(self, perplexity_client: PerplexityClient, serpapi_client: SerpAPIClient):
        self.perplexity = perplexity_client
        self.serpapi = serpapi_client
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_url_content(self, url: str, timeout: int = 30) -> Optional[str]:
        """Fetch content from URL"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def extract_g2_reviews(self, html: str) -> List[Dict]:
        """
        Extract reviews from G2 page HTML

        Args:
            html: HTML content from G2 page

        Returns:
            List of review dictionaries
        """
        soup = BeautifulSoup(html, 'html.parser')
        reviews = []

        # G2 review patterns (may need adjustment based on actual HTML structure)
        review_divs = soup.find_all('div', class_=re.compile(r'review|paper', re.I))

        for review_div in review_divs[:20]:
            review = {}

            # Extract rating
            rating_tag = review_div.find('div', class_=re.compile(r'rating|stars', re.I))
            if rating_tag:
                review['rating'] = rating_tag.get_text(strip=True)

            # Extract review title
            title_tag = review_div.find(['h3', 'h4'], class_=re.compile(r'title|headline', re.I))
            if title_tag:
                review['title'] = title_tag.get_text(strip=True)

            # Extract review text
            text_tag = review_div.find('div', class_=re.compile(r'text|content|body', re.I))
            if text_tag:
                review['text'] = text_tag.get_text(strip=True)[:500]

            # Extract pros/cons
            pros_tag = review_div.find('div', class_=re.compile(r'pros?', re.I))
            if pros_tag:
                review['pros'] = pros_tag.get_text(strip=True)

            cons_tag = review_div.find('div', class_=re.compile(r'cons?', re.I))
            if cons_tag:
                review['cons'] = cons_tag.get_text(strip=True)

            # Extract date
            date_tag = review_div.find('time')
            if date_tag:
                review['date'] = date_tag.get('datetime') or date_tag.get_text(strip=True)

            if review.get('title') or review.get('text'):
                reviews.append(review)

        return reviews

    def search_social_media_feedback(self, competitor: str) -> Dict:
        """
        Search for competitor feedback on social media

        Args:
            competitor: Competitor name

        Returns:
            Dictionary containing social media feedback
        """
        logger.info(f"Searching social media feedback for {competitor}")

        results = {
            "reddit": [],
            "linkedin": [],
            "twitter": [],
            "general": []
        }

        # Search Reddit mentions
        reddit_query = f"{competitor} DAP digital adoption platform site:reddit.com"
        reddit_results = self.serpapi.search(reddit_query, num_results=10, time_filter="qdr:m")

        if reddit_results.get("organic_results"):
            results["reddit"] = [{
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            } for item in reddit_results["organic_results"]]

        # Search LinkedIn mentions
        linkedin_query = f"{competitor} digital adoption platform site:linkedin.com"
        linkedin_results = self.serpapi.search(linkedin_query, num_results=10, time_filter="qdr:m")

        if linkedin_results.get("organic_results"):
            results["linkedin"] = [{
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            } for item in linkedin_results["organic_results"]]

        # Use Perplexity for comprehensive feedback search
        feedback_query = f"Recent user feedback and reviews about {competitor} digital adoption platform from Reddit, LinkedIn, and review sites"
        perplexity_result = self.perplexity.search(feedback_query, recency_filter="month")

        if perplexity_result.get("choices"):
            results["general"] = {
                "content": perplexity_result["choices"][0]["message"]["content"],
                "citations": perplexity_result.get("citations", [])
            }

        return results

    def analyze_review_platform(self, competitor: str, platform_url: str, platform_name: str) -> Dict:
        """
        Analyze feedback from a review platform

        Args:
            competitor: Competitor name
            platform_url: URL of the review platform page
            platform_name: Name of platform (G2, Gartner, etc.)

        Returns:
            Dictionary containing review analysis
        """
        logger.info(f"Analyzing {platform_name} reviews for {competitor}")

        results = {
            "platform": platform_name,
            "competitor": competitor,
            "url": platform_url,
            "reviews": [],
            "summary": {}
        }

        # Fetch page content
        html = self.fetch_url_content(platform_url)

        if html:
            if "g2.com" in platform_url.lower():
                results["reviews"] = self.extract_g2_reviews(html)
            else:
                # Generic review extraction
                soup = BeautifulSoup(html, 'html.parser')
                review_sections = soup.find_all(['div', 'article'], class_=re.compile(r'review', re.I))

                for section in review_sections[:15]:
                    review = {
                        "text": section.get_text(strip=True)[:500]
                    }
                    results["reviews"].append(review)

        # Use Perplexity to get summarized feedback
        feedback_query = f"Latest user reviews and feedback about {competitor} on {platform_name} in the past 30 days"
        perplexity_result = self.perplexity.search(feedback_query, recency_filter="month")

        if perplexity_result.get("choices"):
            results["summary"] = {
                "content": perplexity_result["choices"][0]["message"]["content"],
                "citations": perplexity_result.get("citations", [])
            }

        return results

    def search_competitor_feedback(self, competitor: str, review_urls: Dict[str, str]) -> Dict:
        """
        Search all feedback sources for a competitor

        Args:
            competitor: Competitor name
            review_urls: Dictionary of review platform URLs

        Returns:
            Comprehensive feedback analysis
        """
        logger.info(f"Searching all feedback for {competitor}")

        results = {
            "competitor": competitor,
            "review_platforms": {},
            "social_media": {},
            "web_mentions": []
        }

        # Analyze G2 reviews
        if review_urls.get("g2"):
            results["review_platforms"]["g2"] = self.analyze_review_platform(
                competitor, review_urls["g2"], "G2"
            )

        # Analyze Gartner reviews
        if review_urls.get("gartner"):
            results["review_platforms"]["gartner"] = self.analyze_review_platform(
                competitor, review_urls["gartner"], "Gartner"
            )

        # Search social media
        results["social_media"] = self.search_social_media_feedback(competitor)

        # General web search for reviews
        web_query = f"{competitor} user reviews feedback complaints 2025"
        web_results = self.serpapi.search(web_query, num_results=10, time_filter="qdr:m")

        if web_results.get("organic_results"):
            results["web_mentions"] = [{
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            } for item in web_results["organic_results"]]

        return results

    def analyze_all_competitor_feedback(self, competitors_config: List[Dict]) -> Dict:
        """
        Analyze feedback for all competitors

        Args:
            competitors_config: List of competitor configurations

        Returns:
            Dictionary containing all feedback analyses
        """
        results = {}

        for competitor in competitors_config:
            name = competitor.get("name")
            urls = competitor.get("urls", {})

            if name:
                results[name] = self.search_competitor_feedback(name, urls)

        return results
