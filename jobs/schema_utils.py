"""Small, idempotent migrations for service-owned Delta tables."""

COST_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.costs_daily (
  date DATE, name STRING,
  dbus DOUBLE, dbu_usd DOUBLE,
  ai_calls LONG, ai_input_tokens LONG, ai_output_tokens LONG, ai_usd DOUBLE,
  computed_at TIMESTAMP, workspace_id STRING, ai_tokens_gateway LONG, idle_usd DOUBLE
) COMMENT 'Per-app daily cost: exact app-compute DBUs/$ from billing + AI tokens from telemetry'"""


def ensure_columns(spark, table: str, columns: dict[str, str]) -> None:
    existing = set(spark.table(table).columns)
    missing = [f"{name} {typ}" for name, typ in columns.items() if name not in existing]
    if missing:
        spark.sql(f"ALTER TABLE {table} ADD COLUMNS ({', '.join(missing)})")


def workspace_column(spark, table: str, workspace_id: str) -> None:
    ensure_columns(spark, table, {"workspace_id": "STRING"})
    # Legacy rows belong to the workspace that owns this service schema.
    spark.sql(
        f"UPDATE {table} SET workspace_id = :ws WHERE workspace_id IS NULL",
        args={"ws": workspace_id},
    )


def ensure_costs_table(spark, fq: str, workspace_id: str) -> None:
    # Readers and writers can start independently on both fresh and upgraded installations.
    spark.sql(COST_DDL.format(fq=fq))
    table = f"{fq}.costs_daily"
    ensure_columns(
        spark, table, {"workspace_id": "STRING", "ai_tokens_gateway": "LONG", "idle_usd": "DOUBLE"}
    )
    workspace_column(spark, table, workspace_id)
