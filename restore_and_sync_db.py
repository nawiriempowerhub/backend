"""
restore_and_sync_db.py
Safely restores all tables and synchronizes columns for Railway Postgres database.
Run this script from your terminal:
    python restore_and_sync_db.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, text, inspect
from app.database import engine, Base
import app.models as models

def main():
    print("=" * 60)
    print("Connecting to database...")
    print("=" * 60)

    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT current_database();"))
            db_name = res.scalar()
            print(f"[OK] Connected to database: {db_name}")
    except Exception as e:
        print(f"[ERROR] Could not connect to database: {e}")
        sys.exit(1)

    print("\nEnsuring all tables exist from models...")
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("[OK] Base.metadata.create_all completed.")
    except Exception as e:
        print(f"[WARNING] create_all had an issue: {e}")
        print("Continuing with individual table checks...")

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"\nCurrent tables in database: {existing_tables}")

    # Check and add any missing columns in the donations table
    if "donations" in existing_tables:
        existing_columns = [col["name"] for col in inspector.get_columns("donations")]
        print(f"\nExisting columns in 'donations': {existing_columns}")

        columns_to_add = [
            ("donor_phone", "VARCHAR"),
            ("message", "TEXT"),
            ("external_reference", "VARCHAR"),
            ("payhero_reference", "VARCHAR"),
            ("provider_reference", "VARCHAR"),
            ("payment_provider", "VARCHAR DEFAULT 'm-pesa'"),
            ("transaction_date", "TIMESTAMP WITH TIME ZONE"),
            ("updated_at", "TIMESTAMP WITH TIME ZONE"),
        ]

        with engine.begin() as conn:
            # Ensure paymentstatus enum exists
            try:
                conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE paymentstatus AS ENUM ('PENDING', 'QUEUED', 'SUCCESS', 'FAILED');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                print("[OK] Checked/Created enum 'paymentstatus'.")
            except Exception as ex:
                print(f"[INFO] Enum creation note: {ex}")

            # Check payment_status column
            if "payment_status" not in existing_columns:
                try:
                    conn.execute(text("ALTER TABLE donations ADD COLUMN payment_status paymentstatus DEFAULT 'PENDING';"))
                    print("[OK] Added column 'payment_status' to donations.")
                except Exception as ex:
                    print(f"[WARNING] Could not add payment_status: {ex}")

            for col_name, col_type in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE donations ADD COLUMN {col_name} {col_type};"))
                        print(f"[OK] Added column '{col_name}' to donations.")
                    except Exception as ex:
                        print(f"[WARNING] Could not add column '{col_name}': {ex}")

            # Also create index on external_reference if not exists
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_donations_external_reference ON donations (external_reference);"))
            except Exception:
                pass

    print("\n" + "=" * 60)
    print("Database sync finished successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
