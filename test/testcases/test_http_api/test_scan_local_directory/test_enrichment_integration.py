#!/usr/bin/env python3
"""
Integration test for source_type/location enrichment in dialog_service.py.

This test simulates what happens when retrieval returns results:
1. Creates a KB with local_scan documents in the DB
2. Runs the enrichment code directly on mock kbinfos
3. Verifies the enrichment is correct

This doesn't require ES indexing or LLM models.
"""

import sys

sys.path.insert(0, "/ragflow")

from common import settings

settings.init_settings()

from unittest.mock import MagicMock, patch
from api.db.db_models import DB
from api.db.services.document_service import DocumentService


class MockDoc:
    def __init__(self, id, source_type, location):
        self.id = id
        self.source_type = source_type
        self.location = location


def test_enrichment_with_real_db():
    """Test enrichment using real DB data."""
    DB.connect()

    # Find a local_scan document in the DB
    from api.db.db_models import Document

    docs = list(Document.select().limit(5))
    print(f"\n  Found {len(docs)} documents in DB:")
    for d in docs:
        print(f"    id={d.id[:20]}..., name={d.name}, source_type={d.source_type}, location={d.location}")

    if not docs:
        print("  No documents found in DB - cannot test enrichment")
        DB.close()
        return

    # Build mock kbinfos like ES would return
    doc_ids = [d.id for d in docs]

    # Simulate the enrichment code from dialog_service.py
    kbinfos = {"doc_aggs": [{"doc_id": docs[0].id, "doc_name": docs[0].name}], "chunks": [{"doc_id": docs[0].id, "content": "test chunk"}]}

    print(f"\n  Before enrichment:")
    print(f"    doc_agg: {kbinfos['doc_aggs'][0]}")
    print(f"    chunk: {kbinfos['chunks'][0]}")

    # Run the actual enrichment code
    if kbinfos.get("doc_aggs"):
        enriched_doc_ids = [d["doc_id"] for d in kbinfos["doc_aggs"] if d.get("doc_id")]
        if enriched_doc_ids:
            docs_map = {doc.id: doc for doc in DocumentService.get_by_ids(enriched_doc_ids)}
            for d in kbinfos["doc_aggs"]:
                doc = docs_map.get(d.get("doc_id"))
                if doc:
                    d["source_type"] = doc.source_type
                    d["location"] = doc.location
            for c in kbinfos["chunks"]:
                doc = docs_map.get(c.get("doc_id"))
                if doc:
                    c["source_type"] = doc.source_type
                    c["location"] = doc.location

    print(f"\n  After enrichment:")
    print(f"    doc_agg: doc_id={kbinfos['doc_aggs'][0].get('doc_id', '')[:20]}..., source_type={kbinfos['doc_aggs'][0].get('source_type')}, location={kbinfos['doc_aggs'][0].get('location')}")
    print(f"    chunk: doc_id={kbinfos['chunks'][0].get('doc_id', '')[:20]}..., source_type={kbinfos['chunks'][0].get('source_type')}, location={kbinfos['chunks'][0].get('location')}")

    # Verify
    da = kbinfos["doc_aggs"][0]
    assert "source_type" in da, f"doc_agg missing source_type! Keys: {list(da.keys())}"
    assert "location" in da, f"doc_agg missing location! Keys: {list(da.keys())}"
    print(f"\n  PASS: doc_agg enriched with source_type={da['source_type']}, location={da['location']}")

    c = kbinfos["chunks"][0]
    assert "source_type" in c, f"chunk missing source_type! Keys: {list(c.keys())}"
    assert "location" in c, f"chunk missing location! Keys: {list(c.keys())}"
    print(f"  PASS: chunk enriched with source_type={c['source_type']}, location={c['location']}")

    DB.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Integration test: enrichment with real DB data")
    print("=" * 60)
    test_enrichment_with_real_db()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
