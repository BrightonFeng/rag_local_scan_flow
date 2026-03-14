from datetime import datetime

from api.db.db_models import DB, logging
from api.db.db_models import ScannedDirectory
from api.db.services.common_service import CommonService


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
    @DB.connection_context()
    def get_documents_by_directory(cls, directory_path, kb_id):
        from api.db.db_models import Document
        from api.db.db_models import File2Document

        doc_ids = list(Document.select(Document.id).where(Document.source_type == "local_path", Document.location.startswith(directory_path), Document.kb_id == kb_id))

        file_ids = list(File2Document.select(File2Document.file_id).where(File2Document.document_id.in_([d.id for d in doc_ids])))

        return file_ids
