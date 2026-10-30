"""Small, idempotent migrations for service-owned Delta tables."""


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
