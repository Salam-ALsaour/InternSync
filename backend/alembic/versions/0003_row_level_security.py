"""row level security on every table; unused file-link setting removed (Increment 2 design, Section 10)

On the hosted database, tables in the public schema can also be reached through the provider's Data API. With row
level security on and no policy, that path returns nothing; the API connects as the owner of the tables, which row
level security does not restrict. Later migrations that add tables run the same statement for them.

Files are always streamed by the API after the permission check (CR-08), so `files.signed_url_seconds` is unused.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-26 01:20:00
"""
from alembic import op

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None

EACH_TABLE = """
DO $$
DECLARE t record;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE format('ALTER TABLE public.%I {} ROW LEVEL SECURITY', t.tablename);
    END LOOP;
END $$
"""


def upgrade() -> None:
    op.execute(EACH_TABLE.format("ENABLE"))
    op.execute("DELETE FROM system_settings WHERE key = 'files.signed_url_seconds'")


def downgrade() -> None:
    op.execute("INSERT INTO system_settings (key, value) VALUES ('files.signed_url_seconds', '60') "
               "ON CONFLICT (key) DO NOTHING")
    op.execute(EACH_TABLE.format("DISABLE"))
