import dlt
import requests
import os
from datetime import date, datetime
from decimal import Decimal

# Flask mock server URL (uses Docker service name inside containers)
MOCK_SERVER_URL = os.getenv("MOCK_SERVER_URL", "http://mock-server:5000")

# PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/customer_db")

# Track total records fetched across all pages
_records_fetched = 0


def _convert_types(customers):
    """Convert string date/timestamp fields to proper Python types."""
    for c in customers:
        if c.get("date_of_birth"):
            c["date_of_birth"] = date.fromisoformat(c["date_of_birth"])
        if c.get("created_at"):
            c["created_at"] = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
        if c.get("account_balance") is not None:
            c["account_balance"] = Decimal(str(c["account_balance"]))
    return customers


@dlt.resource(
    name="customers",            # table name in PostgreSQL
    write_disposition="merge",   # upsert: insert new, update existing
    primary_key="customer_id",   # used to match existing records
    columns={
        "customer_id":     {"data_type": "text", "nullable": False},
        "first_name":      {"data_type": "text", "nullable": False},
        "last_name":       {"data_type": "text", "nullable": False},
        "email":           {"data_type": "text", "nullable": False},
        "phone":           {"data_type": "text", "nullable": True},
        "address":         {"data_type": "text", "nullable": True},
        "date_of_birth":   {"data_type": "date", "nullable": True},
        "account_balance": {"data_type": "decimal", "precision": 15, "scale": 2, "nullable": True},
        "created_at":      {"data_type": "timestamp", "nullable": True},
    }
)
def fetch_customers():
    """
    dlt resource: fetches all customers from Flask API page by page.
    dlt automatically loads each yielded batch into PostgreSQL.
    """
    global _records_fetched
    _records_fetched = 0

    page = 1
    limit = 10

    while True:
        print(f"Fetching page {page} from Flask...")

        response = requests.get(
            f"{MOCK_SERVER_URL}/api/customers",
            params={"page": page, "limit": limit}
        )
        response.raise_for_status()

        data = response.json()
        customers = _convert_types(data["data"])

        # No more records — stop
        if not customers:
            break

        _records_fetched += len(customers)

        # Yield batch — dlt handles the actual DB write
        yield customers

        # If fewer records than limit, this was the last page
        if len(customers) < limit:
            break

        page += 1

    print(f"Total records fetched: {_records_fetched}")


def _apply_schema_constraints():
    """
    Post-load: alter DLT-created columns to match the exact required schema.
    DLT uses unbounded 'character varying' — this adds VARCHAR lengths,
    changes address to TEXT, created_at to TIMESTAMP, and adds PRIMARY KEY.
    """
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()

    alter_statements = [
        "ALTER TABLE customers ALTER COLUMN customer_id TYPE VARCHAR(50)",
        "ALTER TABLE customers ALTER COLUMN first_name TYPE VARCHAR(100)",
        "ALTER TABLE customers ALTER COLUMN last_name TYPE VARCHAR(100)",
        "ALTER TABLE customers ALTER COLUMN email TYPE VARCHAR(255)",
        "ALTER TABLE customers ALTER COLUMN phone TYPE VARCHAR(20)",
        "ALTER TABLE customers ALTER COLUMN address TYPE TEXT",
        "ALTER TABLE customers ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'",
    ]

    # Add PRIMARY KEY if not already set
    cur.execute("""
        SELECT 1 FROM pg_constraint
        WHERE conname = 'customers_pkey' AND conrelid = 'customers'::regclass
    """)
    if not cur.fetchone():
        alter_statements.append(
            "ALTER TABLE customers ADD CONSTRAINT customers_pkey PRIMARY KEY (customer_id)"
        )

    for stmt in alter_statements:
        try:
            cur.execute(stmt)
            print(f"  ✓ {stmt}")
        except Exception as e:
            print(f"  ⚠ {stmt} — {e}")

    cur.close()
    conn.close()
    print("Schema constraints applied.")


def run_ingestion():
    """
    Runs the dlt pipeline:
      Flask API → dlt resource → PostgreSQL (merge/upsert)
    Then applies exact schema constraints (VARCHAR lengths, PRIMARY KEY).
    """
    global _records_fetched
    print("Starting dlt ingestion pipeline...")

    # Create the dlt pipeline pointing to our PostgreSQL instance
    pipeline = dlt.pipeline(
        pipeline_name="customer_pipeline",
        destination=dlt.destinations.postgres(credentials=DATABASE_URL),
        dataset_name="public"         # use the public PostgreSQL schema
    )

    # Run the pipeline — dlt fetches data and upserts into customers table
    load_info = pipeline.run(fetch_customers())

    print(f"dlt load complete: {load_info}")

    # Apply exact schema constraints after dlt creates the table
    _apply_schema_constraints()

    return _records_fetched
