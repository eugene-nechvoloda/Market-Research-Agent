"""Scheduler for automated weekly research execution"""
import schedule
import time
import logging
from datetime import datetime
import pytz
from typing import Callable

logger = logging.getLogger(__name__)


class ResearchScheduler:
    """Manages scheduled execution of market research"""

    def __init__(self, research_task: Callable, timezone: str = "CET"):
        """
        Initialize scheduler

        Args:
            research_task: Function to execute on schedule
            timezone: Timezone for scheduling (default: CET)
        """
        self.research_task = research_task
        self.timezone = pytz.timezone("Europe/Paris")  # CET timezone

    def schedule_weekly(self, day: str = "monday", time_str: str = "08:00"):
        """
        Schedule weekly execution

        Args:
            day: Day of week (monday, tuesday, etc.)
            time_str: Time in HH:MM format
        """
        logger.info(f"Scheduling research for every {day} at {time_str} CET")

        # Schedule the job
        schedule_func = getattr(schedule.every(), day.lower())
        schedule_func.at(time_str).do(self._run_task_with_logging)

        logger.info("Schedule configured successfully")

    def schedule_daily(self, time_str: str = "08:00"):
        """
        Schedule daily execution (for testing)

        Args:
            time_str: Time in HH:MM format
        """
        logger.info(f"Scheduling research for every day at {time_str} CET")
        schedule.every().day.at(time_str).do(self._run_task_with_logging)
        logger.info("Daily schedule configured successfully")

    def run_once(self):
        """Run the research task once immediately"""
        logger.info("Running research task once...")
        self._run_task_with_logging()

    def _run_task_with_logging(self):
        """Execute task with proper logging"""
        try:
            current_time = datetime.now(self.timezone)
            logger.info(f"Starting scheduled research execution at {current_time}")

            # Run the research task
            self.research_task()

            logger.info("Scheduled research execution completed successfully")

        except Exception as e:
            logger.error(f"Error during scheduled execution: {str(e)}", exc_info=True)

    def start(self, blocking: bool = True):
        """
        Start the scheduler

        Args:
            blocking: If True, run in blocking mode (keeps script running)
        """
        logger.info("Starting scheduler...")

        if blocking:
            logger.info("Scheduler running in blocking mode. Press Ctrl+C to stop.")
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
        else:
            # Non-blocking mode - run pending once
            schedule.run_pending()

    def get_next_run(self) -> str:
        """Get timestamp of next scheduled run"""
        next_run = schedule.next_run()
        if next_run:
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return "No scheduled runs"

    def clear_schedule(self):
        """Clear all scheduled jobs"""
        schedule.clear()
        logger.info("Schedule cleared")
