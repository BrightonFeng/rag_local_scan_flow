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


def start_scan_scheduler():
    """Start the background scheduler for scanned directories."""
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
                                do_scan(d.kb_id, d.directory_path, d.scan_interval_minutes)
                            except Exception as e:
                                logging.error(f"Auto-scan failed for {d.directory_path}: {str(e)}")
            except Exception as e:
                logging.error(f"Background scan scheduler error: {str(e)}")
                time.sleep(60)

    thread = threading.Thread(target=scan_worker, daemon=True)
    thread.start()
    logging.info("Scanned directory background scheduler started")


def do_scan(kb_id, path, scan_interval=60):
    """Core scanning logic for background scheduler."""
    from api.db.services.knowledgebase_service import KnowledgebaseService
    from api.db.services.document_service import DocumentService
    from api.db.services.file_service import FileService
    from api.db.services.file2document_service import File2DocumentService
    from api.db.services.scanned_directory_service import ScannedDirectoryService
    from api.db.db_models import File, File2Document, Document

    logging.info(f"Starting auto-scan for path: {path}, kb_id: {kb_id}")

    e, kb = KnowledgebaseService.get_by_id(kb_id)
    if not e:
        logging.error(f"Knowledgebase not found: {kb_id}")
        return

    path = os.path.abspath(path)
    if not os.path.exists(path):
        logging.error(f"Path does not exist: {path}")
        return
    if not os.path.isdir(path):
        logging.error(f"Path is not a directory: {path}")
        return

    supported_extensions = (
        r".*\.pdf$|"
        r".*\.(msg|eml|doc|docx|ppt|pptx|yml|xml|htm|json|jsonl|ldjson|csv|txt|ini|xls|xlsx|wps|rtf|hlp|pages|numbers|key|md|py|js|java|c|cpp|h|php|go|ts|sh|cs|kt|html|sql)$|"
        r".*\.(wav|flac|ape|alac|wv|mp3|aac|ogg|vorbis|opus)$|"
        r".*\.(jpg|jpeg|png|tif|gif|pcx|tga|exif|fpx|svg|psd|cdr|pcd|dxf|ufo|eps|ai|raw|webp|avif|apng|icon|ico|mpg|mpeg|avi|rm|rmvb|mov|wmv|asf|dat|asx|wvx|mpe|mpa|mp4|avi|mkv)$"
    )

    files_to_import = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if re.match(supported_extensions, file, re.IGNORECASE):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, path)
                files_to_import.append((file_path, rel_path))

    if not files_to_import:
        logging.info(f"No supported files found in: {path}")
        ScannedDirectoryService.update_last_scan_time_by_path(kb_id, path)
        return

    existing_dirs = ScannedDirectoryService.get_by_kb_id(kb_id)
    scan_dir_id = None
    for existing_dir in existing_dirs:
        if existing_dir.directory_path == path:
            scan_dir_id = existing_dir.id
            break

    if not scan_dir_id:
        new_id = uuid4().hex
        scan_dir_id = new_id
        ScannedDirectoryService.insert(
            id=new_id,
            kb_id=kb_id,
            directory_path=path,
            scan_interval_minutes=scan_interval,
            created_by=kb.tenant_id,
        )

    imported_docs = []

    current_file_paths = set()
    for file_path, rel_path in files_to_import:
        current_file_paths.add(file_path)

    existing_docs = list(DocumentService.query(kb_id=kb.id, source_type=FileSource.LOCAL_SCAN.value))
    deleted_count = 0
    skipped_count = 0
    reparsed_count = 0

    for existing_doc in existing_docs:
        doc_location = existing_doc.location
        if not doc_location or not doc_location.startswith(path):
            continue

        if doc_location not in current_file_paths:
            try:
                File2DocumentService.delete_by_document_id(existing_doc.id)
            except:
                pass
            try:
                File.delete_by_id(existing_doc.id)
            except:
                pass
            try:
                Document.delete_by_id(existing_doc.id)
            except:
                pass
            deleted_count += 1
            logging.info(f"Deleted document (file removed): {existing_doc.name}, location: {doc_location}")
        else:
            try:
                file_stat = os.stat(doc_location)
                if existing_doc.size == file_stat.st_size:
                    skipped_count += 1
                    logging.info(f"Skipped (unchanged): {existing_doc.name}, size: {file_stat.st_size}")
                    continue
                else:
                    reparsed_count += 1
                    logging.info(f"Re-parsing (modified): {existing_doc.name}, old size: {existing_doc.size}, new size: {file_stat.st_size}")
                    try:
                        File2DocumentService.delete_by_document_id(existing_doc.id)
                    except:
                        pass
                    try:
                        File.delete_by_id(existing_doc.id)
                    except:
                        pass
                    try:
                        Document.delete_by_id(existing_doc.id)
                    except:
                        pass
            except OSError:
                pass

    logging.info(f"Auto-scan summary: deleted={deleted_count}, skipped={skipped_count}, reparsed={reparsed_count}, new={len(files_to_import) - skipped_count - reparsed_count}")

    for file_path, rel_path in files_to_import:
        try:
            existing_docs = list(DocumentService.query(kb_id=kb.id, location=file_path))
            if existing_docs:
                skipped_count += 1
                continue

            filename = os.path.basename(file_path)
            doc_id = uuid4().hex

            from api.utils.file_utils import filename_type
            from api.db import FileType
            from common.constants import ParserType

            filetype = filename_type(filename)
            file_parser = kb.parser_id
            if filetype == FileType.VISUAL.value:
                file_parser = ParserType.PICTURE.value
            elif filetype == FileType.AURAL.value:
                file_parser = ParserType.AUDIO.value

            doc = {
                "id": doc_id,
                "kb_id": kb.id,
                "parser_id": file_parser,
                "pipeline_id": kb.pipeline_id,
                "parser_config": kb.parser_config,
                "created_by": kb.tenant_id,
                "type": filename.split(".")[-1] if "." in filename else "",
                "name": filename,
                "source_type": FileSource.LOCAL_SCAN.value,
                "suffix": filename.split(".")[-1] if "." in filename else "",
                "location": file_path,
                "size": os.path.getsize(file_path),
                "thumbnail": "",
                "content_hash": "",
                "run": "1",
                "status": "1",
                "progress": 0,
            }
            DocumentService.insert(doc)

            kb_folder = FileService.get_kb_folder(kb.tenant_id)
            parent_id = kb_folder.get("id")

            file_rec = {
                "id": doc_id,
                "parent_id": parent_id,
                "tenant_id": kb.tenant_id,
                "created_by": kb.tenant_id,
                "name": filename,
                "location": file_path,
                "size": os.path.getsize(file_path),
                "type": filename.split(".")[-1] if "." in filename else "",
                "source_type": "",
            }
            File.insert(**file_rec).execute()

            try:
                File2Document.insert(id=doc_id, document_id=doc_id, file_id=doc_id).execute()
            except Exception:
                pass

            doc["tenant_id"] = kb.tenant_id
            DocumentService.run(kb.tenant_id, doc, {})
            imported_docs.append(doc_id)
        except Exception as e:
            logging.error(f"Failed to process file {rel_path}: {str(e)}")

    ScannedDirectoryService.update_last_scan_time_by_path(kb_id, path)
    logging.info(f"Auto-scan completed: {len(imported_docs)} files imported from {path}")


start_scan_scheduler()
