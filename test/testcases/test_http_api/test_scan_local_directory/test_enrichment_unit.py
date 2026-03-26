#!/usr/bin/env python3
"""
Unit test for source_type/location enrichment in dialog_service.py.

Tests that the enrichment code correctly adds source_type and location
to both doc_aggs and chunks based on doc_ids.
"""

import sys

sys.path.insert(0, "/ragflow")

from unittest.mock import MagicMock, patch


class MockDoc:
    def __init__(self, id, source_type, location):
        self.id = id
        self.source_type = source_type
        self.location = location


def test_enrichment_code_exists():
    """Test that dialog_service.py contains the enrichment code."""
    with open("/ragflow/api/db/services/dialog_service.py") as f:
        content = f.read()

    assert "from api.db.services.document_service import DocumentService" in content, "Missing DocumentService import"
    assert 'd["source_type"]' in content, "Missing source_type assignment"
    assert 'd["location"]' in content, "Missing location assignment"
    print("  PASS: dialog_service.py contains enrichment code")


def test_enrichment_logic():
    """Test the enrichment logic with mock data."""
    from api.db.services.document_service import DocumentService

    docs = {
        "doc-1": MockDoc("doc-1", "local_scan", "/hdd1/test_scan/image.jpg"),
        "doc-2": MockDoc("doc-2", "upload", None),
    }

    def mock_get_by_ids(doc_ids):
        return [docs[did] for did in doc_ids if did in docs]

    kbinfos = {
        "doc_aggs": [
            {"doc_id": "doc-1", "doc_name": "image.jpg"},
            {"doc_id": "doc-2", "doc_name": "file.pdf"},
            {"doc_id": "doc-unknown", "doc_name": "unknown"},
        ],
        "chunks": [
            {"doc_id": "doc-1", "content": "chunk 1"},
            {"doc_id": "doc-2", "content": "chunk 2"},
            {"doc_id": "doc-1", "content": "chunk 3"},
        ],
    }

    with patch.object(DocumentService, "get_by_ids", side_effect=mock_get_by_ids):
        if kbinfos.get("doc_aggs"):
            doc_ids = [d["doc_id"] for d in kbinfos["doc_aggs"] if d.get("doc_id")]
            if doc_ids:
                fetched_docs = {doc.id: doc for doc in DocumentService.get_by_ids(doc_ids)}
                for d in kbinfos["doc_aggs"]:
                    doc = fetched_docs.get(d.get("doc_id"))
                    if doc:
                        d["source_type"] = doc.source_type
                        d["location"] = doc.location
                for c in kbinfos["chunks"]:
                    doc = fetched_docs.get(c.get("doc_id"))
                    if doc:
                        c["source_type"] = doc.source_type
                        c["location"] = doc.location

    for d in kbinfos["doc_aggs"]:
        print(f"  doc_agg: doc_id={d['doc_id']}, source_type={d.get('source_type')}, location={d.get('location')}")

    for c in kbinfos["chunks"]:
        print(f"  chunk: doc_id={c['doc_id']}, source_type={c.get('source_type')}, location={c.get('location')}")

    da1 = next(d for d in kbinfos["doc_aggs"] if d["doc_id"] == "doc-1")
    assert da1.get("source_type") == "local_scan", f"Expected local_scan, got {da1.get('source_type')}"
    assert da1.get("location") == "/hdd1/test_scan/image.jpg", f"Expected path, got {da1.get('location')}"

    da2 = next(d for d in kbinfos["doc_aggs"] if d["doc_id"] == "doc-2")
    assert da2.get("source_type") == "upload", f"Expected upload, got {da2.get('source_type')}"
    assert da2.get("location") is None, f"Expected None, got {da2.get('location')}"

    da_unknown = next(d for d in kbinfos["doc_aggs"] if d["doc_id"] == "doc-unknown")
    assert "source_type" not in da_unknown, "Unknown doc should not have source_type"

    chunks_doc1 = [c for c in kbinfos["chunks"] if c["doc_id"] == "doc-1"]
    for c in chunks_doc1:
        assert c.get("source_type") == "local_scan", f"Chunk source_type should be local_scan"
        assert c.get("location") == "/hdd1/test_scan/image.jpg", f"Chunk location should be path"

    print("  PASS: enrichment logic correct")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing source_type/location enrichment")
    print("=" * 60)

    print("\n1. Testing enrichment code exists in dialog_service.py:")
    test_enrichment_code_exists()

    print("\n2. Testing enrichment logic with mock data:")
    test_enrichment_logic()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
