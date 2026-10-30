"""Telemetry expressions shared by service jobs (no Spark dependency)."""


def vg(key: str, typ: str = "string") -> str:
    return f"variant_get(attributes, '$[\"{key}\"]', '{typ}')"


HTTP_STATUS = f"coalesce({vg('http.response.status_code', 'int')}, {vg('http.status_code', 'int')})"
HTTP_ROUTE = f"coalesce({vg('http.route')}, name)"
TRAFFIC_KIND = (
    f"coalesce({vg('traffic.kind')}, CASE WHEN name ILIKE '%healthz%' THEN 'probe' ELSE 'real' END)"
)
NOT_PROBE = f"{TRAFFIC_KIND} = 'real'"
SERVER = "kind ILIKE '%server%'"
DUR = "(end_time_unix_nano - start_time_unix_nano) / 1e6"
ERR = f"(coalesce({HTTP_STATUS} >= 400, false) OR coalesce(status.code, '') ILIKE '%error%')"
UHASH = vg("user.id_hash")
SESS = vg("session.id")
MODEL = f"nullif(replace({vg('gen_ai.request.model')}, '\"', ''), '')"
IN_TOK = f"coalesce({vg('gen_ai.usage.input_tokens', 'long')}, 0)"
OUT_TOK = f"coalesce({vg('gen_ai.usage.output_tokens', 'long')}, 0)"
BILLABLE = """(CASE WHEN app_has_markers THEN coalesce(billable, false)
               ELSE span_type IN ('LLM', 'CHAT_MODEL')
                 OR (span_type IS NULL AND NOT trace_has_llm) END)"""


def enriched_spans(fq: str, predicate: str) -> str:
    # MLflow JSON-encodes some attributes. Explicit false also opts an app into markers.
    return f"""
      WITH spans AS (
        SELECT *, {MODEL} AS model, {TRAFFIC_KIND} AS traffic_kind,
               {vg("monitor.llm.billable", "boolean")} AS billable,
               replace({vg("mlflow.spanType")}, '"', '') AS span_type
        FROM {fq}.otel_spans WHERE {predicate}
      ), marked AS (
        SELECT *, max(CASE WHEN billable IS NOT NULL THEN 1 ELSE 0 END)
                     OVER (PARTITION BY date, service_name) = 1 AS app_has_markers,
                  max(CASE WHEN span_type IN ('LLM', 'CHAT_MODEL') THEN 1 ELSE 0 END)
                     OVER (PARTITION BY date, service_name, trace_id) = 1 AS trace_has_llm
        FROM spans
      )"""
