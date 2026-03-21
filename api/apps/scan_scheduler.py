"""
Background scheduler for periodic directory scanning.
"""

import logging
import threading
import time
import os
import re
from datetime import datetime
from uuid import uuid4
from common.constants import FileSource

_scheduler_started = False


def start_scan_scheduler():
    """Start the background scheduler for scanned directories."""
    global _scheduler_started
    if _scheduler_started:
        logging.info("Scan scheduler already started, skipping")
        return
    _scheduler_started = True

    logging.info("Starting scanned directory background scheduler")

    def scan_worker():
        while True:
            try:
                time.sleep(60)

                from api.db.services.scanned_directory_service import ScannedDirectoryService
                from api.db.services.knowledgebase_service import KnowledgebaseService
                from api.db.services.document_service import DocumentService
                from api.db.services.file_service import FileService
                from api.db.services.file2document_service import File2DocumentService
                from api.db.db_models import File, File2Document, Document

                all_dirs = ScannedDirectoryService.get_all()
                now = datetime.now()

                for d in all_dirs:
                    if d.last_scan_time:
                        time_since_last_scan = (now - d.last_scan_time).total_seconds() / 60
                        if time_since_last_scan >= d.scan_interval_minutes:
                            logging.info(f"Auto-scanning directory: {d.directory_path}, kb_id={d.kb_id}")
                            try:
                                success, data, error = ScannedDirectoryService.scan_directory(d.kb_id, d.directory_path, d.scan_interval_minutes, tenant_id=d.created_by)
                                if not success:
                                    logging.error(f"Auto-scan failed for {d.directory_path}: {error}")
                            except Exception as e:
                                logging.error(f"Auto-scan failed for {d.directory_path}: {str(e)}")
            except Exception as e:
                logging.error(f"Background scan scheduler error: {str(e)}")
                time.sleep(60)

    thread = threading.Thread(target=scan_worker, daemon=True)
    thread.start()
    logging.info("Scanned directory background scheduler started")


start_scan_scheduler()
