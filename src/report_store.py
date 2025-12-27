"""Report storage and management using Postgres"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ReportStore:
    """Manages report metadata and storage in Postgres"""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            logger.warning("DATABASE_URL not set - reports will not persist!")
            self.database_url = None
        self._init_database()

    def _get_connection(self):
        """Get database connection"""
        if not self.database_url:
            return None
        try:
            return psycopg2.connect(self.database_url)
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None

    def _init_database(self):
        """Initialize database table"""
        if not self.database_url:
            return

        conn = self._get_connection()
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS market_reports (
                        id VARCHAR(255) PRIMARY KEY,
                        title TEXT NOT NULL,
                        date VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        markdown_content TEXT,
                        html_content TEXT,
                        executive_summary TEXT,
                        word_count INTEGER DEFAULT 0,
                        reading_time_minutes INTEGER DEFAULT 1,
                        google_docs_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info("Database table initialized")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
        finally:
            conn.close()

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
        Add a new report to the database

        Returns:
            Report ID
        """
        if not self.database_url:
            logger.warning("No database configured - report not saved!")
            return f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        conn = self._get_connection()
        if not conn:
            return ""

        try:
            # Generate unique ID
            report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Calculate reading time (average 200 words per minute)
            reading_time = max(1, round(word_count / 200))

            # Read report content
            markdown_content = ""
            html_content = ""

            try:
                if os.path.exists(markdown_path):
                    with open(markdown_path, 'r', encoding='utf-8') as f:
                        markdown_content = f.read()
            except Exception as e:
                logger.error(f"Error reading markdown file: {e}")

            try:
                if os.path.exists(html_path):
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
            except Exception as e:
                logger.error(f"Error reading HTML file: {e}")

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO market_reports
                    (id, title, date, timestamp, markdown_content, html_content,
                     executive_summary, word_count, reading_time_minutes, google_docs_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    report_id, title, date, datetime.now(),
                    markdown_content, html_content, executive_summary,
                    word_count, reading_time, google_docs_url
                ))
                conn.commit()

                # Verify insertion
                cur.execute("SELECT COUNT(*) FROM market_reports")
                total_count = cur.fetchone()[0]
                logger.info(f"✅ Added report to database: {report_id}")
                logger.info(f"📊 Total reports in database: {total_count}")

            return report_id

        except Exception as e:
            logger.error(f"Error adding report to database: {e}")
            return ""
        finally:
            conn.close()

    def get_report(self, report_id: str) -> Optional[Dict]:
        """Get a specific report by ID"""
        if not self.database_url:
            return None

        conn = self._get_connection()
        if not conn:
            return None

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, title, date, timestamp, executive_summary,
                           word_count, reading_time_minutes, google_docs_url
                    FROM market_reports
                    WHERE id = %s
                """, (report_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting report: {e}")
            return None
        finally:
            conn.close()

    def get_all_reports(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all reports (newest first)"""
        if not self.database_url:
            logger.warning("No database URL - returning empty list")
            return []

        conn = self._get_connection()
        if not conn:
            logger.error("Failed to get database connection")
            return []

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT id, title, date, timestamp, executive_summary,
                           word_count, reading_time_minutes, google_docs_url
                    FROM market_reports
                    ORDER BY timestamp DESC
                """
                if limit:
                    query += f" LIMIT {limit}"

                cur.execute(query)
                rows = cur.fetchall()

                # Convert to list of dicts and format timestamps
                reports = []
                for row in rows:
                    report_dict = dict(row)
                    # Convert timestamp to ISO format string if it's a datetime object
                    if 'timestamp' in report_dict and report_dict['timestamp']:
                        if hasattr(report_dict['timestamp'], 'isoformat'):
                            report_dict['timestamp'] = report_dict['timestamp'].isoformat()
                    reports.append(report_dict)

                logger.info(f"Retrieved {len(reports)} reports from database")
                return reports
        except Exception as e:
            logger.error(f"Error getting all reports: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    def get_latest_report(self) -> Optional[Dict]:
        """Get the most recent report"""
        reports = self.get_all_reports(limit=1)
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
        if not self.database_url:
            return None

        conn = self._get_connection()
        if not conn:
            return None

        try:
            column = "markdown_content" if format == "markdown" else "html_content"
            with conn.cursor() as cur:
                cur.execute(f"SELECT {column} FROM market_reports WHERE id = %s", (report_id,))
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Error reading report content: {e}")
            return None
        finally:
            conn.close()

    def delete_report(self, report_id: str) -> bool:
        """Delete a report from database"""
        if not self.database_url:
            return False

        conn = self._get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM market_reports WHERE id = %s", (report_id,))
                conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting report: {e}")
            return False
        finally:
            conn.close()

    def get_reports_count(self) -> int:
        """Get total number of reports"""
        if not self.database_url:
            return 0

        conn = self._get_connection()
        if not conn:
            return 0

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM market_reports")
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting reports: {e}")
            return 0
        finally:
            conn.close()
