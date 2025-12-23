"""Slack App - Interactive UI client for DAP Market Research Agent"""
import os
import logging
import threading
from datetime import datetime
from pathlib import Path
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from dotenv import load_dotenv

# Import agent components
from .main import MarketResearchAgent
from .scheduler import ResearchScheduler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Initialize Flask app for Railway
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

# Global agent instance
agent = None
scheduler = None
research_status = {
    "running": False,
    "last_run": None,
    "next_scheduled": None,
    "last_report": None
}


def initialize_agent():
    """Initialize the Market Research Agent"""
    global agent, scheduler
    try:
        agent = MarketResearchAgent(config_path="config/config.yaml")
        logger.info("Market Research Agent initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}")
        return False


# Slash command: /research
@app.command("/research")
def handle_research_command(ack, command, respond):
    """Handle /research slash command"""
    ack()

    user_id = command["user_id"]
    text = command.get("text", "").strip()

    if not text or text == "help":
        respond(get_help_message())
    elif text == "run":
        handle_run_research(respond, user_id)
    elif text == "status":
        handle_status(respond)
    elif text == "schedule":
        handle_schedule_info(respond)
    elif text.startswith("schedule "):
        # Extract schedule parameters
        params = text.replace("schedule ", "").strip()
        handle_set_schedule(respond, params)
    elif text == "latest":
        handle_latest_report(respond)
    else:
        respond(f"Unknown command: `{text}`. Type `/research help` for available commands.")


def get_help_message():
    """Get help message with available commands"""
    return {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 DAP Market Research Agent - Commands"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Available Commands:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "`/research run` - Run research immediately\n"
                           "`/research status` - Check current status\n"
                           "`/research schedule` - View schedule information\n"
                           "`/research latest` - Get the latest report\n"
                           "`/research help` - Show this help message"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💡 *Tip:* Reports are automatically generated every Monday at 8:00 AM CET"
                    }
                ]
            }
        ]
    }


def handle_run_research(respond, user_id):
    """Handle immediate research execution"""
    global research_status, agent

    if research_status["running"]:
        respond({
            "text": "❌ Research is already running. Please wait for it to complete.",
            "response_type": "ephemeral"
        })
        return

    # Send initial response
    respond({
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🚀 *Starting Market Research*\n\nInitiating comprehensive DAP market research...\nThis may take 5-15 minutes."
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Requested by <@{user_id}> at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
    })

    # Run research in background thread
    def run_research_task():
        global research_status
        try:
            research_status["running"] = True
            research_status["last_run"] = datetime.now().isoformat()

            if agent is None:
                initialize_agent()

            # Execute research
            result = agent.run_research()

            research_status["running"] = False

            if result.get("report", {}).get("success"):
                research_status["last_report"] = result["report"]["markdown_path"]

                # Send success notification
                app.client.chat_postMessage(
                    channel=os.environ.get("SLACK_CHANNEL_ID"),
                    text="✅ Research completed successfully!",
                    blocks=[
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Market Research Completed"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Duration:* {result['metadata'].get('duration_seconds', 0):.1f} seconds\n"
                                       f"*Report Date:* {result['report']['date']}"
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "📄 View Report"
                                    },
                                    "action_id": "view_report",
                                    "value": result["report"]["markdown_path"]
                                }
                            ]
                        }
                    ]
                )
            else:
                # Send error notification
                app.client.chat_postMessage(
                    channel=os.environ.get("SLACK_CHANNEL_ID"),
                    text="❌ Research failed. Check logs for details."
                )

        except Exception as e:
            logger.error(f"Research execution failed: {str(e)}", exc_info=True)
            research_status["running"] = False

            app.client.chat_postMessage(
                channel=os.environ.get("SLACK_CHANNEL_ID"),
                text=f"❌ Research failed with error: {str(e)}"
            )

    # Start background thread
    thread = threading.Thread(target=run_research_task)
    thread.daemon = True
    thread.start()


def handle_status(respond):
    """Handle status check"""
    global research_status

    status_emoji = "🔄" if research_status["running"] else "✅"
    status_text = "Running" if research_status["running"] else "Idle"

    last_run_text = research_status["last_run"] or "Never"
    if research_status["last_run"]:
        last_run_text = datetime.fromisoformat(research_status["last_run"]).strftime("%Y-%m-%d %H:%M:%S")

    respond({
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Agent Status"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{status_emoji} {status_text}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Last Run:*\n{last_run_text}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Next Scheduled:*\nEvery Monday 8:00 AM CET"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Reports Generated:*\n{len(list(Path('reports').glob('*.md'))) if Path('reports').exists() else 0}"
                    }
                ]
            }
        ]
    })


def handle_schedule_info(respond):
    """Handle schedule information request"""
    respond({
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📅 Research Schedule"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Current Schedule:*\n• Every Monday at 8:00 AM CET\n\n"
                           "*What happens during scheduled research:*\n"
                           "1. Broad market research (Perplexity + SerpAPI)\n"
                           "2. Competitor analysis (5 competitors)\n"
                           "3. User feedback search (reviews + social media)\n"
                           "4. Data analysis (Claude Sonnet 4.5)\n"
                           "5. Report generation (GPT-5)\n"
                           "6. Slack notification with report"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💡 Use `/research run` to execute research immediately"
                    }
                ]
            }
        ]
    })


def handle_latest_report(respond):
    """Handle latest report request"""
    reports_dir = Path("reports")

    if not reports_dir.exists():
        respond("No reports available yet. Run `/research run` to generate one.")
        return

    # Find latest markdown report
    reports = sorted(reports_dir.glob("DAP_Market_Report_*.md"), key=os.path.getmtime, reverse=True)

    if not reports:
        respond("No reports available yet. Run `/research run` to generate one.")
        return

    latest_report = reports[0]
    report_date = latest_report.stem.replace("DAP_Market_Report_", "")

    # Read first 1000 chars of report for preview
    with open(latest_report, 'r') as f:
        content = f.read(1000)

    respond({
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📄 Latest Market Research Report"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Report Date:* {report_date}\n*File:* `{latest_report.name}`"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Preview:*\n```{content}```\n..."
                }
            }
        ]
    })

    # Upload the full HTML report
    html_report = latest_report.parent / latest_report.name.replace('.md', '.html')
    if html_report.exists():
        try:
            app.client.files_upload_v2(
                channel=os.environ.get("SLACK_CHANNEL_ID"),
                file=str(html_report),
                title=f"DAP Market Report - {report_date}",
                initial_comment="📊 Full HTML report attached"
            )
        except Exception as e:
            logger.error(f"Failed to upload report: {str(e)}")


# Action handler for view report button
@app.action("view_report")
def handle_view_report(ack, action, respond):
    """Handle view report button click"""
    ack()

    report_path = action["value"]

    if Path(report_path).exists():
        with open(report_path, 'r') as f:
            content = f.read(2000)

        respond({
            "text": f"Report Preview:\n```{content}```\n...",
            "response_type": "ephemeral"
        })


# Home tab
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    """Update the app home tab"""
    try:
        # Get latest report info
        reports_dir = Path("reports")
        report_count = len(list(reports_dir.glob("*.md"))) if reports_dir.exists() else 0

        last_run = research_status.get("last_run", "Never")
        if last_run != "Never":
            last_run = datetime.fromisoformat(last_run).strftime("%Y-%m-%d %H:%M:%S")

        client.views_publish(
            user_id=event["user"],
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📊 DAP Market Research Agent"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Welcome to the DAP Market Research Agent! This bot automatically conducts comprehensive weekly market research on the Digital Adoption Platform landscape."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*📈 Quick Stats*"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Reports Generated:*\n{report_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Last Run:*\n{last_run}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Schedule:*\nMonday 8:00 AM CET"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Status:*\n{'🔄 Running' if research_status['running'] else '✅ Idle'}"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*🚀 Quick Actions*\n\nUse these commands to interact with the agent:"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "`/research run` - Run research now\n"
                                   "`/research status` - Check status\n"
                                   "`/research latest` - Get latest report\n"
                                   "`/research help` - Show all commands"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "💡 The agent monitors 5 competitors: Pendo, WalkMe, WhatFix, Apty, Appcues"
                            }
                        ]
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


# Flask routes for Railway
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """Handle Slack events"""
    return handler.handle(request)


@flask_app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@flask_app.route("/", methods=["GET"])
def home():
    """Home endpoint"""
    return {
        "name": "DAP Market Research Agent",
        "status": "running",
        "version": "1.0.0"
    }


def main():
    """Main entry point for Slack app"""
    logger.info("Starting DAP Market Research Agent Slack App...")

    # Initialize agent
    if not initialize_agent():
        logger.error("Failed to initialize agent. Exiting.")
        return

    # Get port from environment (Railway sets this)
    port = int(os.environ.get("PORT", 3000))

    logger.info(f"Slack app starting on port {port}")

    # Run Flask app
    flask_app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
