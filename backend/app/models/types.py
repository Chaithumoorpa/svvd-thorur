from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import ARRAY

# PostgreSQL ARRAY(String) in production; JSON on SQLite so the test-suite can
# create the schema without a Postgres server.
StringArray = ARRAY(String).with_variant(JSON(), "sqlite")

# Money is always Numeric, never float/int.
MONEY_PRECISION = 12
MONEY_SCALE = 2
