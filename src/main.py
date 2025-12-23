"""Main orchestrator for DAP Market Research Agent"""
import logging
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Import modules
from .api_clients import (
    PerplexityClient,
    SerpAPIClient,
    ClaudeClient,
    OpenAIClient,
    SlackClient
)
from .research_modules import (
    BroadResearchModule,
    CompetitorAnalysisModule,
    FeedbackSearchModule
)
from .analysis import DataAnalyzer
from .report_generation import ReportGenerator
from .scheduler import ResearchScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_research_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class MarketResearchAgent:
    """Main orchestrator for DAP market research"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the Market Research Agent

        Args:
            config_path: Path to configuration file
        """
        logger.info("Initializing Market Research Agent...")

        # Load environment variables
        load_dotenv()

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize API clients
        logger.info("Initializing API clients...")
        self.perplexity = PerplexityClient()
        self.serpapi = SerpAPIClient()
        self.claude = ClaudeClient()
        self.openai = OpenAIClient()
        self.slack = SlackClient()

        # Initialize research modules
        logger.info("Initializing research modules...")
        self.broad_research = BroadResearchModule(self.perplexity, self.serpapi)
        self.competitor_analysis = CompetitorAnalysisModule()
        self.feedback_search = FeedbackSearchModule(self.perplexity, self.serpapi)

        # Initialize analysis and reporting
        self.analyzer = DataAnalyzer(self.claude)
        self.report_generator = ReportGenerator(self.openai)

        logger.info("Market Research Agent initialized successfully")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration: {str(e)}")
            raise

    def run_research(self) -> dict:
        """
        Execute complete research workflow

        Returns:
            Dictionary containing all research results
        """
        logger.info("="*80)
        logger.info("Starting DAP Market Research Workflow")
        logger.info("="*80)

        start_time = datetime.now()
        results = {
            "metadata": {
                "execution_time": start_time.isoformat(),
                "agent_version": "1.0.0"
            }
        }

        try:
            # Step 1: Broad Market Research
            logger.info("\n[1/6] Conducting broad market research...")
            results["broad_research"] = self.broad_research.research_market_trends()

            competitors = [c["name"] for c in self.config["competitors"]]
            competitor_general = self.broad_research.research_competitors_general(competitors)
            results["competitor_general_research"] = competitor_general

            logger.info("✓ Broad market research completed")

            # Step 2: Competitor Analysis
            logger.info("\n[2/6] Analyzing competitor websites...")
            results["competitor_analysis"] = self.competitor_analysis.analyze_all_competitors(
                self.config["competitors"]
            )
            logger.info("✓ Competitor analysis completed")

            # Step 3: User Feedback Search
            logger.info("\n[3/6] Searching user feedback...")
            results["user_feedback"] = self.feedback_search.analyze_all_competitor_feedback(
                self.config["competitors"]
            )
            logger.info("✓ User feedback search completed")

            # Step 4: Data Analysis with Claude
            logger.info("\n[4/6] Analyzing data with Claude Sonnet 4.5...")
            results["analysis"] = self.analyzer.analyze_research_data(results)
            logger.info("✓ Data analysis completed")

            # Step 5: Report Generation with GPT-5
            logger.info("\n[5/6] Generating report with GPT-5...")
            report_result = self.report_generator.generate_report(
                research_data=results,
                analysis_results=results["analysis"],
                output_dir=self.config["output"]["output_directory"]
            )
            results["report"] = report_result
            logger.info("✓ Report generation completed")

            # Step 6: Send Slack Notification
            logger.info("\n[6/6] Sending Slack notification...")
            if report_result["success"]:
                # Read the report to extract summary
                with open(report_result["markdown_path"], 'r') as f:
                    report_content = f.read()

                summary = self.report_generator.extract_executive_summary(report_content)

                # Send notification
                slack_result = self.slack.send_report_notification(
                    report_url=f"file://{os.path.abspath(report_result['html_path'])}",
                    summary=summary,
                    report_date=report_result["date"]
                )

                # Also upload the HTML file
                self.slack.upload_file(
                    file_path=report_result["html_path"],
                    title=f"DAP Market Report - {report_result['date']}",
                    initial_comment="📊 Weekly DAP Market Research Report is ready!"
                )

                logger.info("✓ Slack notification sent")
            else:
                logger.error("Report generation failed, skipping Slack notification")

            # Calculate execution time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            results["metadata"]["duration_seconds"] = duration

            logger.info("="*80)
            logger.info(f"Research workflow completed successfully in {duration:.2f} seconds")
            logger.info("="*80)

            return results

        except Exception as e:
            logger.error(f"Error during research workflow: {str(e)}", exc_info=True)
            results["error"] = str(e)
            return results


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="DAP Market Research Agent")
    parser.add_argument(
        "--mode",
        choices=["once", "schedule", "daily"],
        default="once",
        help="Execution mode: 'once' for immediate execution, 'schedule' for weekly scheduling, 'daily' for daily testing"
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to configuration file"
    )

    args = parser.parse_args()

    # Initialize agent
    agent = MarketResearchAgent(config_path=args.config)

    if args.mode == "once":
        # Run once immediately
        logger.info("Running research once...")
        agent.run_research()

    elif args.mode == "schedule":
        # Schedule for weekly execution
        logger.info("Setting up weekly schedule...")
        scheduler = ResearchScheduler(
            research_task=agent.run_research,
            timezone="CET"
        )
        scheduler.schedule_weekly(
            day=agent.config["schedule"]["day_of_week"],
            time_str=agent.config["schedule"]["time"]
        )
        logger.info(f"Next run: {scheduler.get_next_run()}")
        scheduler.start(blocking=True)

    elif args.mode == "daily":
        # Schedule for daily execution (testing)
        logger.info("Setting up daily schedule for testing...")
        scheduler = ResearchScheduler(
            research_task=agent.run_research,
            timezone="CET"
        )
        scheduler.schedule_daily(time_str=agent.config["schedule"]["time"])
        logger.info(f"Next run: {scheduler.get_next_run()}")
        scheduler.start(blocking=True)


if __name__ == "__main__":
    main()
