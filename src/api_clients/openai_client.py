"""OpenAI API client for report generation using GPT-5"""
import os
from typing import Optional
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.client = OpenAI(api_key=self.api_key)
        # Use GPT-4 Turbo: 128k input context, 4096 max output tokens
        self.model = "gpt-4-turbo"

    def generate_report(
        self,
        research_data: dict,
        analysis_results: str,
        report_template: str,
        system_prompt: str
    ) -> str:
        """
        Generate comprehensive report using GPT-4 Turbo

        Args:
            research_data: Raw research data
            analysis_results: Analysis from Claude
            report_template: Report structure template
            system_prompt: System instructions for report generation

        Returns:
            Generated report as markdown string
        """
        try:
            logger.info("Starting GPT-4 Turbo report generation...")

            # Format research data efficiently with JSON
            import json
            formatted_data = json.dumps(research_data, indent=2, default=str)

            user_message = f"""Generate a comprehensive DAP market research report.

=== RESEARCH DATA ===
{formatted_data}

=== ANALYSIS RESULTS ===
{analysis_results}

=== REPORT STRUCTURE ===
{report_template}

CRITICAL INSTRUCTIONS (Priority: Fill sections efficiently within token limit):
1. Fill ALL sections with available data - extract info from broad_research, competitor_analysis, user_feedback
2. Map data intelligently even if not perfectly categorized (e.g., blog posts → Product Updates, news → Strategic Moves)
3. Use Claude's analysis for Strategic Insights (30/60/90 day recommendations)
4. Be concise but comprehensive - prioritize substance over length
5. Only write "*No new updates this week.*" when genuinely no data exists
6. Focus on completing ALL sections rather than making some sections extremely long

Structure: Follow template exactly. Quality over quantity in each section."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.4,
                max_tokens=4096  # GPT-4 Turbo maximum for completions
            )

            report = response.choices[0].message.content
            logger.info("GPT-4 Turbo report generation completed")
            return report

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"Error generating report: {str(e)}"
