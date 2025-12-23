"""Report storage and management"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ReportStore:
    """Manages report metadata and storage"""

    def __init__(self, storage_path: str = "reports/reports_index.json"):
        self.storage_path = storage_path
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Ensure the index file exists"""
        if not os.path.exists(self.storage_path):
            self._save_index([])

    def _load_index(self) -> List[Dict]:
        """Load reports index"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return []

    def _save_index(self, reports: List[Dict]):
        """Save reports index"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(reports, separators=(',', ':'), indent=2, fp=f)
        except Exception as e:
            logger.error(f"Error saving index: {e}")

    def add_report(
        self,
        title: str,
        date: str,
        markdown_path: str,
        html_path: str,
        executive_summary: str,
        word_count: int = 0,
        google_docs_url: Optional[str] = None
    ) -> str:
        """
        Add a new report to the index

        Returns:
            Report ID
        """
        reports = self._load_index()

        # Generate unique ID
        report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Calculate reading time (average 200 words per minute)
        reading_time = max(1, round(word_count / 200))

        report_entry = {
            "id": report_id,
            "title": title,
            "date": date,
            "timestamp": datetime.now().isoformat(),
            "markdown_path": markdown_path,
            "html_path": html_path,
            "executive_summary": executive_summary,
            "word_count": word_count,
            "reading_time_minutes": reading_time,
            "google_docs_url": google_docs_url
        }

        reports.insert(0, report_entry)  # Add to beginning (newest first)
        self._save_index(reports)

        logger.info(f"Added report to index: {report_id}")
        return report_id

    def get_report(self, report_id: str) -> Optional[Dict]:
        """Get a specific report by ID"""
        reports = self._load_index()
        for report in reports:
            if report["id"] == report_id:
                return report
        return None

    def get_all_reports(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all reports (newest first)"""
        reports = self._load_index()
        if limit:
            return reports[:limit]
        return reports

    def get_latest_report(self) -> Optional[Dict]:
        """Get the most recent report"""
        reports = self._load_index()
        return reports[0] if reports else None

    def get_report_content(self, report_id: str, format: str = "markdown") -> Optional[str]:
        """
        Get report content

        Args:
            report_id: Report ID
            format: 'markdown' or 'html'

        Returns:
            Report content or None
        """
        report = self.get_report(report_id)
        if not report:
            return None

        path_key = f"{format}_path"
        file_path = report.get(path_key)

        if not file_path or not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading report content: {e}")
            return None

    def delete_report(self, report_id: str) -> bool:
        """Delete a report from index"""
        reports = self._load_index()
        updated_reports = [r for r in reports if r["id"] != report_id]

        if len(updated_reports) < len(reports):
            self._save_index(updated_reports)
            return True
        return False

    def get_reports_count(self) -> int:
        """Get total number of reports"""
        return len(self._load_index())
