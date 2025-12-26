"""OpenAI API client for report generation using GPT-5"""
import os
from typing import Optional
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI API"""

    def __init__(self, api_key: Optional[str] = None):
        # Support both naming conventions: OPENAI_API_KEY and AI_INTEGRATIONS_OPENAI_API_KEY
        self.api_key = (
            api_key or
            os.getenv("OPENAI_API_KEY") or
            os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY")
        )

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.client = OpenAI(api_key=self.api_key)
        # Note: GPT-5 model name - update when available
        # For now using latest available model
        self.model = "gpt-4-turbo-preview"  # Update to "gpt-5" when available

    def generate_report(
        self,
        research_data: dict,
        analysis_results: str,
        report_template: str,
        system_prompt: str
    ) -> str:
        """
        Generate comprehensive report using GPT-5

        Args:
            research_data: Raw research data
            analysis_results: Analysis from Claude
            report_template: Report structure template
            system_prompt: System instructions for report generation

        Returns:
            Generated report as markdown string
        """
        try:
            logger.info("Starting GPT-5 report generation...")

            user_message = f"""Generate a comprehensive DAP market research report based on the following:

=== RESEARCH DATA ===
{str(research_data)}

=== ANALYSIS RESULTS ===
{analysis_results}

=== REPORT STRUCTURE ===
{report_template}

Follow the structure exactly and adhere to all rules and guidelines provided."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.4,
                max_tokens=16000
            )

            report = response.choices[0].message.content
            logger.info("GPT-5 report generation completed")
            return report

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"Error generating report: {str(e)}"
