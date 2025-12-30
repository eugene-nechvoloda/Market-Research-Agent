"""
n8n Webhook Integration Client

This module handles communication with n8n workflows for external research processing.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class N8NClient:
    """Client for triggering n8n research workflows and receiving results"""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize n8n client

        Args:
            webhook_url: n8n webhook URL to trigger research workflow
        """
        self.webhook_url = webhook_url or os.getenv("N8N_WEBHOOK_URL")
        if not self.webhook_url:
            logger.warning("N8N_WEBHOOK_URL not set - n8n integration disabled")

        self.enabled = bool(self.webhook_url)
        logger.info(f"n8n integration {'enabled' if self.enabled else 'disabled'}")

    def trigger_research(self, research_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Trigger n8n research workflow

        Args:
            research_params: Optional parameters to customize research
                - date: Report date (defaults to today)
                - focus_areas: List of specific areas to research
                - competitors: List of competitors to track

        Returns:
            Dict with trigger status and request_id
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "n8n integration not enabled - N8N_WEBHOOK_URL not configured"
            }

        try:
            # Prepare request payload
            payload = {
                "timestamp": datetime.now().isoformat(),
                "source": "dap-market-research-agent",
                "request_type": "research",
                "params": research_params or {}
            }

            logger.info(f"Triggering n8n research workflow at {self.webhook_url}")
            logger.debug(f"Payload: {payload}")

            # Send POST request to n8n webhook
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )

            response.raise_for_status()

            # Parse response
            result = response.json() if response.text else {}

            logger.info(f"✅ Successfully triggered n8n research workflow")
            logger.debug(f"Response: {result}")

            return {
                "success": True,
                "request_id": result.get("request_id", datetime.now().isoformat()),
                "status": result.get("status", "triggered"),
                "message": result.get("message", "Research workflow triggered successfully")
            }

        except requests.exceptions.Timeout:
            logger.error("n8n webhook request timed out after 30 seconds")
            return {
                "success": False,
                "error": "Request to n8n timed out"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger n8n workflow: {e}")
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error triggering n8n workflow: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def validate_research_data(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate research data received from n8n

        Args:
            data: Research data from n8n

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "Data must be a dictionary"

        # Check for required fields (flexible structure)
        # n8n can return either structured JSON or markdown
        if "markdown" in data or "json" in data or "results" in data:
            return True, None

        # If data has any content, consider it valid
        if data:
            return True, None

        return False, "Research data is empty"

    def format_research_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format research results from n8n into agent's expected structure

        Args:
            data: Raw research data from n8n

        Returns:
            Formatted research results compatible with agent's report generator
        """
        logger.info("Formatting research results from n8n")

        # If n8n returns markdown directly
        if "markdown" in data:
            return {
                "raw_markdown": data["markdown"],
                "source": "n8n",
                "timestamp": datetime.now().isoformat()
            }

        # If n8n returns structured JSON
        if "json" in data or "results" in data:
            return {
                "research_data": data.get("json") or data.get("results"),
                "source": "n8n",
                "timestamp": datetime.now().isoformat()
            }

        # Default: pass through as-is
        return {
            "research_data": data,
            "source": "n8n",
            "timestamp": datetime.now().isoformat()
        }
