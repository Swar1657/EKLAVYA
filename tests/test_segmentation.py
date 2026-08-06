import pytest
pytest.importorskip("sqlalchemy")
def test_dealer_segments_if_database_available():
    from src.db.connection import get_engine
    from sqlalchemy import text
    try:
        with get_engine().connect() as c: rows=c.execute(text("SELECT dealer_id,cluster_id,segment_label FROM dealer_segments")).all()
    except Exception: pytest.skip("Postgres segmentation results are not available")
    assert len(rows)==70 and 3<=len(set(r[1] for r in rows))<=5 and all(r[2] for r in rows)
