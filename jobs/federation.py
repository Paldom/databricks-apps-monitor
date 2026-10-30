"""Direct UC feeder transport and hub views; raw telemetry stays local."""

import re


def identifier(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("Invalid catalog/schema identifier")
    return f"`{value}`"


def feeder_schema(workspace_name, workspace_id):
    if not str(workspace_id).isdigit():
        raise ValueError("workspace_id must be numeric")
    name = re.sub(r"[^a-z0-9_]", "_", workspace_name.lower())[:120].strip("_") or "workspace"
    return f"af_{name}__{workspace_id}"


def arguments(parser):
    parser.add_argument(
        "--deployment-mode", choices=("standalone", "feeder", "hub"), default="standalone"
    )
    parser.add_argument("--hub-catalog", default="")
    parser.add_argument("--workspace-name", default="")


def destination(args, client):
    if args.deployment_mode == "standalone":
        return None
    if not args.hub_catalog or args.hub_catalog == "unset":
        raise ValueError("hub_catalog is required for feeder/hub mode")
    catalog = identifier(args.hub_catalog)
    ws = str(client.get_workspace_id())
    name = args.workspace_name or client.config.host.removeprefix("https://").split(".")[0]
    return f"{catalog}.{identifier(feeder_schema(name, ws))}"


def publish(spark, args, client, tables):
    if args.deployment_mode != "feeder":
        return
    dest = destination(args, client)
    source = f"{identifier(args.catalog)}.{identifier(args.schema)}"
    ws = str(client.get_workspace_id())
    name = feeder_schema(
        args.workspace_name or client.config.host.removeprefix("https://").split(".")[0], ws
    ).rsplit("__", 1)[0][3:]
    spark.sql(
        f"CREATE SCHEMA IF NOT EXISTS {dest} COMMENT 'Apps Monitor feeder snapshots and retained aggregates'"
    )
    for table in tables:
        if table == "apps_inventory":
            # The current snapshot includes deletions; retries never duplicate history.
            query = f"SELECT *, '{name}' AS workspace_name FROM {source}.apps_inventory WHERE workspace_id = :ws AND snapshot_ts = :snapshot_ts"
            params = {"ws": ws, "snapshot_ts": args.snapshot_ts}
            targets = (
                ("apps_current", ("workspace_id", "name"), True),
                ("apps_history", ("workspace_id", "name", "snapshot_ts"), False),
            )
        else:
            projection = (
                "date, name, dbus, computed_at, workspace_id" if table == "costs_daily" else "*"
            )
            query = f"SELECT {projection}, '{name}' AS workspace_name FROM {source}.{table} WHERE workspace_id = :ws"
            params = {"ws": ws}
            keys = {
                "agg_app_daily": ("workspace_id", "date", "name", "traffic_kind"),
                "costs_daily": ("workspace_id", "date", "name"),
                "alert_events": ("workspace_id", "source", "rule", "app", "ts", "state"),
            }[table]
            targets = ((table, keys, False),)
        spark.sql(query, args=params).createOrReplaceTempView("reach_publish")
        for target, keys, current in targets:
            spark.sql(
                f"CREATE TABLE IF NOT EXISTS {dest}.{target} COMMENT 'Feeder {target}; workspace_id is part of every key' AS SELECT * FROM reach_publish WHERE false"
            )
            if current:
                spark.sql(f"INSERT OVERWRITE {dest}.{target} SELECT * FROM reach_publish")
            else:
                match = " AND ".join(f"t.{k} <=> s.{k}" for k in keys)
                delete = " WHEN NOT MATCHED BY SOURCE THEN DELETE" if table == "costs_daily" else ""
                spark.sql(
                    f"MERGE INTO {dest}.{target} t USING reach_publish s ON {match} WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *{delete}"
                )
        if table == "apps_inventory":
            spark.sql(
                f"CREATE OR REPLACE VIEW {dest}.apps_inventory COMMENT 'Latest feeder inventory; apps_history retains snapshots' AS SELECT * FROM {dest}.apps_current"
            )


def union_sql(catalog, schemas, table):
    cat = identifier(catalog)
    return " UNION ALL ".join(
        f"SELECT * FROM {cat}.{identifier(s)}.{identifier(table)}" for s in sorted(set(schemas))
    )


def hub_views(spark, args):
    if args.deployment_mode != "hub":
        return
    if not args.hub_catalog or args.hub_catalog == "unset":
        raise ValueError("hub_catalog is required for hub mode")
    cat = identifier(args.hub_catalog)
    fq = f"{identifier(args.catalog)}.{identifier(args.schema)}"
    rows = spark.sql(
        f"SELECT table_schema, table_name FROM {cat}.information_schema.tables WHERE table_schema LIKE 'af_%'"
    ).collect()
    available = {}
    for row in rows:
        schema = row["table_schema"]
        if re.fullmatch(r"af_[a-z0-9_]+__\d+", schema):
            available.setdefault(row["table_name"], []).append(schema)
    # Replace empty views too so removed feeders disappear from the fleet.
    empty = {
        "apps_current": "CAST(NULL AS STRING) workspace_id, CAST(NULL AS STRING) workspace_name, CAST(NULL AS STRING) name, CAST(NULL AS STRING) url, CAST(NULL AS STRING) app_state, CAST(NULL AS STRING) compute_state, CAST(NULL AS TIMESTAMP) snapshot_ts",
        "agg_app_daily": "CAST(NULL AS STRING) workspace_id, CAST(NULL AS STRING) workspace_name, CAST(NULL AS STRING) name, CAST(NULL AS STRING) traffic_kind, CAST(NULL AS DATE) date, CAST(NULL AS BIGINT) requests, CAST(NULL AS BIGINT) errors",
        "costs_daily": "CAST(NULL AS STRING) workspace_id, CAST(NULL AS STRING) workspace_name, CAST(NULL AS STRING) name, CAST(NULL AS DATE) date, CAST(NULL AS DOUBLE) dbus, CAST(NULL AS TIMESTAMP) computed_at",
        "alert_events": "CAST(NULL AS STRING) workspace_id, CAST(NULL AS STRING) source, CAST(NULL AS STRING) rule, CAST(NULL AS STRING) app, CAST(NULL AS STRING) state, CAST(NULL AS TIMESTAMP) ts",
    }
    for table, columns in empty.items():
        body = (
            union_sql(args.hub_catalog, available.get(table, []), table)
            or f"SELECT {columns} WHERE false"
        )
        view = "v_fleet_costs_unpriced" if table == "costs_daily" else f"v_fleet_{table}"
        spark.sql(
            f"CREATE OR REPLACE VIEW {fq}.{view} COMMENT 'Union of discovered feeder {table}; keyed by workspace_id' AS {body}"
        )
    spark.sql(f"""CREATE OR REPLACE VIEW {fq}.v_fleet_alerts_open
      COMMENT 'Latest firing event across feeders, partitioned by workspace/source/rule/app' AS
      SELECT * EXCEPT (rn) FROM (SELECT *, row_number() OVER (
        PARTITION BY workspace_id, source, rule, app ORDER BY ts DESC, state DESC) rn
        FROM {fq}.v_fleet_alert_events) WHERE rn = 1 AND state = 'firing'""")
    spark.sql(f"""CREATE OR REPLACE VIEW {fq}.v_fleet_costs_daily
      COMMENT 'Feeder DBUs with account billing priced once at the hub; never sum feeder USD' AS
      WITH priced AS (
        SELECT CAST(u.workspace_id AS STRING) workspace_id, u.usage_date AS date,
               u.usage_metadata.app_name AS name,
               sum(u.usage_quantity * coalesce(p.pricing.effective_list.default, p.pricing.default)) AS dbu_usd
        FROM system.billing.usage u LEFT JOIN system.billing.list_prices p
          ON u.sku_name = p.sku_name AND u.cloud = p.cloud AND p.currency_code = 'USD'
         AND u.usage_end_time >= p.price_start_time
         AND (p.price_end_time IS NULL OR u.usage_end_time < p.price_end_time)
        WHERE u.billing_origin_product = 'APPS' GROUP BY 1, 2, 3)
      SELECT c.*, p.dbu_usd FROM {fq}.v_fleet_costs_unpriced c LEFT JOIN priced p
        ON c.workspace_id = p.workspace_id AND c.date = p.date AND c.name = p.name""")
