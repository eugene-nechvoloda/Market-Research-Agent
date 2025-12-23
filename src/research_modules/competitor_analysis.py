"""Competitor analysis module for direct URL monitoring"""
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class CompetitorAnalysisModule:
    """Module for analyzing competitor websites and announcements"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_url_content(self, url: str, timeout: int = 30) -> Optional[str]:
        """
        Fetch content from a URL

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            HTML content or None if error
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def extract_blog_posts(self, html: str, days_back: int = 30) -> List[Dict]:
        """
        Extract recent blog posts from HTML

        Args:
            html: HTML content
            days_back: How many days back to consider recent

        Returns:
            List of blog post dictionaries
        """
        soup = BeautifulSoup(html, 'html.parser')
        posts = []

        # Common blog post patterns
        article_tags = soup.find_all(['article', 'div'], class_=re.compile(r'post|article|blog-item', re.I))

        for article in article_tags[:20]:  # Limit to recent posts
            post = {}

            # Extract title
            title_tag = article.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|heading', re.I))
            if title_tag:
                post['title'] = title_tag.get_text(strip=True)

            # Extract link
            link_tag = article.find('a', href=True)
            if link_tag:
                post['link'] = link_tag['href']

            # Extract date
            date_tag = article.find(['time', 'span'], class_=re.compile(r'date|time|published', re.I))
            if date_tag:
                post['date'] = date_tag.get_text(strip=True)

            # Extract excerpt
            excerpt_tag = article.find(['p', 'div'], class_=re.compile(r'excerpt|summary|description', re.I))
            if excerpt_tag:
                post['excerpt'] = excerpt_tag.get_text(strip=True)[:300]

            if post.get('title'):
                posts.append(post)

        return posts

    def extract_press_releases(self, html: str) -> List[Dict]:
        """
        Extract press releases from HTML

        Args:
            html: HTML content

        Returns:
            List of press release dictionaries
        """
        soup = BeautifulSoup(html, 'html.parser')
        releases = []

        # Look for press release patterns
        release_tags = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'press|release|news-item', re.I))

        for release in release_tags[:15]:
            item = {}

            # Extract title
            title_tag = release.find(['h1', 'h2', 'h3', 'h4', 'a'])
            if title_tag:
                item['title'] = title_tag.get_text(strip=True)

            # Extract link
            link_tag = release.find('a', href=True)
            if link_tag:
                item['link'] = link_tag['href']

            # Extract date
            date_tag = release.find(['time', 'span'], class_=re.compile(r'date|time', re.I))
            if date_tag:
                item['date'] = date_tag.get_text(strip=True)

            if item.get('title'):
                releases.append(item)

        return releases

    def extract_product_updates(self, html: str) -> List[Dict]:
        """
        Extract product updates/release notes from HTML

        Args:
            html: HTML content

        Returns:
            List of product update dictionaries
        """
        soup = BeautifulSoup(html, 'html.parser')
        updates = []

        # Look for update/release note patterns
        update_tags = soup.find_all(['article', 'div', 'section'],
                                     class_=re.compile(r'update|release|changelog|feature', re.I))

        for update in update_tags[:15]:
            item = {}

            # Extract title/version
            title_tag = update.find(['h1', 'h2', 'h3', 'h4'])
            if title_tag:
                item['title'] = title_tag.get_text(strip=True)

            # Extract date
            date_tag = update.find(['time', 'span'], class_=re.compile(r'date|time|version', re.I))
            if date_tag:
                item['date'] = date_tag.get_text(strip=True)

            # Extract description
            desc_tag = update.find(['p', 'div'], class_=re.compile(r'description|content|summary', re.I))
            if desc_tag:
                item['description'] = desc_tag.get_text(strip=True)[:400]

            # Extract features list
            features_list = update.find(['ul', 'ol'])
            if features_list:
                features = [li.get_text(strip=True) for li in features_list.find_all('li')[:10]]
                item['features'] = features

            if item.get('title'):
                updates.append(item)

        return updates

    def analyze_competitor(self, competitor_name: str, urls: Dict[str, str]) -> Dict:
        """
        Analyze a competitor's online presence

        Args:
            competitor_name: Name of the competitor
            urls: Dictionary of URLs to analyze (blog, newsroom, releases, etc.)

        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Analyzing competitor: {competitor_name}")

        results = {
            "competitor": competitor_name,
            "timestamp": datetime.now().isoformat(),
            "blog_posts": [],
            "press_releases": [],
            "product_updates": [],
            "case_studies": []
        }

        # Fetch and analyze blog
        if urls.get("blog"):
            logger.info(f"Fetching blog: {urls['blog']}")
            html = self.fetch_url_content(urls["blog"])
            if html:
                results["blog_posts"] = self.extract_blog_posts(html)

        # Fetch and analyze newsroom/press releases
        if urls.get("newsroom"):
            logger.info(f"Fetching newsroom: {urls['newsroom']}")
            html = self.fetch_url_content(urls["newsroom"])
            if html:
                results["press_releases"] = self.extract_press_releases(html)

        # Fetch and analyze product updates
        if urls.get("releases"):
            logger.info(f"Fetching releases: {urls['releases']}")
            html = self.fetch_url_content(urls["releases"])
            if html:
                results["product_updates"] = self.extract_product_updates(html)

        # Fetch case studies
        if urls.get("case_studies"):
            logger.info(f"Fetching case studies: {urls['case_studies']}")
            html = self.fetch_url_content(urls["case_studies"])
            if html:
                results["case_studies"] = self.extract_blog_posts(html)  # Similar structure

        logger.info(f"Completed analysis for {competitor_name}")
        return results

    def analyze_all_competitors(self, competitors_config: List[Dict]) -> Dict:
        """
        Analyze all competitors

        Args:
            competitors_config: List of competitor configurations with URLs

        Returns:
            Dictionary containing all competitor analyses
        """
        results = {}

        for competitor in competitors_config:
            name = competitor.get("name")
            urls = competitor.get("urls", {})

            if name and urls:
                results[name] = self.analyze_competitor(name, urls)

        return results
