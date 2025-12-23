"""Slack client for sending notifications"""
import os
from typing import Optional, Dict
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class SlackClient:
    """Client for sending Slack notifications"""

    def __init__(self, token: Optional[str] = None, channel_id: Optional[str] = None):
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        self.channel_id = channel_id or os.getenv("SLACK_CHANNEL_ID")

        if not self.token:
            raise ValueError("Slack bot token not provided")
        if not self.channel_id:
            raise ValueError("Slack channel ID not provided")

        self.client = WebClient(token=self.token)

    def send_message(self, text: str, blocks: Optional[list] = None) -> Dict:
        """
        Send a message to Slack channel

        Args:
            text: Message text (fallback)
            blocks: Optional Slack Block Kit blocks

        Returns:
            Response from Slack API
        """
        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=text,
                blocks=blocks
            )
            logger.info(f"Slack message sent successfully to {self.channel_id}")
            return {"success": True, "response": response}

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {"success": False, "error": e.response["error"]}

    def send_report_notification(
        self,
        report_url: str,
        summary: str,
        report_date: str
    ) -> Dict:
        """
        Send formatted report notification

        Args:
            report_url: URL to the generated report
            summary: Brief summary of key findings
            report_date: Date of the report

        Returns:
            Response from Slack API
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Weekly DAP Market Research Report Ready"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Report Date:* {report_date}\n\n*Key Highlights:*\n{summary}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📄 View Full Report"
                        },
                        "url": report_url,
                        "style": "primary"
                    }
                ]
            }
        ]

        return self.send_message(
            text=f"Weekly DAP Market Research Report for {report_date} is ready!",
            blocks=blocks
        )

    def upload_file(
        self,
        file_path: str,
        title: Optional[str] = None,
        initial_comment: Optional[str] = None
    ) -> Dict:
        """
        Upload a file to Slack channel

        Args:
            file_path: Path to file to upload
            title: Optional file title
            initial_comment: Optional comment

        Returns:
            Response from Slack API
        """
        try:
            response = self.client.files_upload_v2(
                channel=self.channel_id,
                file=file_path,
                title=title,
                initial_comment=initial_comment
            )
            logger.info(f"File uploaded successfully to {self.channel_id}")
            return {"success": True, "response": response}

        except SlackApiError as e:
            logger.error(f"Slack file upload error: {e.response['error']}")
            return {"success": False, "error": e.response["error"]}
