import pytest
from src.nl_query.nl_to_sql import validate_sql
@pytest.mark.parametrize("sql",["DROP TABLE dealers","SELECT 1; DELETE FROM dealers","UPDATE dealers SET region='x'","INSERT INTO dealers VALUES (1)"])
def test_destructive_sql_rejected(sql):
    with pytest.raises(ValueError): validate_sql(sql)
def test_select_is_bounded(): assert validate_sql("SELECT * FROM dealers").endswith("LIMIT 200")
