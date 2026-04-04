from datetime import datetime

from api.db.db_models import DB, logging
from api.db.db_models import ScannedDirectory
from api.db.services.common_service import CommonService
from common.constants import FileSource


SUPPORTED_EXTENSIONS = (
    r".*\.pdf$|"
    r".*\.(msg|eml|doc|docx|ppt|pptx|yml|xml|htm|json|jsonl|ldjson|csv|txt|ini|xls|xlsx|wps|rtf|hlp|pages|numbers|key|md|py|js|java|c|cpp|h|php|go|ts|sh|cs|kt|html|sql)$|"
    r".*\.(wav|flac|ape|alac|wv|mp3|aac|ogg|vorbis|opus)$|"
    r".*\.(jpg|jpeg|png|tif|gif|pcx|tga|exif|fpx|svg|psd|cdr|pcd|dxf|ufo|eps|ai|raw|webp|avif|apng|icon|ico|mpg|mpeg|avi|rm|rmvb|mov|wmv|asf|dat|asx|wvx|mpe|mpa|mp4|avi|mkv)$"
)

MAX_SCAN_FILE_COUNT = 10000


class ScannedDirectoryService(CommonService):
    model = ScannedDirectory

    @classmethod
    @DB.connection_context()
    def get_all(cls):
        return list(cls.model.select())

    @classmethod
    @DB.connection_context()
    def get_by_kb_id(cls, kb_id):
        return list(cls.model.select().where(cls.model.kb_id == kb_id))

    @classmethod
    @DB.connection_context()
    def add(cls, kb_id, directory_path, scan_interval_minutes, created_by):
        from uuid import uuid4

        return cls.insert(
            id=uuid4().hex,
            kb_id=kb_id,
            directory_path=directory_path,
            scan_interval_minutes=scan_interval_minutes,
            created_by=created_by,
            created_at=datetime.now(),
        )

    @classmethod
    @DB.connection_context()
    def update_last_scan_time(cls, directory_id):
        cls.model.update(last_scan_time=datetime.now()).where(cls.model.id == directory_id).execute()

    @classmethod
    @DB.connection_context()
    def update_last_scan_time_by_path(cls, kb_id, directory_path):
        cls.model.update(last_scan_time=datetime.now()).where((cls.model.kb_id == kb_id) & (cls.model.directory_path == directory_path)).execute()

    @classmethod
    @DB.connection_context()
    def update_scan_interval(cls, directory_id, scan_interval_minutes):
        cls.model.update(scan_interval_minutes=scan_interval_minutes).where(cls.model.id == directory_id).execute()

    @classmethod
    @DB.connection_context()
    def delete_by_id(cls, pid):
        cls.model.delete().where(cls.model.id == pid).execute()

    @classmethod
    def scan_directory(cls, kb_id, path, scan_interval=60, created_by=None, tenant_id=None, priority=0):
        """
        Core scanning logic for local directory scan.

        Args:
            kb_id: Knowledge base ID
            path: Directory path to scan
            scan_interval: Scan interval in minutes
            created_by: User ID who initiated the scan (for API calls)
            tenant_id: Tenant ID (alternative to created_by for background scans)
            priority: Task priority (0=normal, 1=high)

        Returns:
            tuple: (success: bool, data: dict or scan_dir_id, error_message: str or None)
        """
        from uuid import uuid4
        import os
        import re
        from api.db.services.knowledgebase_service import KnowledgebaseService
        from api.db.services.document_service import DocumentService
        from api.db.services.file_service import FileService
        from api.db.services.file2document_service import File2DocumentService
        from api.db.db_models import File, File2Document, Document
        from api.utils.file_utils import filename_type
        from api.db import FileType
        from common.constants import ParserType

        e, kb = KnowledgebaseService.get_by_id(kb_id)
        if not e:
            return False, None, f"Knowledgebase not found: {kb_id}"

        path = os.path.abspath(path)
        if not os.path.exists(path):
            return False, None, f"Path does not exist: {path}"
        if not os.path.isdir(path):
            return False, None, f"Path is not a directory: {path}"

        creator = created_by or tenant_id
        if not creator:
            return False, None, "No creator specified"

        # Count files first
        file_count = 0
        for root, dirs, files in os.walk(path):
            for file in files:
                if re.match(SUPPORTED_EXTENSIONS, file, re.IGNORECASE):
                    file_count += 1
                    if file_count > MAX_SCAN_FILE_COUNT:
                        return False, None, f"所选目录包含超过 {MAX_SCAN_FILE_COUNT} 个文件。请将目录拆分为多个子目录后逐个添加。"

        # Collect files to import
        files_to_import = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if re.match(SUPPORTED_EXTENSIONS, file, re.IGNORECASE):
                    files_to_import.append((os.path.join(root, file), os.path.relpath(os.path.join(root, file), path)))

        # Get or create scanned directory record
        existing_dirs = cls.get_by_kb_id(kb_id)
        scan_dir_id = None
        for existing_dir in existing_dirs:
            if existing_dir.directory_path == path:
                cls.update_last_scan_time(existing_dir.id)
                scan_dir_id = existing_dir.id
                break

        if not scan_dir_id:
            new_id = uuid4().hex
            scan_dir_id = new_id
            cls.insert(
                id=new_id,
                kb_id=kb_id,
                directory_path=path,
                scan_interval_minutes=scan_interval,
                created_by=creator,
                created_at=datetime.now(),
            )
            cls.update_last_scan_time(scan_dir_id)

        # Build current file paths set
        if not files_to_import:
            current_file_paths = set()
        else:
            current_file_paths = {fp for fp, _ in files_to_import}

        # Get existing docs for this KB from this directory
        existing_docs = list(DocumentService.query(kb_id=kb.id, source_type=FileSource.LOCAL_SCAN.value))

        deleted_count = 0
        skipped_count = 0
        reparsed_count = 0
        imported_docs = []
        errors = []

        # Process deletions and re-parsing
        for existing_doc in existing_docs:
            doc_location = existing_doc.location
            if not doc_location or not doc_location.startswith(path):
                continue

            if doc_location not in current_file_paths:
                # File was deleted
                try:
                    File2DocumentService.delete_by_document_id(existing_doc.id)
                    File.delete_by_id(existing_doc.id)
                    tenant_id_for_del = DocumentService.get_tenant_id(existing_doc.id)
                    DocumentService.remove_document(existing_doc, tenant_id_for_del)
                except Exception as e:
                    logging.warning(f"Failed to delete document {existing_doc.id}: {e}")
                deleted_count += 1
                logging.info(f"Deleted document (file removed): {existing_doc.name}, location: {doc_location}")
            else:
                # File exists, check if modified (size or mtime changed)
                # Use content_hash field to store mtime for LOCAL_SCAN documents
                try:
                    file_stat = os.stat(doc_location)
                    current_mtime = str(int(file_stat.st_mtime))
                    if existing_doc.size == file_stat.st_size and existing_doc.content_hash == current_mtime:
                        skipped_count += 1
                        logging.info(f"Skipped (unchanged): {existing_doc.name}, size: {file_stat.st_size}, mtime: {current_mtime}")
                        continue
                    else:
                        old_mtime = existing_doc.content_hash or "N/A"
                        logging.info(f"Re-parsing (modified): {existing_doc.name}, old size: {existing_doc.size}, new size: {file_stat.st_size}, old mtime: {old_mtime}, new mtime: {current_mtime}")
                        try:
                            File2DocumentService.delete_by_document_id(existing_doc.id)
                            File.delete_by_id(existing_doc.id)
                            tenant_id_for_reparse = DocumentService.get_tenant_id(existing_doc.id)
                            DocumentService.remove_document(existing_doc, tenant_id_for_reparse)
                            reparsed_count += 1
                        except Exception as e:
                            logging.warning(f"Failed to delete document {existing_doc.id} for re-parsing: {e}")
                except OSError:
                    pass

        logging.info(f"Scan summary: deleted={deleted_count}, skipped={skipped_count}, reparsed={reparsed_count}, new={len(files_to_import) - skipped_count - reparsed_count}")

        # Import new files
        for file_path, rel_path in files_to_import:
            try:
                # Check if doc already exists (for re-parsed files that were just deleted)
                existing_check = list(DocumentService.query(kb_id=kb.id, location=file_path))
                if existing_check:
                    skipped_count += 1
                    continue

                filename = os.path.basename(file_path)
                doc_id = uuid4().hex

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
                    "created_by": creator,
                    "type": filename.split(".")[-1] if "." in filename else "",
                    "name": filename,
                    "source_type": FileSource.LOCAL_SCAN.value,
                    "suffix": filename.split(".")[-1] if "." in filename else "",
                    "location": file_path,
                    "size": os.path.getsize(file_path),
                    "thumbnail": "",
                    "content_hash": str(int(os.path.getmtime(file_path))),
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
                    "created_by": creator,
                    "name": filename,
                    "location": file_path,
                    "size": os.path.getsize(file_path),
                    "type": filename.split(".")[-1] if "." in filename else "",
                    "source_type": "",
                }
                File.insert(**file_rec).execute()

                try:
                    File2Document.insert(id=doc_id, document_id=doc_id, file_id=doc_id).execute()
                except Exception as e:
                    logging.warning(f"Failed to create File2Document for {rel_path}: {e}")

                doc["tenant_id"] = kb.tenant_id
                DocumentService.run(kb.tenant_id, doc, {}, priority=priority)
                imported_docs.append(doc_id)
            except Exception as e:
                logging.error(f"Failed to process file {rel_path}: {str(e)}")
                errors.append(f"{rel_path}: {str(e)}")

        cls.update_last_scan_time_by_path(kb_id, path)

        return (
            True,
            {
                "imported": imported_docs,
                "errors": errors,
                "scan_dir_id": scan_dir_id,
                "deleted": deleted_count,
                "skipped": skipped_count,
                "reparsed": reparsed_count,
            },
            None,
        )
