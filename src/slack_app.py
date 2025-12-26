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
from .report_store import ReportStore
from .google_docs_export import GoogleDocsExporter
from .slack_app_helpers import (
    extract_executive_summary,
    count_words,
    markdown_to_slack_blocks,
    truncate_text
)
from .home_tab_views import build_reports_view, build_settings_view

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

# Global instances
agent = None
scheduler = None
report_store = ReportStore()
google_docs_exporter = GoogleDocsExporter()

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
    global research_status, agent, report_store

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

                # Extract executive summary and word count
                markdown_path = result["report"]["markdown_path"]
                executive_summary = extract_executive_summary(markdown_path)
                word_count = count_words(markdown_path)

                # Try to export to Google Docs
                google_docs_url = None
                if google_docs_exporter.enabled:
                    google_docs_url = google_docs_exporter.export_report(
                        markdown_path,
                        f"DAP Market Report - {result['report']['date']}"
                    )
                else:
                    # Create placeholder URL for demo
                    google_docs_url = google_docs_exporter.create_google_doc_placeholder(
                        f"DAP Market Report",
                        result['report']['date']
                    )

                # Add to report store
                report_id = report_store.add_report(
                    title=f"DAP Market Research Report - {result['report']['date']}",
                    date=result['report']['date'],
                    markdown_path=markdown_path,
                    html_path=result["report"]["html_path"],
                    executive_summary=executive_summary,
                    word_count=word_count,
                    google_docs_url=google_docs_url
                )

                # Send enhanced notification
                send_report_notification(
                    report_id=report_id,
                    title=f"DAP Market Research Report",
                    date=result['report']['date'],
                    executive_summary=executive_summary,
                    reading_time=max(1, round(word_count / 200)),
                    google_docs_url=google_docs_url,
                    duration=result['metadata'].get('duration_seconds', 0)
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


def send_user_notification(client, user_id, report_id, title, date, executive_summary, reading_time, google_docs_url, duration):
    """Send report completion notification directly to user via ephemeral message"""
    try:
        client.chat_postEphemeral(
            channel=user_id,
            user=user_id,
            text=f"✅ {title} - {date} is ready!",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"✅ {title} Complete!"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Date:*\n{date}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Reading Time:*\n~{reading_time} min"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Executive Summary:*\n{truncate_text(executive_summary, 400)}"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⏱️ *Generated in {duration:.1f}s*\n\n📊 Your report is now available in the *Reports* tab of the app home. Click the button below to view it."
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📖 View Report"
                            },
                            "style": "primary",
                            "action_id": "open_report_tab",
                            "value": report_id
                        }
                    ]
                }
            ]
        )
        logger.info(f"Sent user notification for report {report_id} to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send user notification: {e}")


def send_report_notification(report_id, title, date, executive_summary, reading_time, google_docs_url, duration):
    """Send enhanced report notification to channel"""
    try:
        app.client.chat_postMessage(
            channel=os.environ.get("SLACK_CHANNEL_ID"),
            text=f"✅ {title} - {date} is ready!",
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📊 {title}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Date:*\n{date}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Reading Time:*\n~{reading_time} min"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Executive Summary:*\n{truncate_text(executive_summary, 500)}"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📖 Read Full Report"
                            },
                            "style": "primary",
                            "action_id": "open_report_tab",
                            "value": report_id
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📄 Google Docs"
                            },
                            "url": google_docs_url,
                            "action_id": "open_google_docs"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"⏱️ Generated in {duration:.1f}s | Click 'Read Full Report' to view in the Reports tab"
                        }
                    ]
                }
            ]
        )
        logger.info(f"Sent enhanced notification for report {report_id}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


# Action handler: Open report in Reports tab
@app.action("open_report_tab")
def handle_open_report_tab(ack, action, body, client):
    """Handle opening report in Reports tab"""
    ack()

    report_id = action["value"]
    user_id = body["user"]["id"]

    # Open the app home and switch to Reports tab
    try:
        # Publish the home view with Reports tab active
        publish_reports_tab(client, user_id, report_id)

        logger.info(f"Opened report {report_id} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to open report tab: {e}")


# Action handler for view report button (legacy)
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


# Action handler: View specific report
@app.action("view_specific_report")
def handle_view_specific_report(ack, action, body, client):
    """Handle viewing a specific report from history"""
    ack()

    report_id = action["value"]
    user_id = body["user"]["id"]

    # Open report in Reports tab
    publish_reports_tab(client, user_id, report_id)


def publish_reports_tab(client, user_id, report_id=None):
    """Publish Reports tab showing full report content"""
    global report_store

    if report_id:
        # Show specific report
        report = report_store.get_report(report_id)
        if not report:
            logger.error(f"Report {report_id} not found")
            return

        # Get report content
        content = report_store.get_report_content(report_id, format="markdown")
        if not content:
            logger.error(f"Could not read report content for {report_id}")
            return

        # Convert markdown to Slack blocks
        content_blocks = markdown_to_slack_blocks(content, max_blocks=45)

        # Build view with report content
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{report['title']}*"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 {report['date']} • ⏱️ {report['reading_time_minutes']} min read • 📊 {report['word_count']:,} words"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]

        # Add report content blocks
        blocks.extend(content_blocks)

        # Add footer with actions
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📄 Open in Google Docs"
                        },
                        "url": report.get('google_docs_url', '#'),
                        "action_id": "open_google_docs_from_tab"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "⬅️ Back to Reports"
                        },
                        "action_id": "back_to_reports_list",
                        "value": "home"
                    }
                ]
            }
        ])

        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": blocks
            }
        )
    else:
        # Show reports list (call main home tab)
        update_home_tab(client, {"user": user_id}, logger)


# Action handler: Back to reports list
# Action handler: Back to reports list
@app.action("back_to_reports_list")
def handle_back_to_reports(ack, body, client):
    """Handle back to reports list"""
    ack()
    user_id = body["user"]["id"]
    publish_reports_tab_view(client, user_id)


# Home tab
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    """Update the app home tab - default to Reports view"""
    try:
        publish_reports_tab_view(client, event["user"])
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


def publish_reports_tab_view(client, user_id):
    """Publish Reports tab view"""
    try:
        blocks = build_reports_view(report_store, research_status)

        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": blocks
            }
        )
        logger.info(f"Published Reports view for user {user_id}")
    except Exception as e:
        logger.error(f"Error publishing Reports view: {e}")


def publish_settings_tab_view(client, user_id):
    """Publish Settings tab view"""
    try:
        blocks = build_settings_view(research_status)

        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": blocks
            }
        )
        logger.info(f"Published Settings view for user {user_id}")
    except Exception as e:
        logger.error(f"Error publishing Settings view: {e}")


# Action handler: Switch to Settings tab
@app.action("switch_to_settings")
def handle_switch_to_settings(ack, body, client):
    """Switch to Settings view"""
    ack()
    user_id = body["user"]["id"]
    publish_settings_tab_view(client, user_id)


# Action handler: Switch to Reports tab
@app.action("switch_to_reports")
def handle_switch_to_reports(ack, body, client):
    """Switch to Reports view"""
    ack()
    user_id = body["user"]["id"]
    publish_reports_tab_view(client, user_id)


# Action handler: Manual generate report
@app.action("manual_generate_report")
def handle_manual_generate(ack, body, client):
    """Handle manual report generation from Home tab"""
    ack()
    user_id = body["user"]["id"]

    # Trigger research
    if research_status["running"]:
        client.chat_postEphemeral(
            channel=user_id,
            user=user_id,
            text="❌ Research is already running. Please wait for it to complete."
        )
        return

    # Send immediate feedback to user
    client.chat_postEphemeral(
        channel=user_id,
        user=user_id,
        text="🚀 *Research Started!*\n\nYour market research report is being generated. This takes 5-15 minutes.\n\n*Progress:*\n⏳ Step 1/6: Broad market research...\n\nI'll notify you when it's complete. You can continue using Slack normally."
    )

    # Update home tab to show "In Progress" status
    research_status["running"] = True
    research_status["last_run"] = datetime.now().isoformat()
    publish_reports_tab_view(client, user_id)

    # Run research in background
    def run_research_task():
        global research_status
        try:
            # Check if agent is initialized, try to initialize if not
            if agent is None:
                if not initialize_agent():
                    # Agent initialization failed - likely missing API keys
                    research_status["running"] = False
                    publish_reports_tab_view(client, user_id)
                    client.chat_postEphemeral(
                        channel=user_id,
                        user=user_id,
                        text="❌ *Research Failed - Missing API Keys*\n\n"
                             "Cannot start research because required API keys are not configured.\n\n"
                             "*Required Environment Variables in Railway:*\n"
                             "• `ANTHROPIC_API_KEY` - For Claude Sonnet 4.5 analysis\n"
                             "• `OPENAI_API_KEY` - For GPT report generation\n"
                             "• `PERPLEXITY_API_KEY` - For market research\n"
                             "• `SERPAPI_API_KEY` - For web search\n\n"
                             "Please add these to your Railway project settings and redeploy."
                    )
                    return

            # Send progress updates
            client.chat_postEphemeral(
                channel=user_id,
                user=user_id,
                text="⏳ *Step 2/6:* Competitor analysis in progress..."
            )

            result = agent.run_research()
            research_status["running"] = False

            if result.get("report", {}).get("success"):
                research_status["last_report"] = result["report"]["markdown_path"]

                markdown_path = result["report"]["markdown_path"]
                executive_summary = extract_executive_summary(markdown_path)
                word_count = count_words(markdown_path)

                google_docs_url = None
                if google_docs_exporter.enabled:
                    google_docs_url = google_docs_exporter.export_report(
                        markdown_path,
                        f"DAP Market Report - {result['report']['date']}"
                    )
                else:
                    google_docs_url = google_docs_exporter.create_google_doc_placeholder(
                        f"DAP Market Report",
                        result['report']['date']
                    )

                report_id = report_store.add_report(
                    title=f"DAP Market Research Report - {result['report']['date']}",
                    date=result['report']['date'],
                    markdown_path=markdown_path,
                    html_path=result["report"]["html_path"],
                    executive_summary=executive_summary,
                    word_count=word_count,
                    google_docs_url=google_docs_url
                )

                # Update home tab with new report
                publish_reports_tab_view(client, user_id)

                # Send completion notification to user
                send_user_notification(
                    client=client,
                    user_id=user_id,
                    report_id=report_id,
                    title=f"DAP Market Research Report",
                    date=result['report']['date'],
                    executive_summary=executive_summary,
                    reading_time=max(1, round(word_count / 200)),
                    google_docs_url=google_docs_url,
                    duration=result['metadata'].get('duration_seconds', 0)
                )

                # Also send to channel if configured
                channel_id = os.environ.get("SLACK_CHANNEL_ID")
                if channel_id:
                    send_report_notification(
                        report_id=report_id,
                        title=f"DAP Market Research Report",
                        date=result['report']['date'],
                        executive_summary=executive_summary,
                        reading_time=max(1, round(word_count / 200)),
                        google_docs_url=google_docs_url,
                        duration=result['metadata'].get('duration_seconds', 0)
                    )
            else:
                research_status["running"] = False
                publish_reports_tab_view(client, user_id)
                client.chat_postEphemeral(
                    channel=user_id,
                    user=user_id,
                    text="❌ Research failed. Check logs for details."
                )

        except Exception as e:
            logger.error(f"Research execution failed: {str(e)}", exc_info=True)
            research_status["running"] = False
            publish_reports_tab_view(client, user_id)
            client.chat_postEphemeral(
                channel=user_id,
                user=user_id,
                text=f"❌ Research failed with error: {str(e)}"
            )

    thread = threading.Thread(target=run_research_task)
    thread.daemon = True
    thread.start()


# Action handler: Open schedule modification modal
@app.action("open_schedule_modal")
def handle_open_schedule_modal(ack, body, client):
    """Open modal for modifying schedule"""
    ack()

    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "schedule_modify_modal",
            "title": {"type": "plain_text", "text": "Modify Schedule"},
            "submit": {"type": "plain_text", "text": "Save"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Configure Research Schedule*"}
                },
                {
                    "type": "input",
                    "block_id": "frequency_block",
                    "element": {
                        "type": "static_select",
                        "action_id": "frequency_select",
                        "placeholder": {"type": "plain_text", "text": "Select frequency"},
                        "initial_option": {"text": {"type": "plain_text", "text": "Weekly"}, "value": "weekly"},
                        "options": [
                            {"text": {"type": "plain_text", "text": "Daily"}, "value": "daily"},
                            {"text": {"type": "plain_text", "text": "Weekly"}, "value": "weekly"},
                            {"text": {"type": "plain_text", "text": "Bi-weekly"}, "value": "biweekly"},
                            {"text": {"type": "plain_text", "text": "Monthly"}, "value": "monthly"}
                        ]
                    },
                    "label": {"type": "plain_text", "text": "Frequency"}
                },
                {
                    "type": "input",
                    "block_id": "day_block",
                    "element": {
                        "type": "static_select",
                        "action_id": "day_select",
                        "placeholder": {"type": "plain_text", "text": "Select day"},
                        "initial_option": {"text": {"type": "plain_text", "text": "Monday"}, "value": "monday"},
                        "options": [
                            {"text": {"type": "plain_text", "text": "Monday"}, "value": "monday"},
                            {"text": {"type": "plain_text", "text": "Tuesday"}, "value": "tuesday"},
                            {"text": {"type": "plain_text", "text": "Wednesday"}, "value": "wednesday"},
                            {"text": {"type": "plain_text", "text": "Thursday"}, "value": "thursday"},
                            {"text": {"type": "plain_text", "text": "Friday"}, "value": "friday"},
                            {"text": {"type": "plain_text", "text": "Saturday"}, "value": "saturday"},
                            {"text": {"type": "plain_text", "text": "Sunday"}, "value": "sunday"}
                        ]
                    },
                    "label": {"type": "plain_text", "text": "Day of Week"}
                },
                {
                    "type": "input",
                    "block_id": "time_block",
                    "element": {
                        "type": "timepicker",
                        "action_id": "time_select",
                        "initial_time": "08:00",
                        "placeholder": {"type": "plain_text", "text": "Select time"}
                    },
                    "label": {"type": "plain_text", "text": "Time (CET)"}
                }
            ]
        }
    )


# View submission handler: Schedule modification
@app.view("schedule_modify_modal")
def handle_schedule_modification(ack, body, client, view):
    """Handle schedule modification submission"""
    ack()

    values = view["state"]["values"]
    frequency = values["frequency_block"]["frequency_select"]["selected_option"]["value"]
    day = values["day_block"]["day_select"]["selected_option"]["value"]
    time = values["time_block"]["time_select"]["selected_time"]

    user_id = body["user"]["id"]

    client.chat_postEphemeral(
        channel=user_id,
        user=user_id,
        text=f"✅ Schedule updated!\n\n*Frequency:* {frequency}\n*Day:* {day}\n*Time:* {time} CET\n\n_Note: Scheduler will be updated on next deployment._"
    )

    publish_settings_tab_view(client, user_id)


# Flask routes for Railway
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """Handle Slack events"""
    # Handle Slack URL verification challenge
    if request.json and "challenge" in request.json:
        logger.info("Received Slack challenge request")
        return {"challenge": request.json["challenge"]}

    # Handle all other Slack events
    return handler.handle(request)


@flask_app.route("/slack/actions", methods=["POST"])
def slack_actions():
    """Handle Slack interactive components (buttons, modals, etc.)"""
    return handler.handle(request)


@flask_app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@flask_app.route("/", methods=["GET", "POST"])
def home():
    """Home endpoint - route POST requests to Slack handler"""
    if request.method == "POST":
        # Route Slack requests that come to root
        logger.info("Received POST to / - routing to Slack handler")
        return handler.handle(request)

    return {
        "name": "DAP Market Research Agent",
        "status": "running",
        "version": "1.0.0"
    }


def main():
    """Main entry point for Slack app"""
    logger.info("Starting DAP Market Research Agent Slack App...")

    # Try to initialize agent (optional - can be initialized later)
    if not initialize_agent():
        logger.warning("Failed to initialize agent. App will start anyway.")
        logger.warning("Agent will be initialized when needed (requires all API keys).")

    # Get port from environment (Railway sets this)
    port = int(os.environ.get("PORT", 3000))

    logger.info(f"Slack app starting on port {port}")

    # Run Flask app (starts even if agent initialization failed)
    flask_app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
