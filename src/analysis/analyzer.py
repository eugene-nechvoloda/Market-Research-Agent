"""Data analysis module using Claude Sonnet 4.5"""
import logging
import json
from typing import Dict
from ..api_clients import ClaudeClient

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """Analyzes research data using Claude Sonnet 4.5"""

    def __init__(self, claude_client: ClaudeClient):
        self.claude = claude_client

    def analyze_research_data(self, research_data: Dict) -> Dict:
        """
        Perform comprehensive analysis of research data

        Args:
            research_data: Complete research data dictionary

        Returns:
            Analysis results dictionary
        """
        logger.info("Starting comprehensive data analysis with Claude...")

        # Prepare structured data for analysis
        data_summary = self._prepare_data_summary(research_data)

        # Analysis prompt
        analysis_prompt = """You are analyzing comprehensive DAP (Digital Adoption Platform) market research data.

Your task is to perform deep analysis and extract strategic insights. Focus on:

1. **Executive Insights**: Identify 3-4 most critical strategic insights with business implications
2. **Competitive Intelligence**: Analyze competitor positioning, strengths, weaknesses, and recent moves
3. **Market Dynamics**: Identify trends, trajectory changes, and emerging patterns
4. **Strategic Opportunities**: Highlight immediate opportunities and competitive threats
5. **Product Implications**: Suggest what this means for product strategy and roadmap

CRITICAL RULES:
- Only use data provided - NO fabrication or speculation
- Be concise and data-driven
- Include specific examples and data points
- Identify gaps where data is missing
- Highlight time-sensitive insights

Provide analysis in structured JSON format with these keys:
- executive_summary: List of 3-4 key insights with business impact
- competitor_insights: Dict of insights per competitor
- market_trends: List of identified trends with supporting data
- emerging_opportunities: List of opportunities
- competitive_threats: List of threats
- strategic_recommendations: List of actionable recommendations
- data_gaps: Areas where more data is needed"""

        try:
            # Get analysis from Claude
            analysis_text = self.claude.analyze_data(
                data=json.dumps(data_summary, indent=2),
                analysis_prompt=analysis_prompt
            )

            # Try to parse as JSON, fallback to text
            try:
                analysis_results = json.loads(analysis_text)
            except json.JSONDecodeError:
                logger.warning("Could not parse analysis as JSON, returning as text")
                analysis_results = {
                    "raw_analysis": analysis_text,
                    "executive_summary": self._extract_section(analysis_text, "executive"),
                    "competitor_insights": {},
                    "market_trends": self._extract_section(analysis_text, "trend"),
                    "strategic_recommendations": self._extract_section(analysis_text, "recommend")
                }

            logger.info("Data analysis completed successfully")
            return analysis_results

        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            return {
                "error": str(e),
                "executive_summary": [],
                "competitor_insights": {},
                "market_trends": []
            }

    def _prepare_data_summary(self, research_data: Dict) -> Dict:
        """Prepare concise data summary for analysis"""
        summary = {
            "market_research": {},
            "competitor_data": {},
            "user_feedback": {},
            "metadata": research_data.get("metadata", {})
        }

        # Summarize market research
        if "broad_research" in research_data:
            broad = research_data["broad_research"]
            summary["market_research"] = {
                "market_trends_count": len(broad.get("market_trends", [])),
                "market_size_data_count": len(broad.get("market_size_data", [])),
                "industry_reports_count": len(broad.get("industry_reports", [])),
                "recent_news_count": len(broad.get("recent_news", [])),
                "sample_trends": broad.get("market_trends", [])[:2],
                "sample_news": broad.get("recent_news", [])[:5]
            }

        # Summarize competitor data
        if "competitor_analysis" in research_data:
            comp_analysis = research_data["competitor_analysis"]
            summary["competitor_data"] = {}

            for competitor, data in comp_analysis.items():
                summary["competitor_data"][competitor] = {
                    "blog_posts_count": len(data.get("blog_posts", [])),
                    "press_releases_count": len(data.get("press_releases", [])),
                    "product_updates_count": len(data.get("product_updates", [])),
                    "recent_posts": data.get("blog_posts", [])[:3],
                    "recent_updates": data.get("product_updates", [])[:3]
                }

        # Summarize user feedback
        if "user_feedback" in research_data:
            feedback = research_data["user_feedback"]
            summary["user_feedback"] = {}

            for competitor, data in feedback.items():
                platforms = data.get("review_platforms", {})
                social = data.get("social_media", {})

                summary["user_feedback"][competitor] = {
                    "g2_reviews_count": len(platforms.get("g2", {}).get("reviews", [])),
                    "social_mentions": {
                        "reddit": len(social.get("reddit", [])),
                        "linkedin": len(social.get("linkedin", []))
                    },
                    "sample_reviews": platforms.get("g2", {}).get("reviews", [])[:5]
                }

        return summary

    def _extract_section(self, text: str, keyword: str) -> list:
        """Extract section from text based on keyword"""
        lines = text.split('\n')
        section_lines = []
        in_section = False

        for line in lines:
            if keyword.lower() in line.lower():
                in_section = True
            elif in_section and line.strip().startswith(('#', '-', '*', '1', '2', '3')):
                section_lines.append(line.strip())
            elif in_section and not line.strip():
                break

        return section_lines[:5]  # Return top 5 items
