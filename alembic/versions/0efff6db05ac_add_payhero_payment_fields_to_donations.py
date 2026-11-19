"""add payhero payment fields to donations

Revision ID: 0efff6db05ac
Revises: 
Create Date: 2026-11-19 12:52:20.648258

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0efff6db05ac'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safe migration: Only add the new PayHero columns to donations if missing
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('donations')] if 'donations' in inspector.get_table_names() else []

    # Create Enum type if not present
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymentstatus AS ENUM ('PENDING', 'QUEUED', 'SUCCESS', 'FAILED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    if 'payment_status' not in existing_columns:
        op.execute("ALTER TABLE donations ADD COLUMN IF NOT EXISTS payment_status paymentstatus DEFAULT 'PENDING';")
    if 'external_reference' not in existing_columns:
        op.execute("ALTER TABLE donations ADD COLUMN IF NOT EXISTS external_reference VARCHAR;")
        op.execute("CREATE INDEX IF NOT EXISTS ix_donations_external_reference ON donations (external_reference);")
    if 'payhero_reference' not in existing_columns:
        op.execute("ALTER TABLE donations ADD COLUMN IF NOT EXISTS payhero_reference VARCHAR;")
    if 'provider_reference' not in existing_columns:
        op.execute("ALTER TABLE donations ADD COLUMN IF NOT EXISTS provider_reference VARCHAR;")
    if 'payment_provider' not in existing_columns:
        op.execute("ALTER TABLE donations ADD COLUMN IF NOT EXISTS payment_provider VARCHAR DEFAULT 'm-pesa';")
    if 'transaction_date' not in existing_columns:
        op.execute("ALTER TABLE donations ADD COLUMN IF NOT EXISTS transaction_date TIMESTAMP WITH TIME ZONE;")
    if 'message' not in existing_columns:
        op.execute("ALTER TABLE donations ADD COLUMN IF NOT EXISTS message TEXT;")
    if 'updated_at' not in existing_columns:
        op.execute("ALTER TABLE donations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;")


def downgrade() -> None:
    pass
