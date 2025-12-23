"""Anthropic Claude API client for data analysis"""
import os
from typing import Optional
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client for interacting with Anthropic Claude API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("Anthropic API key not provided")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"  # Claude Sonnet 4.5

    def analyze_data(self, data: str, analysis_prompt: str) -> str:
        """
        Analyze research data using Claude

        Args:
            data: Raw research data to analyze
            analysis_prompt: Instructions for analysis

        Returns:
            Analysis results as string
        """
        try:
            logger.info("Starting Claude analysis...")

            message = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": f"{analysis_prompt}\n\n=== DATA TO ANALYZE ===\n{data}"
                    }
                ]
            )

            analysis = message.content[0].text
            logger.info("Claude analysis completed")
            return analysis

        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            return f"Error during analysis: {str(e)}"

    def synthesize_insights(self, research_data: dict) -> str:
        """
        Synthesize insights from collected research data

        Args:
            research_data: Dictionary containing all research results

        Returns:
            Synthesized insights
        """
        analysis_prompt = """You are analyzing DAP (Digital Adoption Platform) market research data.

Your task is to:
1. Identify key strategic insights and trends
2. Extract actionable intelligence for product strategy
3. Highlight competitive threats and opportunities
4. Note emerging market patterns

Provide a structured analysis with:
- Executive summary (3-4 key insights)
- Competitor positioning
- Market trends
- Strategic recommendations

Be concise and data-driven. Only use information provided in the data."""

        data_str = str(research_data)
        return self.analyze_data(data_str, analysis_prompt)
