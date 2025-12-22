"""Report generation module using GPT-5"""
import logging
import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
from ..api_clients import OpenAIClient

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates comprehensive reports using GPT-5"""

    def __init__(self, openai_client: OpenAIClient):
        self.openai = openai_client

    def generate_report(
        self,
        research_data: Dict,
        analysis_results: Dict,
        output_dir: str = "./reports"
    ) -> Dict:
        """
        Generate comprehensive markdown report

        Args:
            research_data: Complete research data
            analysis_results: Analysis results from Claude
            output_dir: Directory to save reports

        Returns:
            Dictionary containing report paths and metadata
        """
        logger.info("Starting report generation with GPT-5...")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        date_str = datetime.now().strftime("%B %d, %Y")

        # Get system prompt with all rules and guidelines
        system_prompt = self._get_system_prompt()

        # Get report template
        report_template = self._get_report_template()

        # Generate report using GPT-5
        try:
            report_markdown = self.openai.generate_report(
                research_data=research_data,
                analysis_results=analysis_results,
                report_template=report_template,
                system_prompt=system_prompt
            )

            # Save markdown report
            markdown_path = output_path / f"DAP_Market_Report_{timestamp}.md"
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(report_markdown)

            logger.info(f"Markdown report saved to {markdown_path}")

            # Generate HTML version
            html_content = self._markdown_to_html(report_markdown, date_str)
            html_path = output_path / f"DAP_Market_Report_{timestamp}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"HTML report saved to {html_path}")

            return {
                "success": True,
                "markdown_path": str(markdown_path),
                "html_path": str(html_path),
                "timestamp": timestamp,
                "date": date_str
            }

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_system_prompt(self) -> str:
        """Get comprehensive system prompt with all rules"""
        return """You are a DAP Market Research Agent generating a comprehensive weekly market research report.

# CRITICAL RULES & GUARDRAILS (ABSOLUTE PROHIBITIONS):

1. **NO HALLUCINATION**: Only use data from verified sources within the timeframe
2. **NO HISTORICAL BACKFILLING**: Do NOT use data outside the specified timespan
3. **STRICT PLACEHOLDER RULE**: If no data exists, write ONLY: "*No new updates this week.*"
4. **MANDATORY INLINE CITATIONS**: Every factual claim MUST have an inline bracketed markdown source link
   - Format: "Claim text ([Source Name](https://url.com))."
   - Citations must be INLINE within sentences, not at the end
5. **EXTREME BREVITY**: Keep paragraphs short (2-4 sentences max)
6. **NO FORBIDDEN SUBSECTIONS**: Only use explicitly listed H2/H3/H4 subsections

# TEMPORAL INTELLIGENCE:
- GENERAL NEWS: 7-day window
- PRODUCT UPDATES: 30-day window
- PRESS RELEASES: Current calendar month
- USER REVIEWS: 30-day period

# CITATION FORMAT EXAMPLES:
✓ CORRECT: "Pendo raised $150M in Series C funding ([TechCrunch](https://techcrunch.com/article))."
✗ WRONG: "Pendo raised $150M in Series C funding. Source: TechCrunch"
✗ WRONG: "Pendo raised $150M in Series C funding." (no citation at all)

Generate a professional, data-driven report following the exact structure provided."""

    def _get_report_template(self) -> str:
        """Get report structure template"""
        return """# 🚀 Executive Summary
3-4 strategic insights with business implications (max 300 words). Every claim must have inline citations.

# 📰 Recent Digital Adoption Platform Market News
Only news from THIS WEEK (last 7 days). If no new content: "*No significant Digital Adoption Platform market news this week.*"
Include inline citations for each news item.

# 🎯 Competitors Spotlights

## Pendo
### Strategic Moves
### Product Updates
### Partnerships & Integrations
### Case Studies & Customer Stories
### User Feedback

## WalkMe
### Strategic Moves
### Product Updates
### Partnerships & Integrations
### Case Studies & Customer Stories
### User Feedback

## WhatFix
### Strategic Moves
### Product Updates
### Partnerships & Integrations
### Case Studies & Customer Stories
### User Feedback

## Apty
### Strategic Moves
### Product Updates
### Partnerships & Integrations
### Case Studies & Customer Stories
### User Feedback

## Appcues
### Strategic Moves
### Product Updates
### Partnerships & Integrations
### Case Studies & Customer Stories
### User Feedback

# 📊 Overall Market Data
Market size, growth rates, investment trends, analyst forecasts with inline citations.

## Key Market Trends & Insights

## Strategic Implications

## Market Trajectory Analysis

# 📈 Recent Industry Reports & Analysis
New analyst reports, industry analysis with inline citations.
If no reports: "*No new industry reports available this period.*"

# 💡 Strategic Insights for Product Strategy

## Immediate Opportunities (Next 30-90 days)

## Medium-term Considerations (3-6 months)

## Competitive Threats

## Product Roadmap Implications

# 🌟 Emerging Markets & Niches
New product categories, first-mover advantages with inline citations.
If none detected: "*No new emerging markets identified this week.*"
"""

    def _markdown_to_html(self, markdown_content: str, report_date: str) -> str:
        """Convert markdown report to HTML with styling"""
        # Simple markdown to HTML conversion
        html_content = markdown_content.replace('\n# ', '\n<h1>').replace('</h1>\n', '</h1>\n')
        html_content = html_content.replace('\n## ', '\n<h2>').replace('</h2>\n', '</h2>\n')
        html_content = html_content.replace('\n### ', '\n<h3>').replace('</h3>\n', '</h3>\n')
        html_content = html_content.replace('\n#### ', '\n<h4>').replace('</h4>\n', '</h4>\n')

        # Wrap in HTML template
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DAP Market Research Report - {report_date}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 25px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #546e7a;
            margin-top: 20px;
        }}
        h4 {{
            color: #607d8b;
            margin-top: 15px;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        p {{
            margin: 15px 0;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 8px 0;
        }}
        .date {{
            text-align: right;
            color: #7f8c8d;
            font-style: italic;
            margin-bottom: 30px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .header h1 {{
            border: none;
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Digital Adoption Platform Market Research Report</h1>
            <div class="date">{report_date}</div>
        </div>
        {html_content}
    </div>
</body>
</html>"""
        return html

    def extract_executive_summary(self, report_content: str) -> str:
        """Extract executive summary from report for Slack notification"""
        lines = report_content.split('\n')
        summary_lines = []
        in_summary = False

        for line in lines:
            if '# 🚀 Executive Summary' in line or '# Executive Summary' in line:
                in_summary = True
                continue
            elif in_summary and line.startswith('#'):
                break
            elif in_summary and line.strip():
                summary_lines.append(line.strip())

        summary = ' '.join(summary_lines)[:500]  # First 500 chars
        return summary if summary else "Weekly DAP market research report completed successfully."
