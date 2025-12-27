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
        # Use GPT-4 Turbo with 128k context window
        self.model = "gpt-4-turbo"  # Supports up to 128k context, using 16k for completions

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

            # Format research data in a structured way
            import json
            formatted_data = json.dumps(research_data, indent=2, default=str)

            user_message = f"""Generate a comprehensive DAP market research report based on the following:

=== RESEARCH DATA ===
{formatted_data}

=== ANALYSIS RESULTS ===
{analysis_results}

=== REPORT STRUCTURE ===
{report_template}

CRITICAL INSTRUCTIONS:
1. Fill EVERY section with available data - don't leave sections empty unless NO data exists
2. Use data from "broad_research", "competitor_analysis", and "user_feedback" to populate competitor sections
3. Extract Strategic Moves, Product Updates, Partnerships from the research data even if not explicitly labeled
4. Use Claude's analysis results to fill Strategic Insights sections
5. If specific data isn't categorized perfectly, intelligently map it to the appropriate section
6. Only use "*No new updates this week.*" if genuinely no relevant data exists for that section
7. Prioritize USING available data over leaving sections empty

Follow the structure exactly and adhere to all rules and guidelines provided."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.4,
                max_tokens=16000  # Increase to allow full report generation
            )

            report = response.choices[0].message.content
            logger.info("GPT-4 Turbo report generation completed")
            return report

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"Error generating report: {str(e)}"
