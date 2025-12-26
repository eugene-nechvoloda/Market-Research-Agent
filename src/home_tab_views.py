"""Home tab view builders for Slack app"""
from datetime import datetime, timedelta
import pytz


def calculate_next_monday_8am():
    """Calculate next Monday 8:00 AM CET"""
    cet = pytz.timezone('Europe/Paris')
    now = datetime.now(cet)

    # Find next Monday
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0 and now.hour >= 8:
        days_until_monday = 7

    next_monday = now + timedelta(days=days_until_monday)
    next_run = next_monday.replace(hour=8, minute=0, second=0, microsecond=0)

    # Calculate days remaining
    time_until = next_run - now
    days_remaining = time_until.days
    hours_remaining = time_until.seconds // 3600

    return {
        "next_run_date": next_run.strftime("%Y-%m-%d %H:%M CET"),
        "next_run_timestamp": next_run,
        "days_remaining": days_remaining,
        "hours_remaining": hours_remaining,
        "countdown_text": f"{days_remaining}d {hours_remaining}h"
    }


def build_reports_view(report_store, research_status):
    """Build the Reports tab view"""
    reports = report_store.get_all_reports()

    blocks = [
        # Navigation
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📊 Reports* | Settings"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "⚙️ Settings"
                    },
                    "action_id": "switch_to_settings",
                    "value": "settings"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔄 Generate Report"
                    },
                    "style": "primary",
                    "action_id": "manual_generate_report",
                    "value": "generate",
                    "confirm": {
                        "title": {
                            "type": "plain_text",
                            "text": "Generate Report"
                        },
                        "text": {
                            "type": "mrkdwn",
                            "text": "This will start a new market research report generation (takes 5-15 minutes). Continue?"
                        },
                        "confirm": {
                            "type": "plain_text",
                            "text": "Yes, Generate"
                        },
                        "deny": {
                            "type": "plain_text",
                            "text": "Cancel"
                        }
                    }
                }
            ]
        },
        {
            "type": "divider"
        }
    ]

    # Show progress indicator if research is running
    if research_status.get("running"):
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🔄 *Research in Progress*\n\nGenerating market research report... This takes 5-15 minutes.\nYou'll receive a notification when it's complete."
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "⏳ Please wait... You can continue using Slack normally."
                    }
                ]
            },
            {
                "type": "divider"
            }
        ])

    # Report grid
    if reports:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📚 All Reports* ({len(reports)} total)"
            }
        })

        # Add report cards in grid-like layout (2 per row using fields)
        for i in range(0, len(reports), 2):
            report1 = reports[i]
            report2 = reports[i + 1] if i + 1 < len(reports) else None

            # Create section with two reports side by side
            section = {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{report1['title']}*\n📅 {report1['date']}\n⏱️ {report1['reading_time_minutes']} min read"
                    }
                ]
            }

            if report2:
                section["fields"].append({
                    "type": "mrkdwn",
                    "text": f"*{report2['title']}*\n📅 {report2['date']}\n⏱️ {report2['reading_time_minutes']} min read"
                })

            blocks.append(section)

            # Add action buttons for the reports
            action_elements = [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": f"📖 Open"
                    },
                    "action_id": "view_specific_report",
                    "value": report1['id']
                }
            ]

            if report2:
                action_elements.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": f"📖 Open"
                    },
                    "action_id": "view_specific_report",
                    "value": report2['id']
                })

            blocks.append({
                "type": "actions",
                "elements": action_elements
            })

            blocks.append({"type": "divider"})
    else:
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "📭 *No reports yet*\n\nClick 'Generate Report' above to create your first market research report!"
                }
            }
        ])

    return blocks


def build_settings_view(research_status):
    """Build the Settings tab view"""
    next_run_info = calculate_next_monday_8am()

    # Get current status
    status_emoji = "🔄" if research_status.get("running") else "✅"
    status_text = "Running" if research_status.get("running") else "Idle"

    # Format last run
    last_run = research_status.get("last_run")
    if last_run and isinstance(last_run, str):
        try:
            last_run = datetime.fromisoformat(last_run).strftime("%Y-%m-%d %H:%M:%S")
        except:
            last_run = "Never"
    else:
        last_run = "Never"

    blocks = [
        # Navigation
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📊 Reports | *⚙️ Settings*"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Reports"
                    },
                    "action_id": "switch_to_reports",
                    "value": "reports"
                }
            ]
        },
        {
            "type": "divider"
        },
        # Status Section
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📊 Current Status*"
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
                    "text": f"*Last Run:*\n{last_run}"
                }
            ]
        },
        {
            "type": "divider"
        },
        # Schedule Section
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📅 Schedule Configuration*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Frequency:*\nWeekly"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Day & Time:*\nMonday 8:00 AM CET"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Next Run:*\n" + next_run_info['next_run_date']
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Countdown:*\n⏰ {next_run_info['countdown_text']} remaining"
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✏️ Modify Schedule"
                    },
                    "action_id": "open_schedule_modal",
                    "value": "modify_schedule"
                }
            ]
        },
        {
            "type": "divider"
        },
        # API Keys Status
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🔑 API Keys Status*\n\n_Configure in Railway environment variables_"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 Required: Perplexity, SerpAPI, Anthropic, OpenAI API keys"
                }
            ]
        }
    ]

    return blocks
