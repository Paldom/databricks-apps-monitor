window.CONSOLE_FIXTURES = {
  "api/console/trace/0af7651916cd43dd8448eb211c80319c": {
    "trace_id": "0af7651916cd43dd8448eb211c80319c",
    "app": "claims-assistant",
    "root": "POST /api/chat",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "claims-assistant",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "claims-assistant",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "claims-assistant",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "claims-assistant",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "claims-assistant",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "doc-intake",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "doc-intake",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "claims-assistant",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/claims-assistant/logs": {
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0af7651916cd43dd8448eb211c80319c"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0af7651916cd43dd8448eb211c80319c"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0af7651916cd43dd8448eb211c80319c"
      }
    ]
  },
  "api/apps/claims-assistant/errors": {
    "groups": [
      {
        "fingerprint": "demo-0",
        "occurrences": 12,
        "first_seen": "2026-10-30T09:27:00Z",
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "Demo dependency timeout"
      }
    ],
    "failed_requests": [
      {
        "trace_id": "0af7651916cd43dd8448eb211c80319c",
        "name": "POST /api/chat",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ],
    "error_logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0af7651916cd43dd8448eb211c80319c"
      }
    ]
  },
  "api/apps/claims-assistant/traces": {
    "traces": [
      {
        "trace_id": "0af7651916cd43dd8448eb211c80319c",
        "name": "POST /api/chat",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/claims-assistant/agent-traces": {
    "experiment": "201",
    "traces": [
      {
        "trace_id": "tr-demo-0",
        "request_time": "2026-10-30T09:27:00Z",
        "duration_ms": 6420,
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested",
        "client_request_id": "demo-request",
        "tags": {
          "agent": "coverage"
        }
      }
    ]
  },
  "api/apps/claims-assistant/agent-traces/tr-demo-0": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-0",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "claims-assistant",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "claims-assistant",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "claims-assistant",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "claims-assistant",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "claims-assistant",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "doc-intake",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "doc-intake",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "claims-assistant",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0af7651916cd43dd8448eb211c80319c"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0af7651916cd43dd8448eb211c80319c"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0af7651916cd43dd8448eb211c80319c"
      }
    ]
  },
  "api/apps/claims-assistant/requests": {
    "timeline": [
      {
        "ts": "2026-10-29T10:00:00Z",
        "requests": 886,
        "errors": 25,
        "p50_ms": 540,
        "p95_ms": 1603.11
      },
      {
        "ts": "2026-10-29T11:00:00Z",
        "requests": 1063,
        "errors": 35,
        "p50_ms": 540,
        "p95_ms": 1673.71
      },
      {
        "ts": "2026-10-29T12:00:00Z",
        "requests": 1087,
        "errors": 42,
        "p50_ms": 540,
        "p95_ms": 1982.49
      },
      {
        "ts": "2026-10-29T13:00:00Z",
        "requests": 1108,
        "errors": 51,
        "p50_ms": 540,
        "p95_ms": 1822.12
      },
      {
        "ts": "2026-10-29T14:00:00Z",
        "requests": 988,
        "errors": 29,
        "p50_ms": 540,
        "p95_ms": 1729.5
      },
      {
        "ts": "2026-10-29T15:00:00Z",
        "requests": 999,
        "errors": 27,
        "p50_ms": 540,
        "p95_ms": 1566.58
      },
      {
        "ts": "2026-10-29T16:00:00Z",
        "requests": 796,
        "errors": 22,
        "p50_ms": 540,
        "p95_ms": 1604.08
      },
      {
        "ts": "2026-10-29T17:00:00Z",
        "requests": 717,
        "errors": 23,
        "p50_ms": 540,
        "p95_ms": 1155.08
      },
      {
        "ts": "2026-10-29T18:00:00Z",
        "requests": 695,
        "errors": 11,
        "p50_ms": 540,
        "p95_ms": 1099.75
      },
      {
        "ts": "2026-10-29T19:00:00Z",
        "requests": 592,
        "errors": 17,
        "p50_ms": 540,
        "p95_ms": 1122.57
      },
      {
        "ts": "2026-10-29T20:00:00Z",
        "requests": 671,
        "errors": 14,
        "p50_ms": 540,
        "p95_ms": 1115.95
      },
      {
        "ts": "2026-10-29T21:00:00Z",
        "requests": 773,
        "errors": 23,
        "p50_ms": 540,
        "p95_ms": 1292.62
      },
      {
        "ts": "2026-10-29T22:00:00Z",
        "requests": 887,
        "errors": 32,
        "p50_ms": 540,
        "p95_ms": 1540.04
      },
      {
        "ts": "2026-10-29T23:00:00Z",
        "requests": 995,
        "errors": 35,
        "p50_ms": 540,
        "p95_ms": 1526.64
      },
      {
        "ts": "2026-10-30T00:00:00Z",
        "requests": 1096,
        "errors": 48,
        "p50_ms": 540,
        "p95_ms": 1828.26
      },
      {
        "ts": "2026-10-30T01:00:00Z",
        "requests": 1024,
        "errors": 49,
        "p50_ms": 540,
        "p95_ms": 1748.43
      },
      {
        "ts": "2026-10-30T02:00:00Z",
        "requests": 1077,
        "errors": 38,
        "p50_ms": 540,
        "p95_ms": 1764.59
      },
      {
        "ts": "2026-10-30T03:00:00Z",
        "requests": 930,
        "errors": 42,
        "p50_ms": 540,
        "p95_ms": 1848.99
      },
      {
        "ts": "2026-10-30T04:00:00Z",
        "requests": 805,
        "errors": 23,
        "p50_ms": 540,
        "p95_ms": 1469.85
      },
      {
        "ts": "2026-10-30T05:00:00Z",
        "requests": 803,
        "errors": 24,
        "p50_ms": 540,
        "p95_ms": 1484.96
      },
      {
        "ts": "2026-10-30T06:00:00Z",
        "requests": 697,
        "errors": 17,
        "p50_ms": 540,
        "p95_ms": 1016.31
      },
      {
        "ts": "2026-10-30T07:00:00Z",
        "requests": 677,
        "errors": 12,
        "p50_ms": 540,
        "p95_ms": 1146.17
      },
      {
        "ts": "2026-10-30T08:00:00Z",
        "requests": 685,
        "errors": 60,
        "p50_ms": 540,
        "p95_ms": 2594.77
      },
      {
        "ts": "2026-10-30T09:00:00Z",
        "requests": 771,
        "errors": 128,
        "p50_ms": 540,
        "p95_ms": 4054.72
      }
    ],
    "routes": [
      {
        "route": "/api/report",
        "requests": 100,
        "errors": 3,
        "avg_ms": 310,
        "p50_ms": 200,
        "p95_ms": 900
      }
    ]
  },
  "api/apps/claims-assistant/deps": {
    "deps": [
      {
        "dependency": "databricks_sql/wh-7d1a",
        "calls": 1200,
        "avg_ms": 150,
        "p95_ms": 560,
        "errors": 0
      },
      {
        "dependency": "https://doc-intake-1008.aws.databricksapps.com/api/policies",
        "calls": 420,
        "avg_ms": 600,
        "p95_ms": 2900,
        "errors": 4
      },
      {
        "dependency": "https://workspace.invalid/serving-endpoints/claims-model/invocations",
        "calls": 800,
        "avg_ms": 1100,
        "p95_ms": 2300,
        "errors": 15
      },
      {
        "dependency": "api.example.invalid",
        "calls": 70,
        "avg_ms": 100,
        "p95_ms": 180,
        "errors": 0
      }
    ]
  },
  "api/apps/claims-assistant/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/claims-assistant/security": {
    "scan": {
      "name": "claims-assistant",
      "quality_score": 85,
      "findings_critical": 0,
      "findings_high": 0,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 14,
      "py_loc": 1200,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-0",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": []}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/claims-assistant/review": {
    "review": {
      "name": "claims-assistant",
      "verdict": "approve",
      "score_overall": 8.0,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo agent for Claims.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/claims-assistant/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 49.25,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 51.55,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 58.64,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 60.64,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 60.42,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 62.27,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 60.42,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 57.51,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 55.26,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 47.63,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 41.3,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 38.45,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 37.97,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 41.91,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 52.04,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 51.87,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 66.25,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 65.25,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 69.84,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 69.74,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 72.29,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 69.48,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 61.47,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 53.78,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 55.67,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 52.71,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 48.19,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 50.07,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 50.94,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 60.77,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      }
    ],
    "forecast": {
      "forecast_30d_usd": 2290.0,
      "days_observed": 30
    },
    "budget": 2000,
    "mtd_usd": 312.87
  },
  "api/apps/claims-assistant/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "claims-assistant",
        "dbu_usd": 312.87,
        "ai_usd": 1612.9,
        "total_usd": 1830.4,
        "idle_usd": 59.22,
        "usd_per_1k_requests": 2.347,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/claims-assistant/genai": {
    "daily": [
      {
        "date": "2026-10-01",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-02",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-03",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-04",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-05",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-06",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-07",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-08",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-09",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-10",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-11",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-12",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-13",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-14",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-15",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-16",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-17",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-18",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-19",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-20",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-21",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-22",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-23",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-24",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-25",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-26",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-27",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-28",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-29",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-30",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      }
    ],
    "top": [
      {
        "session_id": "hashed-session",
        "user_hash": "hashed-user",
        "calls": 10,
        "tokens": 4000,
        "last_call": "2026-10-30T09:27:00Z"
      }
    ],
    "error_taxonomy": [
      {
        "category": "rate_limit",
        "errors": 3,
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "429 upstream"
      }
    ],
    "agent_steps": [
      {
        "date": "2026-10-29",
        "avg_steps": 5,
        "max_steps": 8,
        "agent_runs": 32
      },
      {
        "date": "2026-10-30",
        "avg_steps": 7,
        "max_steps": 12,
        "agent_runs": 40
      }
    ],
    "quality": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "relevance": 8,
        "faithfulness": 7,
        "toxicity": 0,
        "traces_sampled": 10,
        "comment": "Demo sampled evaluation"
      }
    ],
    "feedback": [
      {
        "date": "2026-10-30",
        "n": 10,
        "avg_rating": 4.2,
        "negative": 1
      }
    ],
    "feedback_recent": []
  },
  "api/apps/claims-assistant/drift": {
    "reports": [
      {
        "week": "2026-10-26",
        "samples": 60,
        "k": 3,
        "silhouette": 0.6,
        "novel_share": 0.31
      }
    ]
  },
  "api/apps/claims-assistant/analytics": {
    "daily": [
      {
        "date": "2026-10-24",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-25",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-26",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-27",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-28",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-29",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-30",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      }
    ],
    "users": [
      {
        "user_hash": "u_demo_91a",
        "first_seen": "2026-10-01",
        "last_seen": "2026-10-30T09:27:00Z",
        "requests": 80,
        "sessions": 10,
        "active_days": 7,
        "errors": 1,
        "tokens": 4000
      }
    ],
    "mtd_usd": 312.87
  },
  "api/apps/claims-assistant/events": {
    "events": [
      {
        "event_name": "answer_shown",
        "app_version": "2.1.1",
        "events": 40,
        "sessions": 32,
        "last_seen": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/claims-assistant/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": [
      {
        "funnel": "answer",
        "app_version": "2.1.1",
        "step_name": "ask_question",
        "sessions": 100,
        "dropoff_pct": 0
      },
      {
        "funnel": "answer",
        "app_version": "2.1.1",
        "step_name": "answer_shown",
        "sessions": 80,
        "dropoff_pct": 20
      }
    ]
  },
  "api/apps/claims-assistant/cohorts": {
    "cohorts": [
      {
        "cohort_week": "2026-10-19",
        "week_number": 1,
        "cohort_size": 40,
        "retained_users": 30,
        "retention_pct": 75,
        "partial_week": true
      }
    ]
  },
  "api/apps/claims-assistant/rum": {
    "routes": [
      {
        "date": "2026-10-30",
        "route": "/",
        "page_views": 200,
        "p75_lcp": 650,
        "p75_cls": 0.02,
        "p75_inp": 80,
        "js_errors": 1,
        "fingerprint": "rum-demo",
        "trace_id": "0af7651916cd43dd8448eb211c80319c"
      }
    ]
  },
  "api/apps/claims-assistant/guardrails": {
    "findings": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "kind": "pii",
        "severity": "warning",
        "excerpt_masked": "[EMAIL]",
        "excerpt_hash": "demo-hash",
        "trace_id": "tr-demo-0"
      }
    ],
    "templates": [
      {
        "date": "2026-10-30",
        "template_hash": "template-demo",
        "samples": 12,
        "daily_samples": 40,
        "share": 0.3
      }
    ]
  },
  "api/apps/claims-assistant/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/claims-assistant/telemetry-health": {
    "health": {
      "quality": "healthy",
      "envelope_coverage": 0.9,
      "orphan_ratio_24h": 0.01,
      "sampler_ratio": 1,
      "last_span_at": "2026-10-30T09:27:00Z",
      "last_log_at": "2026-10-30T09:27:00Z",
      "last_metric_at": "2026-10-30T09:27:00Z",
      "semconv_legacy_only": 0,
      "semconv_stable_only": 0.1,
      "semconv_both": 0.9,
      "gateway_vs_otel_tokens": 12,
      "token_date": "2026-10-29"
    }
  },
  "api/apps/claims-assistant/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": -245.0,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": [
      {
        "slo": "availability",
        "date": "2026-10-10",
        "budget_remaining_pct": 100
      },
      {
        "slo": "availability",
        "date": "2026-10-11",
        "budget_remaining_pct": 80
      },
      {
        "slo": "availability",
        "date": "2026-10-12",
        "budget_remaining_pct": 60
      },
      {
        "slo": "availability",
        "date": "2026-10-13",
        "budget_remaining_pct": 40
      },
      {
        "slo": "availability",
        "date": "2026-10-14",
        "budget_remaining_pct": 20
      },
      {
        "slo": "availability",
        "date": "2026-10-15",
        "budget_remaining_pct": 0
      },
      {
        "slo": "availability",
        "date": "2026-10-16",
        "budget_remaining_pct": -20
      }
    ]
  },
  "api/apps/claims-assistant": {
    "uptime_24h": 99.655,
    "p95_ms": 180,
    "error_rate_1h": 0,
    "checks_24h": 1440,
    "compute_state": "ACTIVE",
    "last": {
      "code": 200,
      "ms": 120
    },
    "ttfb_ms": 110,
    "series": [
      [
        1793350800,
        true,
        200,
        120
      ],
      [
        1793350860,
        true,
        200,
        132
      ],
      [
        1793350920,
        true,
        200,
        144
      ],
      [
        1793350980,
        false,
        502,
        156
      ],
      [
        1793351040,
        true,
        200,
        168
      ],
      [
        1793351100,
        true,
        200,
        180
      ],
      [
        1793351160,
        true,
        200,
        192
      ],
      [
        1793351220,
        true,
        200,
        204
      ]
    ]
  },
  "api/apps/claims-assistant/synthetics": {
    "interval_s": 1800,
    "live": {
      "journey": "Report flow",
      "ok": true,
      "budget_ms": 2500,
      "within_budget": true,
      "ts": 1793352420,
      "steps": [
        {
          "name": "GET /api/report",
          "ok": true,
          "code": 200,
          "ms": 200,
          "detail": "Demo assertion"
        }
      ]
    },
    "browser": [
      {
        "run_ts": "2026-10-30T09:27:00Z",
        "journey": "browser-smoke",
        "ok": true,
        "status_code": 200,
        "latency_ms": 800,
        "detail": "Demo browser result",
        "vantage": "external",
        "failure_stage": null,
        "artifact": "/Volumes/demo/monitor/ui_tests/claims-assistant/run"
      }
    ]
  },
  "api/apps/claims-assistant/ops": {
    "config": {
      "tags_json": "{\"team\": \"Claims\", \"cost_center\": \"CC-410\", \"env\": \"prod\", \"tier\": \"t1\"}",
      "budget_usd_month": 2000,
      "auto_stop": "none",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "warehouse",
        "sql_warehouse": {
          "id": "wh-7d1a",
          "permission": "CAN_USE"
        }
      },
      {
        "name": "model",
        "serving_endpoint": {
          "name": "claims-model",
          "permission": "CAN_QUERY"
        }
      },
      {
        "name": "refresh",
        "job": {
          "id": "101",
          "permission": "CAN_MANAGE_RUN"
        }
      },
      {
        "name": "traces",
        "experiment": {
          "experiment_id": "201",
          "permission": "CAN_EDIT"
        }
      },
      {
        "name": "risk-store",
        "database": {
          "instance_name": "risk-db",
          "permission": "CAN_CONNECT_AND_CREATE"
        }
      },
      {
        "name": "claims-store",
        "postgres": {
          "database": "claims-db",
          "branch": "production"
        }
      },
      {
        "name": "documents",
        "uc_securable": {
          "securable_full_name": "demo.claims.documents",
          "securable_type": "TABLE"
        }
      },
      {
        "name": "credentials",
        "secret": {
          "scope": "app-secrets",
          "key": "api-key"
        }
      },
      {
        "name": "analytics",
        "genie_space": {
          "id": "genie-demo"
        }
      },
      {
        "name": "intake",
        "app": {
          "name": "doc-intake",
          "url": "https://doc-intake-1008.aws.databricksapps.com",
          "permission": "CAN_USE"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 320
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/console/trace/00000000000000000000000000000065": {
    "trace_id": "00000000000000000000000000000065",
    "app": "pricing-api",
    "root": "GET /api/report",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "pricing-api",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "pricing-api",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "pricing-api",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "pricing-api",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "pricing-api",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "pricing-api",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "pricing-api",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "pricing-api",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/pricing-api/logs": {
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "00000000000000000000000000000065"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "00000000000000000000000000000065"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000065"
      }
    ]
  },
  "api/apps/pricing-api/errors": {
    "groups": [
      {
        "fingerprint": "demo-1",
        "occurrences": 13,
        "first_seen": "2026-10-30T09:27:00Z",
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "Demo dependency timeout"
      }
    ],
    "failed_requests": [
      {
        "trace_id": "00000000000000000000000000000065",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ],
    "error_logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000065"
      }
    ]
  },
  "api/apps/pricing-api/traces": {
    "traces": [
      {
        "trace_id": "00000000000000000000000000000065",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/pricing-api/agent-traces": {
    "experiment": null,
    "traces": []
  },
  "api/apps/pricing-api/agent-traces/tr-demo-1": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-1",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "pricing-api",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "pricing-api",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "pricing-api",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "pricing-api",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "pricing-api",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "pricing-api",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "pricing-api",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "pricing-api",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "00000000000000000000000000000065"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "00000000000000000000000000000065"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000065"
      }
    ]
  },
  "api/apps/pricing-api/requests": {
    "timeline": [
      {
        "ts": "2026-10-29T10:00:00Z",
        "requests": 805,
        "errors": 3,
        "p50_ms": 117,
        "p95_ms": 240.49
      },
      {
        "ts": "2026-10-29T11:00:00Z",
        "requests": 1040,
        "errors": 3,
        "p50_ms": 117,
        "p95_ms": 292.03
      },
      {
        "ts": "2026-10-29T12:00:00Z",
        "requests": 1017,
        "errors": 4,
        "p50_ms": 117,
        "p95_ms": 331.31
      },
      {
        "ts": "2026-10-29T13:00:00Z",
        "requests": 1102,
        "errors": 5,
        "p50_ms": 117,
        "p95_ms": 356.82
      },
      {
        "ts": "2026-10-29T14:00:00Z",
        "requests": 1112,
        "errors": 4,
        "p50_ms": 117,
        "p95_ms": 335.15
      },
      {
        "ts": "2026-10-29T15:00:00Z",
        "requests": 1007,
        "errors": 5,
        "p50_ms": 117,
        "p95_ms": 290.7
      },
      {
        "ts": "2026-10-29T16:00:00Z",
        "requests": 821,
        "errors": 3,
        "p50_ms": 117,
        "p95_ms": 240.09
      },
      {
        "ts": "2026-10-29T17:00:00Z",
        "requests": 773,
        "errors": 3,
        "p50_ms": 117,
        "p95_ms": 234.33
      },
      {
        "ts": "2026-10-29T18:00:00Z",
        "requests": 600,
        "errors": 1,
        "p50_ms": 117,
        "p95_ms": 193.59
      },
      {
        "ts": "2026-10-29T19:00:00Z",
        "requests": 701,
        "errors": 3,
        "p50_ms": 117,
        "p95_ms": 215.06
      },
      {
        "ts": "2026-10-29T20:00:00Z",
        "requests": 673,
        "errors": 2,
        "p50_ms": 117,
        "p95_ms": 218.21
      },
      {
        "ts": "2026-10-29T21:00:00Z",
        "requests": 818,
        "errors": 2,
        "p50_ms": 117,
        "p95_ms": 217.72
      },
      {
        "ts": "2026-10-29T22:00:00Z",
        "requests": 831,
        "errors": 3,
        "p50_ms": 117,
        "p95_ms": 290.84
      },
      {
        "ts": "2026-10-29T23:00:00Z",
        "requests": 915,
        "errors": 3,
        "p50_ms": 117,
        "p95_ms": 265.23
      },
      {
        "ts": "2026-10-30T00:00:00Z",
        "requests": 1048,
        "errors": 4,
        "p50_ms": 117,
        "p95_ms": 290.43
      },
      {
        "ts": "2026-10-30T01:00:00Z",
        "requests": 1070,
        "errors": 6,
        "p50_ms": 117,
        "p95_ms": 323.06
      },
      {
        "ts": "2026-10-30T02:00:00Z",
        "requests": 1064,
        "errors": 3,
        "p50_ms": 117,
        "p95_ms": 305.74
      },
      {
        "ts": "2026-10-30T03:00:00Z",
        "requests": 982,
        "errors": 4,
        "p50_ms": 117,
        "p95_ms": 291.37
      },
      {
        "ts": "2026-10-30T04:00:00Z",
        "requests": 905,
        "errors": 3,
        "p50_ms": 117,
        "p95_ms": 291.54
      },
      {
        "ts": "2026-10-30T05:00:00Z",
        "requests": 793,
        "errors": 3,
        "p50_ms": 117,
        "p95_ms": 234.67
      },
      {
        "ts": "2026-10-30T06:00:00Z",
        "requests": 618,
        "errors": 2,
        "p50_ms": 117,
        "p95_ms": 171.33
      },
      {
        "ts": "2026-10-30T07:00:00Z",
        "requests": 597,
        "errors": 2,
        "p50_ms": 117,
        "p95_ms": 221.6
      },
      {
        "ts": "2026-10-30T08:00:00Z",
        "requests": 653,
        "errors": 2,
        "p50_ms": 117,
        "p95_ms": 193.57
      },
      {
        "ts": "2026-10-30T09:00:00Z",
        "requests": 800,
        "errors": 3,
        "p50_ms": 117,
        "p95_ms": 236.8
      }
    ],
    "routes": [
      {
        "route": "/api/report",
        "requests": 100,
        "errors": 3,
        "avg_ms": 310,
        "p50_ms": 200,
        "p95_ms": 900
      }
    ]
  },
  "api/apps/pricing-api/deps": {
    "deps": [
      {
        "dependency": "databricks_sql/wh-7d1a",
        "calls": 1220,
        "avg_ms": 150,
        "p95_ms": 560,
        "errors": 1
      }
    ]
  },
  "api/apps/pricing-api/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/pricing-api/security": {
    "scan": {
      "name": "pricing-api",
      "quality_score": 67,
      "findings_critical": 0,
      "findings_high": 0,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 15,
      "py_loc": 1300,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-1",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": []}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/pricing-api/review": {
    "review": {
      "name": "pricing-api",
      "verdict": "approve",
      "score_overall": 8.3,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo api for Pricing.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/pricing-api/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 17.75,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 22.79,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 24.16,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 22.73,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 25.48,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 22.46,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 24.42,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 19.45,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 20.07,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 14.89,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 14.25,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 14.75,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 15.99,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 15.29,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 17.8,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 20.94,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 19.9,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 24.21,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 25.85,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 25.14,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 25.11,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 22.57,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 21.93,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 20.09,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 15.29,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 14.01,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 14.79,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 16.42,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 17.06,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 18.05,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      }
    ],
    "forecast": {
      "forecast_30d_usd": 677.98,
      "days_observed": 30
    },
    "budget": 900,
    "mtd_usd": 529.93
  },
  "api/apps/pricing-api/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "pricing-api",
        "dbu_usd": 529.93,
        "ai_usd": 58.78,
        "total_usd": 588.71,
        "idle_usd": 55.41,
        "usd_per_1k_requests": 0.956,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/pricing-api/genai": {
    "daily": [],
    "top": [],
    "error_taxonomy": [],
    "agent_steps": [],
    "quality": [],
    "feedback": [],
    "feedback_recent": []
  },
  "api/apps/pricing-api/drift": {
    "reports": []
  },
  "api/apps/pricing-api/analytics": {
    "daily": [
      {
        "date": "2026-10-24",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-25",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-26",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-27",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-28",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-29",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-30",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      }
    ],
    "users": [
      {
        "user_hash": "u_demo_91a",
        "first_seen": "2026-10-01",
        "last_seen": "2026-10-30T09:27:00Z",
        "requests": 80,
        "sessions": 10,
        "active_days": 7,
        "errors": 1,
        "tokens": 4000
      }
    ],
    "mtd_usd": 529.93
  },
  "api/apps/pricing-api/events": {
    "events": [
      {
        "event_name": "answer_shown",
        "app_version": "3.2.2",
        "events": 40,
        "sessions": 32,
        "last_seen": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/pricing-api/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": [
      {
        "funnel": "answer",
        "app_version": "3.2.2",
        "step_name": "ask_question",
        "sessions": 100,
        "dropoff_pct": 0
      },
      {
        "funnel": "answer",
        "app_version": "3.2.2",
        "step_name": "answer_shown",
        "sessions": 80,
        "dropoff_pct": 20
      }
    ]
  },
  "api/apps/pricing-api/cohorts": {
    "cohorts": [
      {
        "cohort_week": "2026-10-19",
        "week_number": 1,
        "cohort_size": 40,
        "retained_users": 30,
        "retention_pct": 75,
        "partial_week": true
      }
    ]
  },
  "api/apps/pricing-api/rum": {
    "routes": [
      {
        "date": "2026-10-30",
        "route": "/",
        "page_views": 200,
        "p75_lcp": 650,
        "p75_cls": 0.02,
        "p75_inp": 80,
        "js_errors": 1,
        "fingerprint": "rum-demo",
        "trace_id": "00000000000000000000000000000065"
      }
    ]
  },
  "api/apps/pricing-api/guardrails": {
    "findings": [],
    "templates": []
  },
  "api/apps/pricing-api/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/pricing-api/telemetry-health": {
    "health": {
      "quality": "healthy",
      "envelope_coverage": 0.9,
      "orphan_ratio_24h": 0.01,
      "sampler_ratio": 1,
      "last_span_at": "2026-10-30T09:27:00Z",
      "last_log_at": "2026-10-30T09:27:00Z",
      "last_metric_at": "2026-10-30T09:27:00Z",
      "semconv_legacy_only": 0,
      "semconv_stable_only": 0.1,
      "semconv_both": 0.9,
      "gateway_vs_otel_tokens": 12,
      "token_date": "2026-10-29"
    }
  },
  "api/apps/pricing-api/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": 74.0,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": [
      {
        "slo": "availability",
        "date": "2026-10-10",
        "budget_remaining_pct": 100
      },
      {
        "slo": "availability",
        "date": "2026-10-11",
        "budget_remaining_pct": 80
      },
      {
        "slo": "availability",
        "date": "2026-10-12",
        "budget_remaining_pct": 60
      },
      {
        "slo": "availability",
        "date": "2026-10-13",
        "budget_remaining_pct": 40
      },
      {
        "slo": "availability",
        "date": "2026-10-14",
        "budget_remaining_pct": 20
      },
      {
        "slo": "availability",
        "date": "2026-10-15",
        "budget_remaining_pct": 0
      },
      {
        "slo": "availability",
        "date": "2026-10-16",
        "budget_remaining_pct": -20
      }
    ]
  },
  "api/apps/pricing-api": {
    "uptime_24h": 99.974,
    "p95_ms": 189,
    "error_rate_1h": 0,
    "checks_24h": 1440,
    "compute_state": "ACTIVE",
    "last": {
      "code": 200,
      "ms": 120
    },
    "ttfb_ms": 110,
    "series": [
      [
        1793350800,
        true,
        200,
        120
      ],
      [
        1793350860,
        true,
        200,
        132
      ],
      [
        1793350920,
        true,
        200,
        144
      ],
      [
        1793350980,
        false,
        502,
        156
      ],
      [
        1793351040,
        true,
        200,
        168
      ],
      [
        1793351100,
        true,
        200,
        180
      ],
      [
        1793351160,
        true,
        200,
        192
      ],
      [
        1793351220,
        true,
        200,
        204
      ]
    ]
  },
  "api/apps/pricing-api/synthetics": {
    "interval_s": 1800,
    "live": {
      "journey": "Report flow",
      "ok": true,
      "budget_ms": 2500,
      "within_budget": true,
      "ts": 1793352420,
      "steps": [
        {
          "name": "GET /api/report",
          "ok": true,
          "code": 200,
          "ms": 200,
          "detail": "Demo assertion"
        }
      ]
    },
    "browser": [
      {
        "run_ts": "2026-10-30T09:27:00Z",
        "journey": "browser-smoke",
        "ok": true,
        "status_code": 200,
        "latency_ms": 800,
        "detail": "Demo browser result",
        "vantage": "external",
        "failure_stage": null,
        "artifact": "/Volumes/demo/monitor/ui_tests/pricing-api/run"
      }
    ]
  },
  "api/apps/pricing-api/ops": {
    "config": {
      "tags_json": "{\"team\": \"Pricing\", \"cost_center\": \"CC-220\", \"env\": \"prod\", \"tier\": \"t1\"}",
      "budget_usd_month": 900,
      "auto_stop": "night",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "model",
        "serving_endpoint": {
          "name": "claims-model",
          "permission": "CAN_QUERY"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 320
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/console/trace/00000000000000000000000000000066": {
    "trace_id": "00000000000000000000000000000066",
    "app": "sales-cockpit",
    "root": "GET /api/report",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "sales-cockpit",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "sales-cockpit",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "sales-cockpit",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "sales-cockpit",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "sales-cockpit",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "sales-cockpit",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "sales-cockpit",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "sales-cockpit",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/sales-cockpit/logs": {
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "00000000000000000000000000000066"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "00000000000000000000000000000066"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000066"
      }
    ]
  },
  "api/apps/sales-cockpit/errors": {
    "groups": [
      {
        "fingerprint": "demo-2",
        "occurrences": 14,
        "first_seen": "2026-10-30T09:27:00Z",
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "Demo dependency timeout"
      }
    ],
    "failed_requests": [
      {
        "trace_id": "00000000000000000000000000000066",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ],
    "error_logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000066"
      }
    ]
  },
  "api/apps/sales-cockpit/traces": {
    "traces": [
      {
        "trace_id": "00000000000000000000000000000066",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/sales-cockpit/agent-traces": {
    "experiment": null,
    "traces": []
  },
  "api/apps/sales-cockpit/agent-traces/tr-demo-2": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-2",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "sales-cockpit",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "sales-cockpit",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "sales-cockpit",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "sales-cockpit",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "sales-cockpit",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "sales-cockpit",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "sales-cockpit",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "sales-cockpit",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "00000000000000000000000000000066"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "00000000000000000000000000000066"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000066"
      }
    ]
  },
  "api/apps/sales-cockpit/requests": {
    "timeline": [
      {
        "ts": "2026-10-29T10:00:00Z",
        "requests": 1650,
        "errors": 5,
        "p50_ms": 110,
        "p95_ms": 304.96
      },
      {
        "ts": "2026-10-29T11:00:00Z",
        "requests": 1721,
        "errors": 3,
        "p50_ms": 110,
        "p95_ms": 321.35
      },
      {
        "ts": "2026-10-29T12:00:00Z",
        "requests": 1894,
        "errors": 6,
        "p50_ms": 110,
        "p95_ms": 339.97
      },
      {
        "ts": "2026-10-29T13:00:00Z",
        "requests": 2022,
        "errors": 5,
        "p50_ms": 110,
        "p95_ms": 341.3
      },
      {
        "ts": "2026-10-29T14:00:00Z",
        "requests": 2065,
        "errors": 7,
        "p50_ms": 110,
        "p95_ms": 355.76
      },
      {
        "ts": "2026-10-29T15:00:00Z",
        "requests": 1820,
        "errors": 3,
        "p50_ms": 110,
        "p95_ms": 349.36
      },
      {
        "ts": "2026-10-29T16:00:00Z",
        "requests": 1534,
        "errors": 3,
        "p50_ms": 110,
        "p95_ms": 264.53
      },
      {
        "ts": "2026-10-29T17:00:00Z",
        "requests": 1421,
        "errors": 4,
        "p50_ms": 110,
        "p95_ms": 285.93
      },
      {
        "ts": "2026-10-29T18:00:00Z",
        "requests": 1388,
        "errors": 2,
        "p50_ms": 110,
        "p95_ms": 205.84
      },
      {
        "ts": "2026-10-29T19:00:00Z",
        "requests": 1350,
        "errors": 3,
        "p50_ms": 110,
        "p95_ms": 233.15
      },
      {
        "ts": "2026-10-29T20:00:00Z",
        "requests": 1403,
        "errors": 3,
        "p50_ms": 110,
        "p95_ms": 210.33
      },
      {
        "ts": "2026-10-29T21:00:00Z",
        "requests": 1541,
        "errors": 4,
        "p50_ms": 110,
        "p95_ms": 272.79
      },
      {
        "ts": "2026-10-29T22:00:00Z",
        "requests": 1520,
        "errors": 4,
        "p50_ms": 110,
        "p95_ms": 330.76
      },
      {
        "ts": "2026-10-29T23:00:00Z",
        "requests": 1801,
        "errors": 6,
        "p50_ms": 110,
        "p95_ms": 324.12
      },
      {
        "ts": "2026-10-30T00:00:00Z",
        "requests": 1939,
        "errors": 5,
        "p50_ms": 110,
        "p95_ms": 352.35
      },
      {
        "ts": "2026-10-30T01:00:00Z",
        "requests": 1985,
        "errors": 6,
        "p50_ms": 110,
        "p95_ms": 357.45
      },
      {
        "ts": "2026-10-30T02:00:00Z",
        "requests": 1906,
        "errors": 5,
        "p50_ms": 110,
        "p95_ms": 328.12
      },
      {
        "ts": "2026-10-30T03:00:00Z",
        "requests": 1873,
        "errors": 5,
        "p50_ms": 110,
        "p95_ms": 321.33
      },
      {
        "ts": "2026-10-30T04:00:00Z",
        "requests": 1593,
        "errors": 3,
        "p50_ms": 110,
        "p95_ms": 282.48
      },
      {
        "ts": "2026-10-30T05:00:00Z",
        "requests": 1321,
        "errors": 2,
        "p50_ms": 110,
        "p95_ms": 254.56
      },
      {
        "ts": "2026-10-30T06:00:00Z",
        "requests": 1202,
        "errors": 3,
        "p50_ms": 110,
        "p95_ms": 245.61
      },
      {
        "ts": "2026-10-30T07:00:00Z",
        "requests": 1090,
        "errors": 1,
        "p50_ms": 110,
        "p95_ms": 212.29
      },
      {
        "ts": "2026-10-30T08:00:00Z",
        "requests": 1356,
        "errors": 3,
        "p50_ms": 110,
        "p95_ms": 231.94
      },
      {
        "ts": "2026-10-30T09:00:00Z",
        "requests": 1556,
        "errors": 2,
        "p50_ms": 110,
        "p95_ms": 242.55
      }
    ],
    "routes": [
      {
        "route": "/api/report",
        "requests": 100,
        "errors": 3,
        "avg_ms": 310,
        "p50_ms": 200,
        "p95_ms": 900
      }
    ]
  },
  "api/apps/sales-cockpit/deps": {
    "deps": [
      {
        "dependency": "databricks_sql/wh-7d1a",
        "calls": 1240,
        "avg_ms": 150,
        "p95_ms": 560,
        "errors": 2
      }
    ]
  },
  "api/apps/sales-cockpit/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/sales-cockpit/security": {
    "scan": {
      "name": "sales-cockpit",
      "quality_score": 87,
      "findings_critical": 0,
      "findings_high": 0,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 16,
      "py_loc": 1400,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-2",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": []}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/sales-cockpit/review": {
    "review": {
      "name": "sales-cockpit",
      "verdict": "approve",
      "score_overall": 8.9,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo web for Sales Ops.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/sales-cockpit/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 12.63,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 14.9,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 14.99,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 15.79,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 15.56,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 14.84,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 16.52,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 13.74,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 13.68,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 11.64,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 9.18,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 10.52,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 11.27,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 12.04,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 11.28,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 12.42,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 15.76,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 16.07,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 16.5,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 15.78,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 15.99,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 15.67,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 13.34,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 13.38,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 12.63,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 9.16,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 8.69,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 10.13,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 12.07,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 11.95,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      }
    ],
    "forecast": {
      "forecast_30d_usd": 401.55,
      "days_observed": 30
    },
    "budget": 600,
    "mtd_usd": 397.92
  },
  "api/apps/sales-cockpit/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "sales-cockpit",
        "dbu_usd": 397.92,
        "ai_usd": 0,
        "total_usd": 397.92,
        "idle_usd": 22.24,
        "usd_per_1k_requests": 0.342,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/sales-cockpit/genai": {
    "daily": [],
    "top": [],
    "error_taxonomy": [],
    "agent_steps": [],
    "quality": [],
    "feedback": [],
    "feedback_recent": []
  },
  "api/apps/sales-cockpit/drift": {
    "reports": []
  },
  "api/apps/sales-cockpit/analytics": {
    "daily": [
      {
        "date": "2026-10-24",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-25",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-26",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-27",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-28",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-29",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-30",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      }
    ],
    "users": [
      {
        "user_hash": "u_demo_91a",
        "first_seen": "2026-10-01",
        "last_seen": "2026-10-30T09:27:00Z",
        "requests": 80,
        "sessions": 10,
        "active_days": 7,
        "errors": 1,
        "tokens": 4000
      }
    ],
    "mtd_usd": 397.92
  },
  "api/apps/sales-cockpit/events": {
    "events": [
      {
        "event_name": "answer_shown",
        "app_version": "1.16.7",
        "events": 40,
        "sessions": 32,
        "last_seen": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/sales-cockpit/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": [
      {
        "funnel": "answer",
        "app_version": "1.16.7",
        "step_name": "ask_question",
        "sessions": 100,
        "dropoff_pct": 0
      },
      {
        "funnel": "answer",
        "app_version": "1.16.7",
        "step_name": "answer_shown",
        "sessions": 80,
        "dropoff_pct": 20
      }
    ]
  },
  "api/apps/sales-cockpit/cohorts": {
    "cohorts": [
      {
        "cohort_week": "2026-10-19",
        "week_number": 1,
        "cohort_size": 40,
        "retained_users": 30,
        "retention_pct": 75,
        "partial_week": true
      }
    ]
  },
  "api/apps/sales-cockpit/rum": {
    "routes": [
      {
        "date": "2026-10-30",
        "route": "/",
        "page_views": 200,
        "p75_lcp": 650,
        "p75_cls": 0.02,
        "p75_inp": 80,
        "js_errors": 1,
        "fingerprint": "rum-demo",
        "trace_id": "00000000000000000000000000000066"
      }
    ]
  },
  "api/apps/sales-cockpit/guardrails": {
    "findings": [],
    "templates": []
  },
  "api/apps/sales-cockpit/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/sales-cockpit/telemetry-health": {
    "health": {
      "quality": "healthy",
      "envelope_coverage": 0.9,
      "orphan_ratio_24h": 0.01,
      "sampler_ratio": 1,
      "last_span_at": "2026-10-30T09:27:00Z",
      "last_log_at": "2026-10-30T09:27:00Z",
      "last_metric_at": "2026-10-30T09:27:00Z",
      "semconv_legacy_only": 0,
      "semconv_stable_only": 0.1,
      "semconv_both": 0.9,
      "gateway_vs_otel_tokens": 12,
      "token_date": "2026-10-29"
    }
  },
  "api/apps/sales-cockpit/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": 64.0,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": [
      {
        "slo": "availability",
        "date": "2026-10-10",
        "budget_remaining_pct": 100
      },
      {
        "slo": "availability",
        "date": "2026-10-11",
        "budget_remaining_pct": 80
      },
      {
        "slo": "availability",
        "date": "2026-10-12",
        "budget_remaining_pct": 60
      },
      {
        "slo": "availability",
        "date": "2026-10-13",
        "budget_remaining_pct": 40
      },
      {
        "slo": "availability",
        "date": "2026-10-14",
        "budget_remaining_pct": 20
      },
      {
        "slo": "availability",
        "date": "2026-10-15",
        "budget_remaining_pct": 0
      },
      {
        "slo": "availability",
        "date": "2026-10-16",
        "budget_remaining_pct": -20
      }
    ]
  },
  "api/apps/sales-cockpit": {
    "uptime_24h": 99.964,
    "p95_ms": 198,
    "error_rate_1h": 0,
    "checks_24h": 1440,
    "compute_state": "ACTIVE",
    "last": {
      "code": 200,
      "ms": 120
    },
    "ttfb_ms": 110,
    "series": [
      [
        1793350800,
        true,
        200,
        120
      ],
      [
        1793350860,
        true,
        200,
        132
      ],
      [
        1793350920,
        true,
        200,
        144
      ],
      [
        1793350980,
        false,
        502,
        156
      ],
      [
        1793351040,
        true,
        200,
        168
      ],
      [
        1793351100,
        true,
        200,
        180
      ],
      [
        1793351160,
        true,
        200,
        192
      ],
      [
        1793351220,
        true,
        200,
        204
      ]
    ]
  },
  "api/apps/sales-cockpit/synthetics": {
    "interval_s": 1800,
    "live": {
      "journey": "Report flow",
      "ok": true,
      "budget_ms": 2500,
      "within_budget": true,
      "ts": 1793352420,
      "steps": [
        {
          "name": "GET /api/report",
          "ok": true,
          "code": 200,
          "ms": 200,
          "detail": "Demo assertion"
        }
      ]
    },
    "browser": [
      {
        "run_ts": "2026-10-30T09:27:00Z",
        "journey": "browser-smoke",
        "ok": true,
        "status_code": 200,
        "latency_ms": 800,
        "detail": "Demo browser result",
        "vantage": "external",
        "failure_stage": null,
        "artifact": "/Volumes/demo/monitor/ui_tests/sales-cockpit/run"
      }
    ]
  },
  "api/apps/sales-cockpit/ops": {
    "config": {
      "tags_json": "{\"team\": \"Sales Ops\", \"cost_center\": \"CC-150\", \"env\": \"prod\", \"tier\": \"t1\"}",
      "budget_usd_month": 600,
      "auto_stop": "idle",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "refresh",
        "job": {
          "id": "101",
          "permission": "CAN_MANAGE_RUN"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 320
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/console/trace/4bf92f3577b34da6a3ce929d0e0e4736": {
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "app": "fraud-triage",
    "root": "GET /api/report",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "fraud-triage",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "fraud-triage",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "fraud-triage",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "fraud-triage",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "fraud-triage",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "fraud-triage",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "fraud-triage",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "fraud-triage",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/fraud-triage/logs": {
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
      }
    ]
  },
  "api/apps/fraud-triage/errors": {
    "groups": [
      {
        "fingerprint": "demo-3",
        "occurrences": 15,
        "first_seen": "2026-10-30T09:27:00Z",
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "Demo dependency timeout"
      }
    ],
    "failed_requests": [
      {
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ],
    "error_logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
      }
    ]
  },
  "api/apps/fraud-triage/traces": {
    "traces": [
      {
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/fraud-triage/agent-traces": {
    "experiment": "201",
    "traces": [
      {
        "trace_id": "tr-demo-3",
        "request_time": "2026-10-30T09:27:00Z",
        "duration_ms": 6420,
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested",
        "client_request_id": "demo-request",
        "tags": {
          "agent": "coverage"
        }
      }
    ]
  },
  "api/apps/fraud-triage/agent-traces/tr-demo-3": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-3",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "fraud-triage",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "fraud-triage",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "fraud-triage",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "fraud-triage",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "fraud-triage",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "fraud-triage",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "fraud-triage",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "fraud-triage",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
      }
    ]
  },
  "api/apps/fraud-triage/requests": {
    "timeline": [
      {
        "ts": "2026-10-29T10:00:00Z",
        "requests": 387,
        "errors": 119,
        "p50_ms": 1820,
        "p95_ms": 4096.44
      },
      {
        "ts": "2026-10-29T11:00:00Z",
        "requests": 413,
        "errors": 126,
        "p50_ms": 1820,
        "p95_ms": 5495.28
      },
      {
        "ts": "2026-10-29T12:00:00Z",
        "requests": 457,
        "errors": 184,
        "p50_ms": 1820,
        "p95_ms": 5144.88
      },
      {
        "ts": "2026-10-29T13:00:00Z",
        "requests": 504,
        "errors": 193,
        "p50_ms": 1820,
        "p95_ms": 5803.02
      },
      {
        "ts": "2026-10-29T14:00:00Z",
        "requests": 464,
        "errors": 158,
        "p50_ms": 1820,
        "p95_ms": 5430.21
      },
      {
        "ts": "2026-10-29T15:00:00Z",
        "requests": 436,
        "errors": 157,
        "p50_ms": 1820,
        "p95_ms": 4905.04
      },
      {
        "ts": "2026-10-29T16:00:00Z",
        "requests": 341,
        "errors": 62,
        "p50_ms": 1820,
        "p95_ms": 4711.13
      },
      {
        "ts": "2026-10-29T17:00:00Z",
        "requests": 305,
        "errors": 82,
        "p50_ms": 1820,
        "p95_ms": 3518.78
      },
      {
        "ts": "2026-10-29T18:00:00Z",
        "requests": 276,
        "errors": 73,
        "p50_ms": 1820,
        "p95_ms": 4097.31
      },
      {
        "ts": "2026-10-29T19:00:00Z",
        "requests": 244,
        "errors": 59,
        "p50_ms": 1820,
        "p95_ms": 3825.38
      },
      {
        "ts": "2026-10-29T20:00:00Z",
        "requests": 284,
        "errors": 84,
        "p50_ms": 1820,
        "p95_ms": 3181.95
      },
      {
        "ts": "2026-10-29T21:00:00Z",
        "requests": 315,
        "errors": 83,
        "p50_ms": 1820,
        "p95_ms": 4440.91
      },
      {
        "ts": "2026-10-29T22:00:00Z",
        "requests": 411,
        "errors": 80,
        "p50_ms": 1820,
        "p95_ms": 4887.23
      },
      {
        "ts": "2026-10-29T23:00:00Z",
        "requests": 409,
        "errors": 91,
        "p50_ms": 1820,
        "p95_ms": 5243.75
      },
      {
        "ts": "2026-10-30T00:00:00Z",
        "requests": 421,
        "errors": 149,
        "p50_ms": 1820,
        "p95_ms": 5852.69
      },
      {
        "ts": "2026-10-30T01:00:00Z",
        "requests": 497,
        "errors": 209,
        "p50_ms": 1820,
        "p95_ms": 5955.75
      },
      {
        "ts": "2026-10-30T02:00:00Z",
        "requests": 435,
        "errors": 133,
        "p50_ms": 1820,
        "p95_ms": 5544.53
      },
      {
        "ts": "2026-10-30T03:00:00Z",
        "requests": 398,
        "errors": 118,
        "p50_ms": 1820,
        "p95_ms": 4887.39
      },
      {
        "ts": "2026-10-30T04:00:00Z",
        "requests": 363,
        "errors": 69,
        "p50_ms": 1820,
        "p95_ms": 4698.62
      },
      {
        "ts": "2026-10-30T05:00:00Z",
        "requests": 297,
        "errors": 45,
        "p50_ms": 1820,
        "p95_ms": 3587.53
      },
      {
        "ts": "2026-10-30T06:00:00Z",
        "requests": 277,
        "errors": 60,
        "p50_ms": 1820,
        "p95_ms": 3945.84
      },
      {
        "ts": "2026-10-30T07:00:00Z",
        "requests": 293,
        "errors": 46,
        "p50_ms": 1820,
        "p95_ms": 3667.68
      },
      {
        "ts": "2026-10-30T08:00:00Z",
        "requests": 275,
        "errors": 202,
        "p50_ms": 1820,
        "p95_ms": 7582.85
      },
      {
        "ts": "2026-10-30T09:00:00Z",
        "requests": 349,
        "errors": 349,
        "p50_ms": 1820,
        "p95_ms": 11897.68
      }
    ],
    "routes": [
      {
        "route": "/api/report",
        "requests": 100,
        "errors": 3,
        "avg_ms": 310,
        "p50_ms": 200,
        "p95_ms": 900
      }
    ]
  },
  "api/apps/fraud-triage/deps": {
    "deps": [
      {
        "dependency": "databricks_sql/wh-7d1a",
        "calls": 1260,
        "avg_ms": 150,
        "p95_ms": 560,
        "errors": 3
      }
    ]
  },
  "api/apps/fraud-triage/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/fraud-triage/security": {
    "scan": {
      "name": "fraud-triage",
      "quality_score": 78,
      "findings_critical": 1,
      "findings_high": 2,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 17,
      "py_loc": 1500,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-3",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": [\"DEMO-CVE-001\"]}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/fraud-triage/review": {
    "review": {
      "name": "fraud-triage",
      "verdict": "approve_with_comments",
      "score_overall": 8.4,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo agent for Risk.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/fraud-triage/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 78.08,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 74.57,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 87.85,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 95.76,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 93.54,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 96.85,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 92.94,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 77.57,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 77.76,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 63.35,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 64.5,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 59.75,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 66.74,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 60.42,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 80.0,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 80.1,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 85.87,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 102.26,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 101.27,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 108.91,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 103.15,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 102.56,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 95.61,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 86.09,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 71.2,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 70.58,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 68.27,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 76.85,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 69.58,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 79.73,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      }
    ],
    "forecast": {
      "forecast_30d_usd": 2757.14,
      "days_observed": 30
    },
    "budget": 2400,
    "mtd_usd": 746.94
  },
  "api/apps/fraud-triage/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "fraud-triage",
        "dbu_usd": 746.94,
        "ai_usd": 1422.77,
        "total_usd": 2169.71,
        "idle_usd": 55.68,
        "usd_per_1k_requests": 8.036,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/fraud-triage/genai": {
    "daily": [
      {
        "date": "2026-10-01",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-02",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-03",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-04",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-05",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-06",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-07",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-08",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-09",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-10",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-11",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-12",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-13",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-14",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-15",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-16",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-17",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-18",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-19",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-20",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-21",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-22",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-23",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-24",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-25",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-26",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-27",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-28",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-29",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-30",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      }
    ],
    "top": [
      {
        "session_id": "hashed-session",
        "user_hash": "hashed-user",
        "calls": 10,
        "tokens": 4000,
        "last_call": "2026-10-30T09:27:00Z"
      }
    ],
    "error_taxonomy": [
      {
        "category": "rate_limit",
        "errors": 3,
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "429 upstream"
      }
    ],
    "agent_steps": [
      {
        "date": "2026-10-29",
        "avg_steps": 5,
        "max_steps": 8,
        "agent_runs": 32
      },
      {
        "date": "2026-10-30",
        "avg_steps": 7,
        "max_steps": 12,
        "agent_runs": 40
      }
    ],
    "quality": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "relevance": 8,
        "faithfulness": 7,
        "toxicity": 0,
        "traces_sampled": 10,
        "comment": "Demo sampled evaluation"
      }
    ],
    "feedback": [
      {
        "date": "2026-10-30",
        "n": 10,
        "avg_rating": 4.2,
        "negative": 1
      }
    ],
    "feedback_recent": []
  },
  "api/apps/fraud-triage/drift": {
    "reports": [
      {
        "week": "2026-10-26",
        "samples": 60,
        "k": 3,
        "silhouette": 0.6,
        "novel_share": 0.31
      }
    ]
  },
  "api/apps/fraud-triage/analytics": {
    "daily": [
      {
        "date": "2026-10-24",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-25",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-26",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-27",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-28",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-29",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-30",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      }
    ],
    "users": [
      {
        "user_hash": "u_demo_91a",
        "first_seen": "2026-10-01",
        "last_seen": "2026-10-30T09:27:00Z",
        "requests": 80,
        "sessions": 10,
        "active_days": 7,
        "errors": 1,
        "tokens": 4000
      }
    ],
    "mtd_usd": 746.94
  },
  "api/apps/fraud-triage/events": {
    "events": [
      {
        "event_name": "answer_shown",
        "app_version": "3.1.2",
        "events": 40,
        "sessions": 32,
        "last_seen": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/fraud-triage/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": [
      {
        "funnel": "answer",
        "app_version": "3.1.2",
        "step_name": "ask_question",
        "sessions": 100,
        "dropoff_pct": 0
      },
      {
        "funnel": "answer",
        "app_version": "3.1.2",
        "step_name": "answer_shown",
        "sessions": 80,
        "dropoff_pct": 20
      }
    ]
  },
  "api/apps/fraud-triage/cohorts": {
    "cohorts": [
      {
        "cohort_week": "2026-10-19",
        "week_number": 1,
        "cohort_size": 40,
        "retained_users": 30,
        "retention_pct": 75,
        "partial_week": true
      }
    ]
  },
  "api/apps/fraud-triage/rum": {
    "routes": [
      {
        "date": "2026-10-30",
        "route": "/",
        "page_views": 200,
        "p75_lcp": 650,
        "p75_cls": 0.02,
        "p75_inp": 80,
        "js_errors": 1,
        "fingerprint": "rum-demo",
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
      }
    ]
  },
  "api/apps/fraud-triage/guardrails": {
    "findings": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "kind": "pii",
        "severity": "warning",
        "excerpt_masked": "[EMAIL]",
        "excerpt_hash": "demo-hash",
        "trace_id": "tr-demo-3"
      }
    ],
    "templates": [
      {
        "date": "2026-10-30",
        "template_hash": "template-demo",
        "samples": 12,
        "daily_samples": 40,
        "share": 0.3
      }
    ]
  },
  "api/apps/fraud-triage/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/fraud-triage/telemetry-health": {
    "health": {
      "quality": "healthy",
      "envelope_coverage": 0.9,
      "orphan_ratio_24h": 0.01,
      "sampler_ratio": 1,
      "last_span_at": "2026-10-30T09:27:00Z",
      "last_log_at": "2026-10-30T09:27:00Z",
      "last_metric_at": "2026-10-30T09:27:00Z",
      "semconv_legacy_only": 0,
      "semconv_stable_only": 0.1,
      "semconv_both": 0.9,
      "gateway_vs_otel_tokens": 12,
      "token_date": "2026-10-29"
    }
  },
  "api/apps/fraud-triage/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": -8411.0,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": [
      {
        "slo": "availability",
        "date": "2026-10-10",
        "budget_remaining_pct": 100
      },
      {
        "slo": "availability",
        "date": "2026-10-11",
        "budget_remaining_pct": 80
      },
      {
        "slo": "availability",
        "date": "2026-10-12",
        "budget_remaining_pct": 60
      },
      {
        "slo": "availability",
        "date": "2026-10-13",
        "budget_remaining_pct": 40
      },
      {
        "slo": "availability",
        "date": "2026-10-14",
        "budget_remaining_pct": 20
      },
      {
        "slo": "availability",
        "date": "2026-10-15",
        "budget_remaining_pct": 0
      },
      {
        "slo": "availability",
        "date": "2026-10-16",
        "budget_remaining_pct": -20
      }
    ]
  },
  "api/apps/fraud-triage": {
    "uptime_24h": 91.489,
    "p95_ms": 207,
    "error_rate_1h": 100,
    "checks_24h": 1440,
    "compute_state": "ACTIVE",
    "last": {
      "code": 200,
      "ms": 120
    },
    "ttfb_ms": 110,
    "series": [
      [
        1793350800,
        true,
        200,
        120
      ],
      [
        1793350860,
        true,
        200,
        132
      ],
      [
        1793350920,
        true,
        200,
        144
      ],
      [
        1793350980,
        false,
        502,
        156
      ],
      [
        1793351040,
        true,
        200,
        168
      ],
      [
        1793351100,
        true,
        200,
        180
      ],
      [
        1793351160,
        true,
        200,
        192
      ],
      [
        1793351220,
        true,
        200,
        204
      ]
    ]
  },
  "api/apps/fraud-triage/synthetics": {
    "interval_s": 1800,
    "live": {
      "journey": "Report flow",
      "ok": false,
      "budget_ms": 2500,
      "within_budget": false,
      "ts": 1793352420,
      "steps": [
        {
          "name": "GET /api/report",
          "ok": false,
          "code": 502,
          "ms": 200,
          "detail": "Demo assertion"
        }
      ]
    },
    "browser": [
      {
        "run_ts": "2026-10-30T09:27:00Z",
        "journey": "browser-smoke",
        "ok": false,
        "status_code": 502,
        "latency_ms": 800,
        "detail": "Demo browser result",
        "vantage": "external",
        "failure_stage": "http",
        "artifact": "/Volumes/demo/monitor/ui_tests/fraud-triage/run"
      }
    ]
  },
  "api/apps/fraud-triage/ops": {
    "config": {
      "tags_json": "{\"team\": \"Risk\", \"cost_center\": \"CC-330\", \"env\": \"prod\", \"tier\": \"t1\"}",
      "budget_usd_month": 2400,
      "auto_stop": "none",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "warehouse",
        "sql_warehouse": {
          "id": "wh-7d1a",
          "permission": "CAN_USE"
        }
      },
      {
        "name": "risk-store",
        "database": {
          "instance_name": "risk-db",
          "permission": "CAN_CONNECT_AND_CREATE"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 320
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/console/trace/00000000000000000000000000000068": {
    "trace_id": "00000000000000000000000000000068",
    "app": "supplier-portal",
    "root": "GET /api/report",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "supplier-portal",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "supplier-portal",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "supplier-portal",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "supplier-portal",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "supplier-portal",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "supplier-portal",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "supplier-portal",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "supplier-portal",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/supplier-portal/logs": {
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "00000000000000000000000000000068"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "00000000000000000000000000000068"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000068"
      }
    ]
  },
  "api/apps/supplier-portal/errors": {
    "groups": [
      {
        "fingerprint": "demo-4",
        "occurrences": 16,
        "first_seen": "2026-10-30T09:27:00Z",
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "Demo dependency timeout"
      }
    ],
    "failed_requests": [
      {
        "trace_id": "00000000000000000000000000000068",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ],
    "error_logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000068"
      }
    ]
  },
  "api/apps/supplier-portal/traces": {
    "traces": [
      {
        "trace_id": "00000000000000000000000000000068",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/supplier-portal/agent-traces": {
    "experiment": null,
    "traces": []
  },
  "api/apps/supplier-portal/agent-traces/tr-demo-4": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-4",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "supplier-portal",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "supplier-portal",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "supplier-portal",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "supplier-portal",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "supplier-portal",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "supplier-portal",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "supplier-portal",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "supplier-portal",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "00000000000000000000000000000068"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "00000000000000000000000000000068"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000068"
      }
    ]
  },
  "api/apps/supplier-portal/requests": {
    "timeline": [
      {
        "ts": "2026-10-29T10:00:00Z",
        "requests": 922,
        "errors": 3,
        "p50_ms": 89,
        "p95_ms": 154.71
      },
      {
        "ts": "2026-10-29T11:00:00Z",
        "requests": 977,
        "errors": 3,
        "p50_ms": 89,
        "p95_ms": 210.77
      },
      {
        "ts": "2026-10-29T12:00:00Z",
        "requests": 1051,
        "errors": 5,
        "p50_ms": 89,
        "p95_ms": 203.62
      },
      {
        "ts": "2026-10-29T13:00:00Z",
        "requests": 1035,
        "errors": 5,
        "p50_ms": 89,
        "p95_ms": 204.18
      },
      {
        "ts": "2026-10-29T14:00:00Z",
        "requests": 1043,
        "errors": 4,
        "p50_ms": 89,
        "p95_ms": 217.9
      },
      {
        "ts": "2026-10-29T15:00:00Z",
        "requests": 961,
        "errors": 3,
        "p50_ms": 89,
        "p95_ms": 202.89
      },
      {
        "ts": "2026-10-29T16:00:00Z",
        "requests": 853,
        "errors": 3,
        "p50_ms": 89,
        "p95_ms": 166.54
      },
      {
        "ts": "2026-10-29T17:00:00Z",
        "requests": 753,
        "errors": 3,
        "p50_ms": 89,
        "p95_ms": 128.43
      },
      {
        "ts": "2026-10-29T18:00:00Z",
        "requests": 768,
        "errors": 1,
        "p50_ms": 89,
        "p95_ms": 143.97
      },
      {
        "ts": "2026-10-29T19:00:00Z",
        "requests": 608,
        "errors": 2,
        "p50_ms": 89,
        "p95_ms": 122.96
      },
      {
        "ts": "2026-10-29T20:00:00Z",
        "requests": 605,
        "errors": 1,
        "p50_ms": 89,
        "p95_ms": 148.81
      },
      {
        "ts": "2026-10-29T21:00:00Z",
        "requests": 814,
        "errors": 2,
        "p50_ms": 89,
        "p95_ms": 150.7
      },
      {
        "ts": "2026-10-29T22:00:00Z",
        "requests": 838,
        "errors": 4,
        "p50_ms": 89,
        "p95_ms": 157.03
      },
      {
        "ts": "2026-10-29T23:00:00Z",
        "requests": 915,
        "errors": 4,
        "p50_ms": 89,
        "p95_ms": 173.02
      },
      {
        "ts": "2026-10-30T00:00:00Z",
        "requests": 1053,
        "errors": 4,
        "p50_ms": 89,
        "p95_ms": 224.7
      },
      {
        "ts": "2026-10-30T01:00:00Z",
        "requests": 1167,
        "errors": 5,
        "p50_ms": 89,
        "p95_ms": 208.22
      },
      {
        "ts": "2026-10-30T02:00:00Z",
        "requests": 998,
        "errors": 5,
        "p50_ms": 89,
        "p95_ms": 211.19
      },
      {
        "ts": "2026-10-30T03:00:00Z",
        "requests": 1067,
        "errors": 4,
        "p50_ms": 89,
        "p95_ms": 175.48
      },
      {
        "ts": "2026-10-30T04:00:00Z",
        "requests": 927,
        "errors": 3,
        "p50_ms": 89,
        "p95_ms": 185.27
      },
      {
        "ts": "2026-10-30T05:00:00Z",
        "requests": 834,
        "errors": 2,
        "p50_ms": 89,
        "p95_ms": 147.79
      },
      {
        "ts": "2026-10-30T06:00:00Z",
        "requests": 652,
        "errors": 1,
        "p50_ms": 89,
        "p95_ms": 150.35
      },
      {
        "ts": "2026-10-30T07:00:00Z",
        "requests": 582,
        "errors": 2,
        "p50_ms": 89,
        "p95_ms": 129.32
      },
      {
        "ts": "2026-10-30T08:00:00Z",
        "requests": 719,
        "errors": 2,
        "p50_ms": 89,
        "p95_ms": 118.92
      },
      {
        "ts": "2026-10-30T09:00:00Z",
        "requests": 795,
        "errors": 2,
        "p50_ms": 89,
        "p95_ms": 144.79
      }
    ],
    "routes": [
      {
        "route": "/api/report",
        "requests": 100,
        "errors": 3,
        "avg_ms": 310,
        "p50_ms": 200,
        "p95_ms": 900
      }
    ]
  },
  "api/apps/supplier-portal/deps": {
    "deps": [
      {
        "dependency": "databricks_sql/wh-7d1a",
        "calls": 1280,
        "avg_ms": 150,
        "p95_ms": 560,
        "errors": 4
      }
    ]
  },
  "api/apps/supplier-portal/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/supplier-portal/security": {
    "scan": {
      "name": "supplier-portal",
      "quality_score": 75,
      "findings_critical": 0,
      "findings_high": 3,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 18,
      "py_loc": 1600,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-4",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": []}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/supplier-portal/review": {
    "review": {
      "name": "supplier-portal",
      "verdict": "reject",
      "score_overall": 4.1,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo web for Procurement.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/supplier-portal/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 22.59,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 29.38,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 29.05,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 32.16,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 29.75,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 29.25,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 29.92,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 26.28,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 24.06,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 20.62,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 20.51,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 18.92,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 20.5,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 22.09,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 20.41,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 26.97,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 26.95,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 30.36,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 30.59,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 30.26,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 31.97,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 31.0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 24.42,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 23.32,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 22.63,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 21.1,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 21.12,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 19.0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 18.21,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 24.6,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      }
    ],
    "forecast": {
      "forecast_30d_usd": 782.89,
      "days_observed": 30
    },
    "budget": 1000,
    "mtd_usd": 749.66
  },
  "api/apps/supplier-portal/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "supplier-portal",
        "dbu_usd": 749.66,
        "ai_usd": 0,
        "total_usd": 749.66,
        "idle_usd": 249.84,
        "usd_per_1k_requests": 1.181,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/supplier-portal/genai": {
    "daily": [],
    "top": [],
    "error_taxonomy": [],
    "agent_steps": [],
    "quality": [],
    "feedback": [],
    "feedback_recent": []
  },
  "api/apps/supplier-portal/drift": {
    "reports": []
  },
  "api/apps/supplier-portal/analytics": {
    "daily": [
      {
        "date": "2026-10-24",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-25",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-26",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-27",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-28",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-29",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-30",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      }
    ],
    "users": [
      {
        "user_hash": "u_demo_91a",
        "first_seen": "2026-10-01",
        "last_seen": "2026-10-30T09:27:00Z",
        "requests": 80,
        "sessions": 10,
        "active_days": 7,
        "errors": 1,
        "tokens": 4000
      }
    ],
    "mtd_usd": 749.66
  },
  "api/apps/supplier-portal/events": {
    "events": [
      {
        "event_name": "answer_shown",
        "app_version": "2.15.7",
        "events": 40,
        "sessions": 32,
        "last_seen": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/supplier-portal/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": [
      {
        "funnel": "answer",
        "app_version": "2.15.7",
        "step_name": "ask_question",
        "sessions": 100,
        "dropoff_pct": 0
      },
      {
        "funnel": "answer",
        "app_version": "2.15.7",
        "step_name": "answer_shown",
        "sessions": 80,
        "dropoff_pct": 20
      }
    ]
  },
  "api/apps/supplier-portal/cohorts": {
    "cohorts": [
      {
        "cohort_week": "2026-10-19",
        "week_number": 1,
        "cohort_size": 40,
        "retained_users": 30,
        "retention_pct": 75,
        "partial_week": true
      }
    ]
  },
  "api/apps/supplier-portal/rum": {
    "routes": [
      {
        "date": "2026-10-30",
        "route": "/",
        "page_views": 200,
        "p75_lcp": 650,
        "p75_cls": 0.02,
        "p75_inp": 80,
        "js_errors": 1,
        "fingerprint": "rum-demo",
        "trace_id": "00000000000000000000000000000068"
      }
    ]
  },
  "api/apps/supplier-portal/guardrails": {
    "findings": [],
    "templates": []
  },
  "api/apps/supplier-portal/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/supplier-portal/telemetry-health": {
    "health": {
      "quality": "healthy",
      "envelope_coverage": 0.9,
      "orphan_ratio_24h": 0.01,
      "sampler_ratio": 1,
      "last_span_at": "2026-10-30T09:27:00Z",
      "last_log_at": "2026-10-30T09:27:00Z",
      "last_metric_at": "2026-10-30T09:27:00Z",
      "semconv_legacy_only": 0,
      "semconv_stable_only": 0.1,
      "semconv_both": 0.9,
      "gateway_vs_otel_tokens": 12,
      "token_date": "2026-10-29"
    }
  },
  "api/apps/supplier-portal/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": 85.0,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": [
      {
        "slo": "availability",
        "date": "2026-10-10",
        "budget_remaining_pct": 100
      },
      {
        "slo": "availability",
        "date": "2026-10-11",
        "budget_remaining_pct": 80
      },
      {
        "slo": "availability",
        "date": "2026-10-12",
        "budget_remaining_pct": 60
      },
      {
        "slo": "availability",
        "date": "2026-10-13",
        "budget_remaining_pct": 40
      },
      {
        "slo": "availability",
        "date": "2026-10-14",
        "budget_remaining_pct": 20
      },
      {
        "slo": "availability",
        "date": "2026-10-15",
        "budget_remaining_pct": 0
      },
      {
        "slo": "availability",
        "date": "2026-10-16",
        "budget_remaining_pct": -20
      }
    ]
  },
  "api/apps/supplier-portal": {
    "uptime_24h": 99.985,
    "p95_ms": 216,
    "error_rate_1h": 0,
    "checks_24h": 1440,
    "compute_state": "ACTIVE",
    "last": {
      "code": 200,
      "ms": 120
    },
    "ttfb_ms": 110,
    "series": [
      [
        1793350800,
        true,
        200,
        120
      ],
      [
        1793350860,
        true,
        200,
        132
      ],
      [
        1793350920,
        true,
        200,
        144
      ],
      [
        1793350980,
        false,
        502,
        156
      ],
      [
        1793351040,
        true,
        200,
        168
      ],
      [
        1793351100,
        true,
        200,
        180
      ],
      [
        1793351160,
        true,
        200,
        192
      ],
      [
        1793351220,
        true,
        200,
        204
      ]
    ]
  },
  "api/apps/supplier-portal/synthetics": {
    "interval_s": 1800,
    "live": {
      "journey": "Report flow",
      "ok": true,
      "budget_ms": 2500,
      "within_budget": true,
      "ts": 1793352420,
      "steps": [
        {
          "name": "GET /api/report",
          "ok": true,
          "code": 200,
          "ms": 200,
          "detail": "Demo assertion"
        }
      ]
    },
    "browser": [
      {
        "run_ts": "2026-10-30T09:27:00Z",
        "journey": "browser-smoke",
        "ok": true,
        "status_code": 200,
        "latency_ms": 800,
        "detail": "Demo browser result",
        "vantage": "external",
        "failure_stage": null,
        "artifact": "/Volumes/demo/monitor/ui_tests/supplier-portal/run"
      }
    ]
  },
  "api/apps/supplier-portal/ops": {
    "config": {
      "tags_json": "{\"team\": \"Procurement\", \"cost_center\": \"CC-505\", \"env\": \"prod\", \"tier\": \"t1\"}",
      "budget_usd_month": 1000,
      "auto_stop": "none",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "risk-store",
        "database": {
          "instance_name": "risk-db",
          "permission": "CAN_CONNECT_AND_CREATE"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 320
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/console/trace/00000000000000000000000000000069": {
    "trace_id": "00000000000000000000000000000069",
    "app": "hr-policy-bot",
    "root": "GET /api/report",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "hr-policy-bot",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "hr-policy-bot",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "hr-policy-bot",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "hr-policy-bot",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "hr-policy-bot",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "hr-policy-bot",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "hr-policy-bot",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "hr-policy-bot",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/hr-policy-bot/logs": {
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "00000000000000000000000000000069"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "00000000000000000000000000000069"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000069"
      }
    ]
  },
  "api/apps/hr-policy-bot/errors": {
    "groups": [
      {
        "fingerprint": "demo-5",
        "occurrences": 17,
        "first_seen": "2026-10-30T09:27:00Z",
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "Demo dependency timeout"
      }
    ],
    "failed_requests": [
      {
        "trace_id": "00000000000000000000000000000069",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ],
    "error_logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000069"
      }
    ]
  },
  "api/apps/hr-policy-bot/traces": {
    "traces": [
      {
        "trace_id": "00000000000000000000000000000069",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/hr-policy-bot/agent-traces": {
    "experiment": "201",
    "traces": [
      {
        "trace_id": "tr-demo-5",
        "request_time": "2026-10-30T09:27:00Z",
        "duration_ms": 6420,
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested",
        "client_request_id": "demo-request",
        "tags": {
          "agent": "coverage"
        }
      }
    ]
  },
  "api/apps/hr-policy-bot/agent-traces/tr-demo-5": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-5",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "hr-policy-bot",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "hr-policy-bot",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "hr-policy-bot",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "hr-policy-bot",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "hr-policy-bot",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "hr-policy-bot",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "hr-policy-bot",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "hr-policy-bot",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "00000000000000000000000000000069"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "00000000000000000000000000000069"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "00000000000000000000000000000069"
      }
    ]
  },
  "api/apps/hr-policy-bot/requests": {
    "timeline": [
      {
        "ts": "2026-10-29T10:00:00Z",
        "requests": 1636,
        "errors": 5,
        "p50_ms": 87,
        "p95_ms": 161.5
      },
      {
        "ts": "2026-10-29T11:00:00Z",
        "requests": 1855,
        "errors": 7,
        "p50_ms": 87,
        "p95_ms": 175.4
      },
      {
        "ts": "2026-10-29T12:00:00Z",
        "requests": 1814,
        "errors": 9,
        "p50_ms": 87,
        "p95_ms": 207.38
      },
      {
        "ts": "2026-10-29T13:00:00Z",
        "requests": 1854,
        "errors": 10,
        "p50_ms": 87,
        "p95_ms": 223.52
      },
      {
        "ts": "2026-10-29T14:00:00Z",
        "requests": 1946,
        "errors": 7,
        "p50_ms": 87,
        "p95_ms": 189.22
      },
      {
        "ts": "2026-10-29T15:00:00Z",
        "requests": 1819,
        "errors": 7,
        "p50_ms": 87,
        "p95_ms": 166.2
      },
      {
        "ts": "2026-10-29T16:00:00Z",
        "requests": 1557,
        "errors": 5,
        "p50_ms": 87,
        "p95_ms": 158.13
      },
      {
        "ts": "2026-10-29T17:00:00Z",
        "requests": 1306,
        "errors": 5,
        "p50_ms": 87,
        "p95_ms": 140.93
      },
      {
        "ts": "2026-10-29T18:00:00Z",
        "requests": 1280,
        "errors": 2,
        "p50_ms": 87,
        "p95_ms": 136.64
      },
      {
        "ts": "2026-10-29T19:00:00Z",
        "requests": 1039,
        "errors": 2,
        "p50_ms": 87,
        "p95_ms": 111.16
      },
      {
        "ts": "2026-10-29T20:00:00Z",
        "requests": 1185,
        "errors": 2,
        "p50_ms": 87,
        "p95_ms": 141.36
      },
      {
        "ts": "2026-10-29T21:00:00Z",
        "requests": 1381,
        "errors": 4,
        "p50_ms": 87,
        "p95_ms": 154.05
      },
      {
        "ts": "2026-10-29T22:00:00Z",
        "requests": 1739,
        "errors": 8,
        "p50_ms": 87,
        "p95_ms": 165.0
      },
      {
        "ts": "2026-10-29T23:00:00Z",
        "requests": 1838,
        "errors": 9,
        "p50_ms": 87,
        "p95_ms": 173.26
      },
      {
        "ts": "2026-10-30T00:00:00Z",
        "requests": 2060,
        "errors": 10,
        "p50_ms": 87,
        "p95_ms": 219.84
      },
      {
        "ts": "2026-10-30T01:00:00Z",
        "requests": 1983,
        "errors": 11,
        "p50_ms": 87,
        "p95_ms": 198.24
      },
      {
        "ts": "2026-10-30T02:00:00Z",
        "requests": 1853,
        "errors": 10,
        "p50_ms": 87,
        "p95_ms": 213.66
      },
      {
        "ts": "2026-10-30T03:00:00Z",
        "requests": 1712,
        "errors": 6,
        "p50_ms": 87,
        "p95_ms": 174.31
      },
      {
        "ts": "2026-10-30T04:00:00Z",
        "requests": 1740,
        "errors": 5,
        "p50_ms": 87,
        "p95_ms": 153.32
      },
      {
        "ts": "2026-10-30T05:00:00Z",
        "requests": 1459,
        "errors": 6,
        "p50_ms": 87,
        "p95_ms": 154.93
      },
      {
        "ts": "2026-10-30T06:00:00Z",
        "requests": 1187,
        "errors": 4,
        "p50_ms": 87,
        "p95_ms": 120.67
      },
      {
        "ts": "2026-10-30T07:00:00Z",
        "requests": 1042,
        "errors": 2,
        "p50_ms": 87,
        "p95_ms": 142.22
      },
      {
        "ts": "2026-10-30T08:00:00Z",
        "requests": 1248,
        "errors": 4,
        "p50_ms": 87,
        "p95_ms": 128.95
      },
      {
        "ts": "2026-10-30T09:00:00Z",
        "requests": 1450,
        "errors": 4,
        "p50_ms": 87,
        "p95_ms": 131.32
      }
    ],
    "routes": [
      {
        "route": "/api/report",
        "requests": 100,
        "errors": 3,
        "avg_ms": 310,
        "p50_ms": 200,
        "p95_ms": 900
      }
    ]
  },
  "api/apps/hr-policy-bot/deps": {
    "deps": [
      {
        "dependency": "databricks_sql/wh-7d1a",
        "calls": 1300,
        "avg_ms": 150,
        "p95_ms": 560,
        "errors": 5
      }
    ]
  },
  "api/apps/hr-policy-bot/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/hr-policy-bot/security": {
    "scan": {
      "name": "hr-policy-bot",
      "quality_score": 62,
      "findings_critical": 0,
      "findings_high": 0,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 19,
      "py_loc": 1700,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-5",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": []}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/hr-policy-bot/review": {
    "review": {
      "name": "hr-policy-bot",
      "verdict": "approve",
      "score_overall": 7.8,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo agent for People.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/hr-policy-bot/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 76.03,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 82.5,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 94.89,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 101.38,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 113.14,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 97.87,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 106.54,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 86.88,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 81.02,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 80.94,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 75.41,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 66.8,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 62.16,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 74.47,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 81.3,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 100.46,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 99.05,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 110.74,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 125.37,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 113.32,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 117.4,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 118.06,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 108.83,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 87.46,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 78.55,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 72.61,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 83.92,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 74.86,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 88.88,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 100.83,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      }
    ],
    "forecast": {
      "forecast_30d_usd": 2648.8,
      "days_observed": 30
    },
    "budget": 3400,
    "mtd_usd": 727.43
  },
  "api/apps/hr-policy-bot/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "hr-policy-bot",
        "dbu_usd": 727.43,
        "ai_usd": 1715.0,
        "total_usd": 2442.43,
        "idle_usd": 131.56,
        "usd_per_1k_requests": 2.129,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/hr-policy-bot/genai": {
    "daily": [
      {
        "date": "2026-10-01",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-02",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-03",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-04",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-05",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-06",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-07",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-08",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-09",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-10",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-11",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-12",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-13",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-14",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-15",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-16",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-17",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-18",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-19",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-20",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-21",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-22",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-23",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-24",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-25",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-26",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-27",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-28",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-29",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-30",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      }
    ],
    "top": [
      {
        "session_id": "hashed-session",
        "user_hash": "hashed-user",
        "calls": 10,
        "tokens": 4000,
        "last_call": "2026-10-30T09:27:00Z"
      }
    ],
    "error_taxonomy": [
      {
        "category": "rate_limit",
        "errors": 3,
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "429 upstream"
      }
    ],
    "agent_steps": [
      {
        "date": "2026-10-29",
        "avg_steps": 5,
        "max_steps": 8,
        "agent_runs": 32
      },
      {
        "date": "2026-10-30",
        "avg_steps": 7,
        "max_steps": 12,
        "agent_runs": 40
      }
    ],
    "quality": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "relevance": 8,
        "faithfulness": 7,
        "toxicity": 0,
        "traces_sampled": 10,
        "comment": "Demo sampled evaluation"
      }
    ],
    "feedback": [
      {
        "date": "2026-10-30",
        "n": 10,
        "avg_rating": 4.2,
        "negative": 1
      }
    ],
    "feedback_recent": []
  },
  "api/apps/hr-policy-bot/drift": {
    "reports": [
      {
        "week": "2026-10-26",
        "samples": 60,
        "k": 3,
        "silhouette": 0.6,
        "novel_share": 0.31
      }
    ]
  },
  "api/apps/hr-policy-bot/analytics": {
    "daily": [
      {
        "date": "2026-10-24",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-25",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-26",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-27",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-28",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-29",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-30",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      }
    ],
    "users": [
      {
        "user_hash": "u_demo_91a",
        "first_seen": "2026-10-01",
        "last_seen": "2026-10-30T09:27:00Z",
        "requests": 80,
        "sessions": 10,
        "active_days": 7,
        "errors": 1,
        "tokens": 4000
      }
    ],
    "mtd_usd": 727.43
  },
  "api/apps/hr-policy-bot/events": {
    "events": [
      {
        "event_name": "answer_shown",
        "app_version": "1.0.2",
        "events": 40,
        "sessions": 32,
        "last_seen": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/hr-policy-bot/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": [
      {
        "funnel": "answer",
        "app_version": "1.0.2",
        "step_name": "ask_question",
        "sessions": 100,
        "dropoff_pct": 0
      },
      {
        "funnel": "answer",
        "app_version": "1.0.2",
        "step_name": "answer_shown",
        "sessions": 80,
        "dropoff_pct": 20
      }
    ]
  },
  "api/apps/hr-policy-bot/cohorts": {
    "cohorts": [
      {
        "cohort_week": "2026-10-19",
        "week_number": 1,
        "cohort_size": 40,
        "retained_users": 30,
        "retention_pct": 75,
        "partial_week": true
      }
    ]
  },
  "api/apps/hr-policy-bot/rum": {
    "routes": [
      {
        "date": "2026-10-30",
        "route": "/",
        "page_views": 200,
        "p75_lcp": 650,
        "p75_cls": 0.02,
        "p75_inp": 80,
        "js_errors": 1,
        "fingerprint": "rum-demo",
        "trace_id": "00000000000000000000000000000069"
      }
    ]
  },
  "api/apps/hr-policy-bot/guardrails": {
    "findings": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "kind": "pii",
        "severity": "warning",
        "excerpt_masked": "[EMAIL]",
        "excerpt_hash": "demo-hash",
        "trace_id": "tr-demo-5"
      }
    ],
    "templates": [
      {
        "date": "2026-10-30",
        "template_hash": "template-demo",
        "samples": 12,
        "daily_samples": 40,
        "share": 0.3
      }
    ]
  },
  "api/apps/hr-policy-bot/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/hr-policy-bot/telemetry-health": {
    "health": {
      "quality": "healthy",
      "envelope_coverage": 0.9,
      "orphan_ratio_24h": 0.01,
      "sampler_ratio": 1,
      "last_span_at": "2026-10-30T09:27:00Z",
      "last_log_at": "2026-10-30T09:27:00Z",
      "last_metric_at": "2026-10-30T09:27:00Z",
      "semconv_legacy_only": 0,
      "semconv_stable_only": 0.1,
      "semconv_both": 0.9,
      "gateway_vs_otel_tokens": 12,
      "token_date": "2026-10-29"
    }
  },
  "api/apps/hr-policy-bot/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": 54.0,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": [
      {
        "slo": "availability",
        "date": "2026-10-10",
        "budget_remaining_pct": 100
      },
      {
        "slo": "availability",
        "date": "2026-10-11",
        "budget_remaining_pct": 80
      },
      {
        "slo": "availability",
        "date": "2026-10-12",
        "budget_remaining_pct": 60
      },
      {
        "slo": "availability",
        "date": "2026-10-13",
        "budget_remaining_pct": 40
      },
      {
        "slo": "availability",
        "date": "2026-10-14",
        "budget_remaining_pct": 20
      },
      {
        "slo": "availability",
        "date": "2026-10-15",
        "budget_remaining_pct": 0
      },
      {
        "slo": "availability",
        "date": "2026-10-16",
        "budget_remaining_pct": -20
      }
    ]
  },
  "api/apps/hr-policy-bot": {
    "uptime_24h": 99.954,
    "p95_ms": 225,
    "error_rate_1h": 0,
    "checks_24h": 1440,
    "compute_state": "ACTIVE",
    "last": {
      "code": 200,
      "ms": 120
    },
    "ttfb_ms": 110,
    "series": [
      [
        1793350800,
        true,
        200,
        120
      ],
      [
        1793350860,
        true,
        200,
        132
      ],
      [
        1793350920,
        true,
        200,
        144
      ],
      [
        1793350980,
        false,
        502,
        156
      ],
      [
        1793351040,
        true,
        200,
        168
      ],
      [
        1793351100,
        true,
        200,
        180
      ],
      [
        1793351160,
        true,
        200,
        192
      ],
      [
        1793351220,
        true,
        200,
        204
      ]
    ]
  },
  "api/apps/hr-policy-bot/synthetics": {
    "interval_s": 1800,
    "live": {
      "journey": "Report flow",
      "ok": true,
      "budget_ms": 2500,
      "within_budget": true,
      "ts": 1793352420,
      "steps": [
        {
          "name": "GET /api/report",
          "ok": true,
          "code": 200,
          "ms": 200,
          "detail": "Demo assertion"
        }
      ]
    },
    "browser": [
      {
        "run_ts": "2026-10-30T09:27:00Z",
        "journey": "browser-smoke",
        "ok": true,
        "status_code": 200,
        "latency_ms": 800,
        "detail": "Demo browser result",
        "vantage": "external",
        "failure_stage": null,
        "artifact": "/Volumes/demo/monitor/ui_tests/hr-policy-bot/run"
      }
    ]
  },
  "api/apps/hr-policy-bot/ops": {
    "config": {
      "tags_json": "{\"team\": \"People\", \"cost_center\": \"CC-610\", \"env\": \"prod\", \"tier\": \"t1\"}",
      "budget_usd_month": 3400,
      "auto_stop": "idle",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "claims-store",
        "postgres": {
          "database": "claims-db",
          "branch": "production"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 320
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/console/trace/0000000000000000000000000000006a": {
    "trace_id": "0000000000000000000000000000006a",
    "app": "forecast-studio",
    "root": "GET /api/report",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "forecast-studio",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "forecast-studio",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "forecast-studio",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "forecast-studio",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "forecast-studio",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "forecast-studio",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "forecast-studio",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "forecast-studio",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/forecast-studio/logs": {
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0000000000000000000000000000006a"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0000000000000000000000000000006a"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006a"
      }
    ]
  },
  "api/apps/forecast-studio/errors": {
    "groups": [
      {
        "fingerprint": "demo-6",
        "occurrences": 18,
        "first_seen": "2026-10-30T09:27:00Z",
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "Demo dependency timeout"
      }
    ],
    "failed_requests": [
      {
        "trace_id": "0000000000000000000000000000006a",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ],
    "error_logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006a"
      }
    ]
  },
  "api/apps/forecast-studio/traces": {
    "traces": [
      {
        "trace_id": "0000000000000000000000000000006a",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/forecast-studio/agent-traces": {
    "experiment": null,
    "traces": []
  },
  "api/apps/forecast-studio/agent-traces/tr-demo-6": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-6",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "forecast-studio",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "forecast-studio",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "forecast-studio",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "forecast-studio",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "forecast-studio",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "forecast-studio",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "forecast-studio",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "forecast-studio",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0000000000000000000000000000006a"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0000000000000000000000000000006a"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006a"
      }
    ]
  },
  "api/apps/forecast-studio/requests": {
    "timeline": [
      {
        "ts": "2026-10-29T10:00:00Z",
        "requests": 883,
        "errors": 14,
        "p50_ms": 682,
        "p95_ms": 1757.76
      },
      {
        "ts": "2026-10-29T11:00:00Z",
        "requests": 925,
        "errors": 16,
        "p50_ms": 682,
        "p95_ms": 1867.68
      },
      {
        "ts": "2026-10-29T12:00:00Z",
        "requests": 1052,
        "errors": 26,
        "p50_ms": 682,
        "p95_ms": 2053.2
      },
      {
        "ts": "2026-10-29T13:00:00Z",
        "requests": 1025,
        "errors": 22,
        "p50_ms": 682,
        "p95_ms": 2133.44
      },
      {
        "ts": "2026-10-29T14:00:00Z",
        "requests": 990,
        "errors": 26,
        "p50_ms": 682,
        "p95_ms": 2353.08
      },
      {
        "ts": "2026-10-29T15:00:00Z",
        "requests": 1006,
        "errors": 27,
        "p50_ms": 682,
        "p95_ms": 1868.8
      },
      {
        "ts": "2026-10-29T16:00:00Z",
        "requests": 824,
        "errors": 19,
        "p50_ms": 682,
        "p95_ms": 1590.62
      },
      {
        "ts": "2026-10-29T17:00:00Z",
        "requests": 752,
        "errors": 8,
        "p50_ms": 682,
        "p95_ms": 1450.89
      },
      {
        "ts": "2026-10-29T18:00:00Z",
        "requests": 771,
        "errors": 14,
        "p50_ms": 682,
        "p95_ms": 1285.02
      },
      {
        "ts": "2026-10-29T19:00:00Z",
        "requests": 739,
        "errors": 13,
        "p50_ms": 682,
        "p95_ms": 1350.34
      },
      {
        "ts": "2026-10-29T20:00:00Z",
        "requests": 628,
        "errors": 9,
        "p50_ms": 682,
        "p95_ms": 1465.15
      },
      {
        "ts": "2026-10-29T21:00:00Z",
        "requests": 701,
        "errors": 8,
        "p50_ms": 682,
        "p95_ms": 1383.46
      },
      {
        "ts": "2026-10-29T22:00:00Z",
        "requests": 868,
        "errors": 16,
        "p50_ms": 682,
        "p95_ms": 1768.7
      },
      {
        "ts": "2026-10-29T23:00:00Z",
        "requests": 1053,
        "errors": 18,
        "p50_ms": 682,
        "p95_ms": 1801.32
      },
      {
        "ts": "2026-10-30T00:00:00Z",
        "requests": 1018,
        "errors": 32,
        "p50_ms": 682,
        "p95_ms": 1950.12
      },
      {
        "ts": "2026-10-30T01:00:00Z",
        "requests": 1100,
        "errors": 21,
        "p50_ms": 682,
        "p95_ms": 2401.82
      },
      {
        "ts": "2026-10-30T02:00:00Z",
        "requests": 1112,
        "errors": 31,
        "p50_ms": 682,
        "p95_ms": 2051.24
      },
      {
        "ts": "2026-10-30T03:00:00Z",
        "requests": 1030,
        "errors": 30,
        "p50_ms": 682,
        "p95_ms": 1984.83
      },
      {
        "ts": "2026-10-30T04:00:00Z",
        "requests": 924,
        "errors": 23,
        "p50_ms": 682,
        "p95_ms": 1728.52
      },
      {
        "ts": "2026-10-30T05:00:00Z",
        "requests": 730,
        "errors": 16,
        "p50_ms": 682,
        "p95_ms": 1729.86
      },
      {
        "ts": "2026-10-30T06:00:00Z",
        "requests": 647,
        "errors": 10,
        "p50_ms": 682,
        "p95_ms": 1279.2
      },
      {
        "ts": "2026-10-30T07:00:00Z",
        "requests": 616,
        "errors": 8,
        "p50_ms": 682,
        "p95_ms": 1137.98
      },
      {
        "ts": "2026-10-30T08:00:00Z",
        "requests": 643,
        "errors": 39,
        "p50_ms": 682,
        "p95_ms": 3004.92
      },
      {
        "ts": "2026-10-30T09:00:00Z",
        "requests": 724,
        "errors": 71,
        "p50_ms": 682,
        "p95_ms": 4831.42
      }
    ],
    "routes": [
      {
        "route": "/api/report",
        "requests": 100,
        "errors": 3,
        "avg_ms": 310,
        "p50_ms": 200,
        "p95_ms": 900
      }
    ]
  },
  "api/apps/forecast-studio/deps": {
    "deps": [
      {
        "dependency": "databricks_sql/wh-7d1a",
        "calls": 1320,
        "avg_ms": 150,
        "p95_ms": 560,
        "errors": 6
      }
    ]
  },
  "api/apps/forecast-studio/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/forecast-studio/security": {
    "scan": {
      "name": "forecast-studio",
      "quality_score": 69,
      "findings_critical": 0,
      "findings_high": 0,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 20,
      "py_loc": 1800,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-6",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": []}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/forecast-studio/review": {
    "review": {
      "name": "forecast-studio",
      "verdict": "approve",
      "score_overall": 8.5,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo web for Finance.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/forecast-studio/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 24.44,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 26.56,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 30.52,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 31.15,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 28.92,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 29.99,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 28.87,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 25.29,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 22.12,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 23.31,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 20.03,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 18.02,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 16.49,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 21.17,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 23.91,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 24.1,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 24.65,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 30.38,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 31.83,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 31.32,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 29.29,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 27.65,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 27.96,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 22.92,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 19.23,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 17.31,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 16.41,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 19.07,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 19.3,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 23.36,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      }
    ],
    "forecast": {
      "forecast_30d_usd": 835.07,
      "days_observed": 30
    },
    "budget": 1100,
    "mtd_usd": 735.54
  },
  "api/apps/forecast-studio/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "forecast-studio",
        "dbu_usd": 735.54,
        "ai_usd": 0,
        "total_usd": 735.54,
        "idle_usd": 44.88,
        "usd_per_1k_requests": 1.168,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/forecast-studio/genai": {
    "daily": [],
    "top": [],
    "error_taxonomy": [],
    "agent_steps": [],
    "quality": [],
    "feedback": [],
    "feedback_recent": []
  },
  "api/apps/forecast-studio/drift": {
    "reports": []
  },
  "api/apps/forecast-studio/analytics": {
    "daily": [
      {
        "date": "2026-10-24",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-25",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-26",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-27",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-28",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-29",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-30",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      }
    ],
    "users": [
      {
        "user_hash": "u_demo_91a",
        "first_seen": "2026-10-01",
        "last_seen": "2026-10-30T09:27:00Z",
        "requests": 80,
        "sessions": 10,
        "active_days": 7,
        "errors": 1,
        "tokens": 4000
      }
    ],
    "mtd_usd": 735.54
  },
  "api/apps/forecast-studio/events": {
    "events": [
      {
        "event_name": "answer_shown",
        "app_version": "1.16.3",
        "events": 40,
        "sessions": 32,
        "last_seen": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/forecast-studio/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": [
      {
        "funnel": "answer",
        "app_version": "1.16.3",
        "step_name": "ask_question",
        "sessions": 100,
        "dropoff_pct": 0
      },
      {
        "funnel": "answer",
        "app_version": "1.16.3",
        "step_name": "answer_shown",
        "sessions": 80,
        "dropoff_pct": 20
      }
    ]
  },
  "api/apps/forecast-studio/cohorts": {
    "cohorts": [
      {
        "cohort_week": "2026-10-19",
        "week_number": 1,
        "cohort_size": 40,
        "retained_users": 30,
        "retention_pct": 75,
        "partial_week": true
      }
    ]
  },
  "api/apps/forecast-studio/rum": {
    "routes": [
      {
        "date": "2026-10-30",
        "route": "/",
        "page_views": 200,
        "p75_lcp": 650,
        "p75_cls": 0.02,
        "p75_inp": 80,
        "js_errors": 1,
        "fingerprint": "rum-demo",
        "trace_id": "0000000000000000000000000000006a"
      }
    ]
  },
  "api/apps/forecast-studio/guardrails": {
    "findings": [],
    "templates": []
  },
  "api/apps/forecast-studio/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/forecast-studio/telemetry-health": {
    "health": {
      "quality": "healthy",
      "envelope_coverage": 0.9,
      "orphan_ratio_24h": 0.01,
      "sampler_ratio": 1,
      "last_span_at": "2026-10-30T09:27:00Z",
      "last_log_at": "2026-10-30T09:27:00Z",
      "last_metric_at": "2026-10-30T09:27:00Z",
      "semconv_legacy_only": 0,
      "semconv_stable_only": 0.1,
      "semconv_both": 0.9,
      "gateway_vs_otel_tokens": 12,
      "token_date": "2026-10-29"
    }
  },
  "api/apps/forecast-studio/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": -14.0,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": [
      {
        "slo": "availability",
        "date": "2026-10-10",
        "budget_remaining_pct": 100
      },
      {
        "slo": "availability",
        "date": "2026-10-11",
        "budget_remaining_pct": 80
      },
      {
        "slo": "availability",
        "date": "2026-10-12",
        "budget_remaining_pct": 60
      },
      {
        "slo": "availability",
        "date": "2026-10-13",
        "budget_remaining_pct": 40
      },
      {
        "slo": "availability",
        "date": "2026-10-14",
        "budget_remaining_pct": 20
      },
      {
        "slo": "availability",
        "date": "2026-10-15",
        "budget_remaining_pct": 0
      },
      {
        "slo": "availability",
        "date": "2026-10-16",
        "budget_remaining_pct": -20
      }
    ]
  },
  "api/apps/forecast-studio": {
    "uptime_24h": 99.43,
    "p95_ms": 234,
    "error_rate_1h": 0,
    "checks_24h": 1440,
    "compute_state": "ACTIVE",
    "last": {
      "code": 200,
      "ms": 120
    },
    "ttfb_ms": 110,
    "series": [
      [
        1793350800,
        true,
        200,
        120
      ],
      [
        1793350860,
        true,
        200,
        132
      ],
      [
        1793350920,
        true,
        200,
        144
      ],
      [
        1793350980,
        false,
        502,
        156
      ],
      [
        1793351040,
        true,
        200,
        168
      ],
      [
        1793351100,
        true,
        200,
        180
      ],
      [
        1793351160,
        true,
        200,
        192
      ],
      [
        1793351220,
        true,
        200,
        204
      ]
    ]
  },
  "api/apps/forecast-studio/synthetics": {
    "interval_s": 1800,
    "live": {
      "journey": "Report flow",
      "ok": true,
      "budget_ms": 2500,
      "within_budget": true,
      "ts": 1793352420,
      "steps": [
        {
          "name": "GET /api/report",
          "ok": true,
          "code": 200,
          "ms": 200,
          "detail": "Demo assertion"
        }
      ]
    },
    "browser": [
      {
        "run_ts": "2026-10-30T09:27:00Z",
        "journey": "browser-smoke",
        "ok": true,
        "status_code": 200,
        "latency_ms": 800,
        "detail": "Demo browser result",
        "vantage": "external",
        "failure_stage": null,
        "artifact": "/Volumes/demo/monitor/ui_tests/forecast-studio/run"
      }
    ]
  },
  "api/apps/forecast-studio/ops": {
    "config": {
      "tags_json": "{\"team\": \"Finance\", \"cost_center\": \"CC-120\", \"env\": \"prod\", \"tier\": \"t1\"}",
      "budget_usd_month": 1100,
      "auto_stop": "none",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "documents",
        "uc_securable": {
          "securable_full_name": "demo.claims.documents",
          "securable_type": "TABLE"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 320
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/console/trace/0000000000000000000000000000006b": {
    "trace_id": "0000000000000000000000000000006b",
    "app": "churn-explorer",
    "root": "GET /api/report",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "churn-explorer",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "churn-explorer",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "churn-explorer",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "churn-explorer",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "churn-explorer",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "churn-explorer",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "churn-explorer",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "churn-explorer",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/churn-explorer/logs": {
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0000000000000000000000000000006b"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0000000000000000000000000000006b"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006b"
      }
    ]
  },
  "api/apps/churn-explorer/errors": {
    "groups": [
      {
        "fingerprint": "demo-7",
        "occurrences": 19,
        "first_seen": "2026-10-30T09:27:00Z",
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "Demo dependency timeout"
      }
    ],
    "failed_requests": [
      {
        "trace_id": "0000000000000000000000000000006b",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ],
    "error_logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006b"
      }
    ]
  },
  "api/apps/churn-explorer/traces": {
    "traces": [
      {
        "trace_id": "0000000000000000000000000000006b",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/churn-explorer/agent-traces": {
    "experiment": null,
    "traces": []
  },
  "api/apps/churn-explorer/agent-traces/tr-demo-7": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-7",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "churn-explorer",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "churn-explorer",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "churn-explorer",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "churn-explorer",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "churn-explorer",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "churn-explorer",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "churn-explorer",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "churn-explorer",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0000000000000000000000000000006b"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0000000000000000000000000000006b"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006b"
      }
    ]
  },
  "api/apps/churn-explorer/requests": {
    "timeline": [
      {
        "ts": "2026-10-29T10:00:00Z",
        "requests": 1878,
        "errors": 3,
        "p50_ms": 98,
        "p95_ms": 233.4
      },
      {
        "ts": "2026-10-29T11:00:00Z",
        "requests": 1909,
        "errors": 5,
        "p50_ms": 98,
        "p95_ms": 221.53
      },
      {
        "ts": "2026-10-29T12:00:00Z",
        "requests": 2246,
        "errors": 7,
        "p50_ms": 98,
        "p95_ms": 267.15
      },
      {
        "ts": "2026-10-29T13:00:00Z",
        "requests": 2205,
        "errors": 5,
        "p50_ms": 98,
        "p95_ms": 271.69
      },
      {
        "ts": "2026-10-29T14:00:00Z",
        "requests": 2218,
        "errors": 7,
        "p50_ms": 98,
        "p95_ms": 268.63
      },
      {
        "ts": "2026-10-29T15:00:00Z",
        "requests": 1830,
        "errors": 4,
        "p50_ms": 98,
        "p95_ms": 231.67
      },
      {
        "ts": "2026-10-29T16:00:00Z",
        "requests": 1830,
        "errors": 5,
        "p50_ms": 98,
        "p95_ms": 210.9
      },
      {
        "ts": "2026-10-29T17:00:00Z",
        "requests": 1418,
        "errors": 4,
        "p50_ms": 98,
        "p95_ms": 192.75
      },
      {
        "ts": "2026-10-29T18:00:00Z",
        "requests": 1323,
        "errors": 3,
        "p50_ms": 98,
        "p95_ms": 164.61
      },
      {
        "ts": "2026-10-29T19:00:00Z",
        "requests": 1418,
        "errors": 2,
        "p50_ms": 98,
        "p95_ms": 169.95
      },
      {
        "ts": "2026-10-29T20:00:00Z",
        "requests": 1470,
        "errors": 3,
        "p50_ms": 98,
        "p95_ms": 165.75
      },
      {
        "ts": "2026-10-29T21:00:00Z",
        "requests": 1405,
        "errors": 3,
        "p50_ms": 98,
        "p95_ms": 184.98
      },
      {
        "ts": "2026-10-29T22:00:00Z",
        "requests": 1633,
        "errors": 5,
        "p50_ms": 98,
        "p95_ms": 189.56
      },
      {
        "ts": "2026-10-29T23:00:00Z",
        "requests": 1913,
        "errors": 4,
        "p50_ms": 98,
        "p95_ms": 248.5
      },
      {
        "ts": "2026-10-30T00:00:00Z",
        "requests": 2112,
        "errors": 8,
        "p50_ms": 98,
        "p95_ms": 261.23
      },
      {
        "ts": "2026-10-30T01:00:00Z",
        "requests": 2123,
        "errors": 8,
        "p50_ms": 98,
        "p95_ms": 254.76
      },
      {
        "ts": "2026-10-30T02:00:00Z",
        "requests": 1975,
        "errors": 7,
        "p50_ms": 98,
        "p95_ms": 275.97
      },
      {
        "ts": "2026-10-30T03:00:00Z",
        "requests": 1860,
        "errors": 6,
        "p50_ms": 98,
        "p95_ms": 257.16
      },
      {
        "ts": "2026-10-30T04:00:00Z",
        "requests": 1809,
        "errors": 4,
        "p50_ms": 98,
        "p95_ms": 212.96
      },
      {
        "ts": "2026-10-30T05:00:00Z",
        "requests": 1652,
        "errors": 5,
        "p50_ms": 98,
        "p95_ms": 171.06
      },
      {
        "ts": "2026-10-30T06:00:00Z",
        "requests": 1197,
        "errors": 2,
        "p50_ms": 98,
        "p95_ms": 167.17
      },
      {
        "ts": "2026-10-30T07:00:00Z",
        "requests": 1320,
        "errors": 3,
        "p50_ms": 98,
        "p95_ms": 140.26
      },
      {
        "ts": "2026-10-30T08:00:00Z",
        "requests": 1445,
        "errors": 4,
        "p50_ms": 98,
        "p95_ms": 148.62
      },
      {
        "ts": "2026-10-30T09:00:00Z",
        "requests": 1355,
        "errors": 2,
        "p50_ms": 98,
        "p95_ms": 184.57
      }
    ],
    "routes": [
      {
        "route": "/api/report",
        "requests": 100,
        "errors": 3,
        "avg_ms": 310,
        "p50_ms": 200,
        "p95_ms": 900
      }
    ]
  },
  "api/apps/churn-explorer/deps": {
    "deps": [
      {
        "dependency": "databricks_sql/wh-7d1a",
        "calls": 1340,
        "avg_ms": 150,
        "p95_ms": 560,
        "errors": 7
      }
    ]
  },
  "api/apps/churn-explorer/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/churn-explorer/security": {
    "scan": {
      "name": "churn-explorer",
      "quality_score": 85,
      "findings_critical": 0,
      "findings_high": 0,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 21,
      "py_loc": 1900,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-7",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": []}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/churn-explorer/review": {
    "review": {
      "name": "churn-explorer",
      "verdict": "approve_with_comments",
      "score_overall": 8.8,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo web for Marketing.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/churn-explorer/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 12.7,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 14.9,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 17.2,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 16.26,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 18.46,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 16.29,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 16.82,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 13.63,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 13.19,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 13.03,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 10.08,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 9.79,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 10.61,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 10.82,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 11.2,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 13.02,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 14.38,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 17.7,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 17.71,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 18.46,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 15.99,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 16.74,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 13.56,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 13.27,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 12.24,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 10.5,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 11.48,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 10.75,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 11.54,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 13.55,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      }
    ],
    "forecast": {
      "forecast_30d_usd": 529.78,
      "days_observed": 30
    },
    "budget": 700,
    "mtd_usd": 417.1
  },
  "api/apps/churn-explorer/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "churn-explorer",
        "dbu_usd": 417.1,
        "ai_usd": 0,
        "total_usd": 417.1,
        "idle_usd": 135.95,
        "usd_per_1k_requests": 0.335,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/churn-explorer/genai": {
    "daily": [],
    "top": [],
    "error_taxonomy": [],
    "agent_steps": [],
    "quality": [],
    "feedback": [],
    "feedback_recent": []
  },
  "api/apps/churn-explorer/drift": {
    "reports": []
  },
  "api/apps/churn-explorer/analytics": {
    "daily": [
      {
        "date": "2026-10-24",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-25",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-26",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-27",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-28",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-29",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-30",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      }
    ],
    "users": [
      {
        "user_hash": "u_demo_91a",
        "first_seen": "2026-10-01",
        "last_seen": "2026-10-30T09:27:00Z",
        "requests": 80,
        "sessions": 10,
        "active_days": 7,
        "errors": 1,
        "tokens": 4000
      }
    ],
    "mtd_usd": 417.1
  },
  "api/apps/churn-explorer/events": {
    "events": [
      {
        "event_name": "answer_shown",
        "app_version": "1.3.6",
        "events": 40,
        "sessions": 32,
        "last_seen": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/churn-explorer/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": [
      {
        "funnel": "answer",
        "app_version": "1.3.6",
        "step_name": "ask_question",
        "sessions": 100,
        "dropoff_pct": 0
      },
      {
        "funnel": "answer",
        "app_version": "1.3.6",
        "step_name": "answer_shown",
        "sessions": 80,
        "dropoff_pct": 20
      }
    ]
  },
  "api/apps/churn-explorer/cohorts": {
    "cohorts": [
      {
        "cohort_week": "2026-10-19",
        "week_number": 1,
        "cohort_size": 40,
        "retained_users": 30,
        "retention_pct": 75,
        "partial_week": true
      }
    ]
  },
  "api/apps/churn-explorer/rum": {
    "routes": [
      {
        "date": "2026-10-30",
        "route": "/",
        "page_views": 200,
        "p75_lcp": 650,
        "p75_cls": 0.02,
        "p75_inp": 80,
        "js_errors": 1,
        "fingerprint": "rum-demo",
        "trace_id": "0000000000000000000000000000006b"
      }
    ]
  },
  "api/apps/churn-explorer/guardrails": {
    "findings": [],
    "templates": []
  },
  "api/apps/churn-explorer/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/churn-explorer/telemetry-health": {
    "health": {
      "quality": "healthy",
      "envelope_coverage": 0.9,
      "orphan_ratio_24h": 0.01,
      "sampler_ratio": 1,
      "last_span_at": "2026-10-30T09:27:00Z",
      "last_log_at": "2026-10-30T09:27:00Z",
      "last_metric_at": "2026-10-30T09:27:00Z",
      "semconv_legacy_only": 0,
      "semconv_stable_only": 0.1,
      "semconv_both": 0.9,
      "gateway_vs_otel_tokens": 12,
      "token_date": "2026-10-29"
    }
  },
  "api/apps/churn-explorer/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": 95.2,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": [
      {
        "slo": "availability",
        "date": "2026-10-10",
        "budget_remaining_pct": 100
      },
      {
        "slo": "availability",
        "date": "2026-10-11",
        "budget_remaining_pct": 80
      },
      {
        "slo": "availability",
        "date": "2026-10-12",
        "budget_remaining_pct": 60
      },
      {
        "slo": "availability",
        "date": "2026-10-13",
        "budget_remaining_pct": 40
      },
      {
        "slo": "availability",
        "date": "2026-10-14",
        "budget_remaining_pct": 20
      },
      {
        "slo": "availability",
        "date": "2026-10-15",
        "budget_remaining_pct": 0
      },
      {
        "slo": "availability",
        "date": "2026-10-16",
        "budget_remaining_pct": -20
      }
    ]
  },
  "api/apps/churn-explorer": {
    "uptime_24h": 99.976,
    "p95_ms": 243,
    "error_rate_1h": 0,
    "checks_24h": 1440,
    "compute_state": "ACTIVE",
    "last": {
      "code": 200,
      "ms": 120
    },
    "ttfb_ms": 110,
    "series": [
      [
        1793350800,
        true,
        200,
        120
      ],
      [
        1793350860,
        true,
        200,
        132
      ],
      [
        1793350920,
        true,
        200,
        144
      ],
      [
        1793350980,
        false,
        502,
        156
      ],
      [
        1793351040,
        true,
        200,
        168
      ],
      [
        1793351100,
        true,
        200,
        180
      ],
      [
        1793351160,
        true,
        200,
        192
      ],
      [
        1793351220,
        true,
        200,
        204
      ]
    ]
  },
  "api/apps/churn-explorer/synthetics": {
    "interval_s": 1800,
    "live": {
      "journey": "Report flow",
      "ok": true,
      "budget_ms": 2500,
      "within_budget": true,
      "ts": 1793352420,
      "steps": [
        {
          "name": "GET /api/report",
          "ok": true,
          "code": 200,
          "ms": 200,
          "detail": "Demo assertion"
        }
      ]
    },
    "browser": [
      {
        "run_ts": "2026-10-30T09:27:00Z",
        "journey": "browser-smoke",
        "ok": true,
        "status_code": 200,
        "latency_ms": 800,
        "detail": "Demo browser result",
        "vantage": "external",
        "failure_stage": null,
        "artifact": "/Volumes/demo/monitor/ui_tests/churn-explorer/run"
      }
    ]
  },
  "api/apps/churn-explorer/ops": {
    "config": {
      "tags_json": "{\"team\": \"Marketing\", \"cost_center\": \"CC-140\", \"env\": \"prod\", \"tier\": \"t1\"}",
      "budget_usd_month": 700,
      "auto_stop": "idle",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "credentials",
        "secret": {
          "scope": "app-secrets",
          "key": "api-key"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 320
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/console/trace/0000000000000000000000000000006c": {
    "trace_id": "0000000000000000000000000000006c",
    "app": "doc-intake",
    "root": "GET /api/report",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "doc-intake",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "doc-intake",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "doc-intake",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "doc-intake",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "doc-intake",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "doc-intake",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "doc-intake",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "doc-intake",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/doc-intake/logs": {
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0000000000000000000000000000006c"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0000000000000000000000000000006c"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006c"
      }
    ]
  },
  "api/apps/doc-intake/errors": {
    "groups": [
      {
        "fingerprint": "demo-8",
        "occurrences": 20,
        "first_seen": "2026-10-30T09:27:00Z",
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "Demo dependency timeout"
      }
    ],
    "failed_requests": [
      {
        "trace_id": "0000000000000000000000000000006c",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ],
    "error_logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006c"
      }
    ]
  },
  "api/apps/doc-intake/traces": {
    "traces": [
      {
        "trace_id": "0000000000000000000000000000006c",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/doc-intake/agent-traces": {
    "experiment": null,
    "traces": []
  },
  "api/apps/doc-intake/agent-traces/tr-demo-8": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-8",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "doc-intake",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "doc-intake",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "doc-intake",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "doc-intake",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "doc-intake",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "doc-intake",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "doc-intake",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "doc-intake",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0000000000000000000000000000006c"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0000000000000000000000000000006c"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006c"
      }
    ]
  },
  "api/apps/doc-intake/requests": {
    "timeline": [
      {
        "ts": "2026-10-29T10:00:00Z",
        "requests": 1204,
        "errors": 3,
        "p50_ms": 109,
        "p95_ms": 221.6
      },
      {
        "ts": "2026-10-29T11:00:00Z",
        "requests": 1302,
        "errors": 4,
        "p50_ms": 109,
        "p95_ms": 227.15
      },
      {
        "ts": "2026-10-29T12:00:00Z",
        "requests": 1396,
        "errors": 4,
        "p50_ms": 109,
        "p95_ms": 275.45
      },
      {
        "ts": "2026-10-29T13:00:00Z",
        "requests": 1361,
        "errors": 4,
        "p50_ms": 109,
        "p95_ms": 290.85
      },
      {
        "ts": "2026-10-29T14:00:00Z",
        "requests": 1426,
        "errors": 4,
        "p50_ms": 109,
        "p95_ms": 235.26
      },
      {
        "ts": "2026-10-29T15:00:00Z",
        "requests": 1347,
        "errors": 4,
        "p50_ms": 109,
        "p95_ms": 256.47
      },
      {
        "ts": "2026-10-29T16:00:00Z",
        "requests": 1067,
        "errors": 2,
        "p50_ms": 109,
        "p95_ms": 233.69
      },
      {
        "ts": "2026-10-29T17:00:00Z",
        "requests": 923,
        "errors": 2,
        "p50_ms": 109,
        "p95_ms": 191.24
      },
      {
        "ts": "2026-10-29T18:00:00Z",
        "requests": 936,
        "errors": 2,
        "p50_ms": 109,
        "p95_ms": 170.9
      },
      {
        "ts": "2026-10-29T19:00:00Z",
        "requests": 835,
        "errors": 2,
        "p50_ms": 109,
        "p95_ms": 165.02
      },
      {
        "ts": "2026-10-29T20:00:00Z",
        "requests": 925,
        "errors": 2,
        "p50_ms": 109,
        "p95_ms": 167.66
      },
      {
        "ts": "2026-10-29T21:00:00Z",
        "requests": 1035,
        "errors": 2,
        "p50_ms": 109,
        "p95_ms": 185.82
      },
      {
        "ts": "2026-10-29T22:00:00Z",
        "requests": 1154,
        "errors": 2,
        "p50_ms": 109,
        "p95_ms": 194.98
      },
      {
        "ts": "2026-10-29T23:00:00Z",
        "requests": 1274,
        "errors": 3,
        "p50_ms": 109,
        "p95_ms": 212.82
      },
      {
        "ts": "2026-10-30T00:00:00Z",
        "requests": 1342,
        "errors": 5,
        "p50_ms": 109,
        "p95_ms": 235.55
      },
      {
        "ts": "2026-10-30T01:00:00Z",
        "requests": 1436,
        "errors": 3,
        "p50_ms": 109,
        "p95_ms": 240.74
      },
      {
        "ts": "2026-10-30T02:00:00Z",
        "requests": 1505,
        "errors": 5,
        "p50_ms": 109,
        "p95_ms": 242.15
      },
      {
        "ts": "2026-10-30T03:00:00Z",
        "requests": 1241,
        "errors": 3,
        "p50_ms": 109,
        "p95_ms": 221.27
      },
      {
        "ts": "2026-10-30T04:00:00Z",
        "requests": 1060,
        "errors": 3,
        "p50_ms": 109,
        "p95_ms": 234.7
      },
      {
        "ts": "2026-10-30T05:00:00Z",
        "requests": 1098,
        "errors": 2,
        "p50_ms": 109,
        "p95_ms": 165.18
      },
      {
        "ts": "2026-10-30T06:00:00Z",
        "requests": 969,
        "errors": 2,
        "p50_ms": 109,
        "p95_ms": 172.72
      },
      {
        "ts": "2026-10-30T07:00:00Z",
        "requests": 869,
        "errors": 1,
        "p50_ms": 109,
        "p95_ms": 167.94
      },
      {
        "ts": "2026-10-30T08:00:00Z",
        "requests": 817,
        "errors": 2,
        "p50_ms": 109,
        "p95_ms": 150.62
      },
      {
        "ts": "2026-10-30T09:00:00Z",
        "requests": 944,
        "errors": 3,
        "p50_ms": 109,
        "p95_ms": 181.58
      }
    ],
    "routes": [
      {
        "route": "/api/report",
        "requests": 100,
        "errors": 3,
        "avg_ms": 310,
        "p50_ms": 200,
        "p95_ms": 900
      }
    ]
  },
  "api/apps/doc-intake/deps": {
    "deps": [
      {
        "dependency": "databricks_sql/wh-7d1a",
        "calls": 1360,
        "avg_ms": 150,
        "p95_ms": 560,
        "errors": 8
      }
    ]
  },
  "api/apps/doc-intake/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/doc-intake/security": {
    "scan": {
      "name": "doc-intake",
      "quality_score": 73,
      "findings_critical": 0,
      "findings_high": 0,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 22,
      "py_loc": 2000,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-8",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": []}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/doc-intake/review": {
    "review": {
      "name": "doc-intake",
      "verdict": "approve",
      "score_overall": 9.3,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo api for Claims.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/doc-intake/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 12.27,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 15.21,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 16.46,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 17.18,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 17.95,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 17.67,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 14.91,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 15.33,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 13.84,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 10.38,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 10.58,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 9.24,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 11.36,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 11.89,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 11.3,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 12.56,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 15.97,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 15.15,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 16.38,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 17.1,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 16.07,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 16.41,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 15.31,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 14.07,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 12.42,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 10.66,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 10.05,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 10.35,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 9.64,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 10.83,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      }
    ],
    "forecast": {
      "forecast_30d_usd": 429.88,
      "days_observed": 30
    },
    "budget": 800,
    "mtd_usd": 358.39
  },
  "api/apps/doc-intake/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "doc-intake",
        "dbu_usd": 358.39,
        "ai_usd": 45.9,
        "total_usd": 404.29,
        "idle_usd": 136.19,
        "usd_per_1k_requests": 0.478,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/doc-intake/genai": {
    "daily": [],
    "top": [],
    "error_taxonomy": [],
    "agent_steps": [],
    "quality": [],
    "feedback": [],
    "feedback_recent": []
  },
  "api/apps/doc-intake/drift": {
    "reports": []
  },
  "api/apps/doc-intake/analytics": {
    "daily": [
      {
        "date": "2026-10-24",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-25",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-26",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-27",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-28",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-29",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-30",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      }
    ],
    "users": [
      {
        "user_hash": "u_demo_91a",
        "first_seen": "2026-10-01",
        "last_seen": "2026-10-30T09:27:00Z",
        "requests": 80,
        "sessions": 10,
        "active_days": 7,
        "errors": 1,
        "tokens": 4000
      }
    ],
    "mtd_usd": 358.39
  },
  "api/apps/doc-intake/events": {
    "events": [
      {
        "event_name": "answer_shown",
        "app_version": "3.9.9",
        "events": 40,
        "sessions": 32,
        "last_seen": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/doc-intake/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": [
      {
        "funnel": "answer",
        "app_version": "3.9.9",
        "step_name": "ask_question",
        "sessions": 100,
        "dropoff_pct": 0
      },
      {
        "funnel": "answer",
        "app_version": "3.9.9",
        "step_name": "answer_shown",
        "sessions": 80,
        "dropoff_pct": 20
      }
    ]
  },
  "api/apps/doc-intake/cohorts": {
    "cohorts": [
      {
        "cohort_week": "2026-10-19",
        "week_number": 1,
        "cohort_size": 40,
        "retained_users": 30,
        "retention_pct": 75,
        "partial_week": true
      }
    ]
  },
  "api/apps/doc-intake/rum": {
    "routes": [
      {
        "date": "2026-10-30",
        "route": "/",
        "page_views": 200,
        "p75_lcp": 650,
        "p75_cls": 0.02,
        "p75_inp": 80,
        "js_errors": 1,
        "fingerprint": "rum-demo",
        "trace_id": "0000000000000000000000000000006c"
      }
    ]
  },
  "api/apps/doc-intake/guardrails": {
    "findings": [],
    "templates": []
  },
  "api/apps/doc-intake/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/doc-intake/telemetry-health": {
    "health": {
      "quality": "healthy",
      "envelope_coverage": 0.9,
      "orphan_ratio_24h": 0.01,
      "sampler_ratio": 1,
      "last_span_at": "2026-10-30T09:27:00Z",
      "last_log_at": "2026-10-30T09:27:00Z",
      "last_metric_at": "2026-10-30T09:27:00Z",
      "semconv_legacy_only": 0,
      "semconv_stable_only": 0.1,
      "semconv_both": 0.9,
      "gateway_vs_otel_tokens": 12,
      "token_date": "2026-10-29"
    }
  },
  "api/apps/doc-intake/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": 52.0,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": [
      {
        "slo": "availability",
        "date": "2026-10-10",
        "budget_remaining_pct": 100
      },
      {
        "slo": "availability",
        "date": "2026-10-11",
        "budget_remaining_pct": 80
      },
      {
        "slo": "availability",
        "date": "2026-10-12",
        "budget_remaining_pct": 60
      },
      {
        "slo": "availability",
        "date": "2026-10-13",
        "budget_remaining_pct": 40
      },
      {
        "slo": "availability",
        "date": "2026-10-14",
        "budget_remaining_pct": 20
      },
      {
        "slo": "availability",
        "date": "2026-10-15",
        "budget_remaining_pct": 0
      },
      {
        "slo": "availability",
        "date": "2026-10-16",
        "budget_remaining_pct": -20
      }
    ]
  },
  "api/apps/doc-intake": {
    "uptime_24h": 99.952,
    "p95_ms": 252,
    "error_rate_1h": 0,
    "checks_24h": 1440,
    "compute_state": "ACTIVE",
    "last": {
      "code": 200,
      "ms": 120
    },
    "ttfb_ms": 110,
    "series": [
      [
        1793350800,
        true,
        200,
        120
      ],
      [
        1793350860,
        true,
        200,
        132
      ],
      [
        1793350920,
        true,
        200,
        144
      ],
      [
        1793350980,
        false,
        502,
        156
      ],
      [
        1793351040,
        true,
        200,
        168
      ],
      [
        1793351100,
        true,
        200,
        180
      ],
      [
        1793351160,
        true,
        200,
        192
      ],
      [
        1793351220,
        true,
        200,
        204
      ]
    ]
  },
  "api/apps/doc-intake/synthetics": {
    "interval_s": 1800,
    "live": {
      "journey": "Report flow",
      "ok": true,
      "budget_ms": 2500,
      "within_budget": true,
      "ts": 1793352420,
      "steps": [
        {
          "name": "GET /api/report",
          "ok": true,
          "code": 200,
          "ms": 200,
          "detail": "Demo assertion"
        }
      ]
    },
    "browser": [
      {
        "run_ts": "2026-10-30T09:27:00Z",
        "journey": "browser-smoke",
        "ok": true,
        "status_code": 200,
        "latency_ms": 800,
        "detail": "Demo browser result",
        "vantage": "external",
        "failure_stage": null,
        "artifact": "/Volumes/demo/monitor/ui_tests/doc-intake/run"
      }
    ]
  },
  "api/apps/doc-intake/ops": {
    "config": {
      "tags_json": "{\"team\": \"Claims\", \"cost_center\": \"CC-410\", \"env\": \"prod\", \"tier\": \"t1\"}",
      "budget_usd_month": 800,
      "auto_stop": "night",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "analytics",
        "genie_space": {
          "id": "genie-demo"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 320
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/console/trace/0000000000000000000000000000006d": {
    "trace_id": "0000000000000000000000000000006d",
    "app": "ops-runbook-bot",
    "root": "GET /api/report",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "ops-runbook-bot",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "ops-runbook-bot",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "ops-runbook-bot",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "ops-runbook-bot",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "ops-runbook-bot",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "ops-runbook-bot",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "ops-runbook-bot",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "ops-runbook-bot",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/ops-runbook-bot/logs": {
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0000000000000000000000000000006d"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0000000000000000000000000000006d"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006d"
      }
    ]
  },
  "api/apps/ops-runbook-bot/errors": {
    "groups": [
      {
        "fingerprint": "demo-9",
        "occurrences": 21,
        "first_seen": "2026-10-30T09:27:00Z",
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "Demo dependency timeout"
      }
    ],
    "failed_requests": [
      {
        "trace_id": "0000000000000000000000000000006d",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ],
    "error_logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006d"
      }
    ]
  },
  "api/apps/ops-runbook-bot/traces": {
    "traces": [
      {
        "trace_id": "0000000000000000000000000000006d",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/ops-runbook-bot/agent-traces": {
    "experiment": "201",
    "traces": [
      {
        "trace_id": "tr-demo-9",
        "request_time": "2026-10-30T09:27:00Z",
        "duration_ms": 6420,
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested",
        "client_request_id": "demo-request",
        "tags": {
          "agent": "coverage"
        }
      }
    ]
  },
  "api/apps/ops-runbook-bot/agent-traces/tr-demo-9": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-9",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "ops-runbook-bot",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "ops-runbook-bot",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "ops-runbook-bot",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "ops-runbook-bot",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "ops-runbook-bot",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "ops-runbook-bot",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "ops-runbook-bot",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "ops-runbook-bot",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0000000000000000000000000000006d"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0000000000000000000000000000006d"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006d"
      }
    ]
  },
  "api/apps/ops-runbook-bot/requests": {
    "timeline": [
      {
        "ts": "2026-10-29T10:00:00Z",
        "requests": 675,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 139.75
      },
      {
        "ts": "2026-10-29T11:00:00Z",
        "requests": 755,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 159.31
      },
      {
        "ts": "2026-10-29T12:00:00Z",
        "requests": 822,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 189.04
      },
      {
        "ts": "2026-10-29T13:00:00Z",
        "requests": 739,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 181.09
      },
      {
        "ts": "2026-10-29T14:00:00Z",
        "requests": 819,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 174.35
      },
      {
        "ts": "2026-10-29T15:00:00Z",
        "requests": 767,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 184.66
      },
      {
        "ts": "2026-10-29T16:00:00Z",
        "requests": 692,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 148.94
      },
      {
        "ts": "2026-10-29T17:00:00Z",
        "requests": 506,
        "errors": 0,
        "p50_ms": 55,
        "p95_ms": 143.27
      },
      {
        "ts": "2026-10-29T18:00:00Z",
        "requests": 460,
        "errors": 0,
        "p50_ms": 55,
        "p95_ms": 120.98
      },
      {
        "ts": "2026-10-29T19:00:00Z",
        "requests": 427,
        "errors": 0,
        "p50_ms": 55,
        "p95_ms": 94.15
      },
      {
        "ts": "2026-10-29T20:00:00Z",
        "requests": 438,
        "errors": 0,
        "p50_ms": 55,
        "p95_ms": 113.34
      },
      {
        "ts": "2026-10-29T21:00:00Z",
        "requests": 600,
        "errors": 0,
        "p50_ms": 55,
        "p95_ms": 127.84
      },
      {
        "ts": "2026-10-29T22:00:00Z",
        "requests": 675,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 158.96
      },
      {
        "ts": "2026-10-29T23:00:00Z",
        "requests": 732,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 161.7
      },
      {
        "ts": "2026-10-30T00:00:00Z",
        "requests": 814,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 188.63
      },
      {
        "ts": "2026-10-30T01:00:00Z",
        "requests": 811,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 187.41
      },
      {
        "ts": "2026-10-30T02:00:00Z",
        "requests": 746,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 170.47
      },
      {
        "ts": "2026-10-30T03:00:00Z",
        "requests": 664,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 180.88
      },
      {
        "ts": "2026-10-30T04:00:00Z",
        "requests": 584,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 133.58
      },
      {
        "ts": "2026-10-30T05:00:00Z",
        "requests": 588,
        "errors": 1,
        "p50_ms": 55,
        "p95_ms": 142.1
      },
      {
        "ts": "2026-10-30T06:00:00Z",
        "requests": 460,
        "errors": 0,
        "p50_ms": 55,
        "p95_ms": 104.32
      },
      {
        "ts": "2026-10-30T07:00:00Z",
        "requests": 453,
        "errors": 0,
        "p50_ms": 55,
        "p95_ms": 93.05
      },
      {
        "ts": "2026-10-30T08:00:00Z",
        "requests": 488,
        "errors": 0,
        "p50_ms": 55,
        "p95_ms": 105.5
      },
      {
        "ts": "2026-10-30T09:00:00Z",
        "requests": 495,
        "errors": 0,
        "p50_ms": 55,
        "p95_ms": 139.95
      }
    ],
    "routes": [
      {
        "route": "/api/report",
        "requests": 100,
        "errors": 3,
        "avg_ms": 310,
        "p50_ms": 200,
        "p95_ms": 900
      }
    ]
  },
  "api/apps/ops-runbook-bot/deps": {
    "deps": [
      {
        "dependency": "databricks_sql/wh-7d1a",
        "calls": 1380,
        "avg_ms": 150,
        "p95_ms": 560,
        "errors": 9
      }
    ]
  },
  "api/apps/ops-runbook-bot/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/ops-runbook-bot/security": {
    "scan": {
      "name": "ops-runbook-bot",
      "quality_score": 69,
      "findings_critical": 0,
      "findings_high": 0,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 23,
      "py_loc": 2100,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-9",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": []}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/ops-runbook-bot/review": {
    "review": {
      "name": "ops-runbook-bot",
      "verdict": "approve_with_comments",
      "score_overall": 9.4,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo agent for Platform.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/ops-runbook-bot/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 25.7,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 33.36,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 31.23,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 34.08,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 35.06,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 38.04,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 34.07,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 30.87,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 30.84,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 24.56,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 23.93,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 23.55,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 25.35,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 27.2,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 29.52,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 31.38,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 34.84,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 36.95,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 42.85,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 42.55,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 42.26,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 37.04,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 35.62,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 34.21,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 30.08,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 25.35,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 26.32,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 29.28,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 27.74,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 30.74,
        "ai_calls": 20,
        "ai_input_tokens": 1200,
        "ai_output_tokens": 200
      }
    ],
    "forecast": {
      "forecast_30d_usd": 1057.29,
      "days_observed": 30
    },
    "budget": 1400,
    "mtd_usd": 451.02
  },
  "api/apps/ops-runbook-bot/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "ops-runbook-bot",
        "dbu_usd": 451.02,
        "ai_usd": 389.64,
        "total_usd": 840.66,
        "idle_usd": 84.84,
        "usd_per_1k_requests": 1.838,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/ops-runbook-bot/genai": {
    "daily": [
      {
        "date": "2026-10-01",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-02",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-03",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-04",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-05",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-06",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-07",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-08",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-09",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-10",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-11",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-12",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-13",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-14",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-15",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-16",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-17",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-18",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-19",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-20",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-21",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-22",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-23",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-24",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-25",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-26",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-27",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-28",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-29",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      },
      {
        "date": "2026-10-30",
        "model": "claims-model",
        "calls": 20,
        "input_tokens": 1200,
        "output_tokens": 200,
        "errors": 1,
        "p95_ms": 900
      }
    ],
    "top": [
      {
        "session_id": "hashed-session",
        "user_hash": "hashed-user",
        "calls": 10,
        "tokens": 4000,
        "last_call": "2026-10-30T09:27:00Z"
      }
    ],
    "error_taxonomy": [
      {
        "category": "rate_limit",
        "errors": 3,
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "429 upstream"
      }
    ],
    "agent_steps": [
      {
        "date": "2026-10-29",
        "avg_steps": 5,
        "max_steps": 8,
        "agent_runs": 32
      },
      {
        "date": "2026-10-30",
        "avg_steps": 7,
        "max_steps": 12,
        "agent_runs": 40
      }
    ],
    "quality": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "relevance": 8,
        "faithfulness": 7,
        "toxicity": 0,
        "traces_sampled": 10,
        "comment": "Demo sampled evaluation"
      }
    ],
    "feedback": [
      {
        "date": "2026-10-30",
        "n": 10,
        "avg_rating": 4.2,
        "negative": 1
      }
    ],
    "feedback_recent": []
  },
  "api/apps/ops-runbook-bot/drift": {
    "reports": [
      {
        "week": "2026-10-26",
        "samples": 60,
        "k": 3,
        "silhouette": 0.6,
        "novel_share": 0.31
      }
    ]
  },
  "api/apps/ops-runbook-bot/analytics": {
    "daily": [
      {
        "date": "2026-10-24",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-25",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-26",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-27",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-28",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-29",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-30",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      }
    ],
    "users": [
      {
        "user_hash": "u_demo_91a",
        "first_seen": "2026-10-01",
        "last_seen": "2026-10-30T09:27:00Z",
        "requests": 80,
        "sessions": 10,
        "active_days": 7,
        "errors": 1,
        "tokens": 4000
      }
    ],
    "mtd_usd": 451.02
  },
  "api/apps/ops-runbook-bot/events": {
    "events": [
      {
        "event_name": "answer_shown",
        "app_version": "1.4.0",
        "events": 40,
        "sessions": 32,
        "last_seen": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/ops-runbook-bot/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": [
      {
        "funnel": "answer",
        "app_version": "1.4.0",
        "step_name": "ask_question",
        "sessions": 100,
        "dropoff_pct": 0
      },
      {
        "funnel": "answer",
        "app_version": "1.4.0",
        "step_name": "answer_shown",
        "sessions": 80,
        "dropoff_pct": 20
      }
    ]
  },
  "api/apps/ops-runbook-bot/cohorts": {
    "cohorts": [
      {
        "cohort_week": "2026-10-19",
        "week_number": 1,
        "cohort_size": 40,
        "retained_users": 30,
        "retention_pct": 75,
        "partial_week": true
      }
    ]
  },
  "api/apps/ops-runbook-bot/rum": {
    "routes": [
      {
        "date": "2026-10-30",
        "route": "/",
        "page_views": 200,
        "p75_lcp": 650,
        "p75_cls": 0.02,
        "p75_inp": 80,
        "js_errors": 1,
        "fingerprint": "rum-demo",
        "trace_id": "0000000000000000000000000000006d"
      }
    ]
  },
  "api/apps/ops-runbook-bot/guardrails": {
    "findings": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "kind": "pii",
        "severity": "warning",
        "excerpt_masked": "[EMAIL]",
        "excerpt_hash": "demo-hash",
        "trace_id": "tr-demo-9"
      }
    ],
    "templates": [
      {
        "date": "2026-10-30",
        "template_hash": "template-demo",
        "samples": 12,
        "daily_samples": 40,
        "share": 0.3
      }
    ]
  },
  "api/apps/ops-runbook-bot/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/ops-runbook-bot/telemetry-health": {
    "health": {
      "quality": "healthy",
      "envelope_coverage": 0.9,
      "orphan_ratio_24h": 0.01,
      "sampler_ratio": 1,
      "last_span_at": "2026-10-30T09:27:00Z",
      "last_log_at": "2026-10-30T09:27:00Z",
      "last_metric_at": "2026-10-30T09:27:00Z",
      "semconv_legacy_only": 0,
      "semconv_stable_only": 0.1,
      "semconv_both": 0.9,
      "gateway_vs_otel_tokens": 12,
      "token_date": "2026-10-29"
    }
  },
  "api/apps/ops-runbook-bot/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": 90.2,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": [
      {
        "slo": "availability",
        "date": "2026-10-10",
        "budget_remaining_pct": 100
      },
      {
        "slo": "availability",
        "date": "2026-10-11",
        "budget_remaining_pct": 80
      },
      {
        "slo": "availability",
        "date": "2026-10-12",
        "budget_remaining_pct": 60
      },
      {
        "slo": "availability",
        "date": "2026-10-13",
        "budget_remaining_pct": 40
      },
      {
        "slo": "availability",
        "date": "2026-10-14",
        "budget_remaining_pct": 20
      },
      {
        "slo": "availability",
        "date": "2026-10-15",
        "budget_remaining_pct": 0
      },
      {
        "slo": "availability",
        "date": "2026-10-16",
        "budget_remaining_pct": -20
      }
    ]
  },
  "api/apps/ops-runbook-bot": {
    "uptime_24h": 99.951,
    "p95_ms": 261,
    "error_rate_1h": 0,
    "checks_24h": 1440,
    "compute_state": "ACTIVE",
    "last": {
      "code": 200,
      "ms": 120
    },
    "ttfb_ms": 110,
    "series": [
      [
        1793350800,
        true,
        200,
        120
      ],
      [
        1793350860,
        true,
        200,
        132
      ],
      [
        1793350920,
        true,
        200,
        144
      ],
      [
        1793350980,
        false,
        502,
        156
      ],
      [
        1793351040,
        true,
        200,
        168
      ],
      [
        1793351100,
        true,
        200,
        180
      ],
      [
        1793351160,
        true,
        200,
        192
      ],
      [
        1793351220,
        true,
        200,
        204
      ]
    ]
  },
  "api/apps/ops-runbook-bot/synthetics": {
    "interval_s": 1800,
    "live": {
      "journey": "Report flow",
      "ok": true,
      "budget_ms": 2500,
      "within_budget": true,
      "ts": 1793352420,
      "steps": [
        {
          "name": "GET /api/report",
          "ok": true,
          "code": 200,
          "ms": 200,
          "detail": "Demo assertion"
        }
      ]
    },
    "browser": [
      {
        "run_ts": "2026-10-30T09:27:00Z",
        "journey": "browser-smoke",
        "ok": true,
        "status_code": 200,
        "latency_ms": 800,
        "detail": "Demo browser result",
        "vantage": "external",
        "failure_stage": null,
        "artifact": "/Volumes/demo/monitor/ui_tests/ops-runbook-bot/run"
      }
    ]
  },
  "api/apps/ops-runbook-bot/ops": {
    "config": {
      "tags_json": "{\"team\": \"Platform\", \"cost_center\": \"CC-900\", \"env\": \"dev\", \"tier\": \"t1\"}",
      "budget_usd_month": 1400,
      "auto_stop": "night",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "intake",
        "app": {
          "name": "doc-intake",
          "url": "https://doc-intake-1008.aws.databricksapps.com",
          "permission": "CAN_USE"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 320
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/console/trace/0000000000000000000000000000006e": {
    "trace_id": "0000000000000000000000000000006e",
    "app": "legacy-reports",
    "root": "GET /api/report",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "legacy-reports",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "legacy-reports",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "legacy-reports",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "legacy-reports",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "legacy-reports",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "legacy-reports",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "legacy-reports",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "legacy-reports",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/legacy-reports/logs": {
    "logs": []
  },
  "api/apps/legacy-reports/errors": {
    "groups": [],
    "failed_requests": [],
    "error_logs": []
  },
  "api/apps/legacy-reports/traces": {
    "traces": []
  },
  "api/apps/legacy-reports/agent-traces": {
    "experiment": null,
    "traces": []
  },
  "api/apps/legacy-reports/agent-traces/tr-demo-10": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-10",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "legacy-reports",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "legacy-reports",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "legacy-reports",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "legacy-reports",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "legacy-reports",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "legacy-reports",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "legacy-reports",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "legacy-reports",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": []
  },
  "api/apps/legacy-reports/requests": {
    "timeline": [],
    "routes": []
  },
  "api/apps/legacy-reports/deps": {
    "deps": []
  },
  "api/apps/legacy-reports/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/legacy-reports/security": {
    "scan": {
      "name": "legacy-reports",
      "quality_score": 71,
      "findings_critical": 0,
      "findings_high": 0,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 24,
      "py_loc": 2200,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-10",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": []}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/legacy-reports/review": {
    "review": {
      "name": "legacy-reports",
      "verdict": "approve",
      "score_overall": 8.4,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo web for Finance.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/legacy-reports/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 0,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      }
    ],
    "forecast": {
      "forecast_30d_usd": 0.0,
      "days_observed": 30
    },
    "budget": 600,
    "mtd_usd": 0
  },
  "api/apps/legacy-reports/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "legacy-reports",
        "dbu_usd": 0,
        "ai_usd": 0,
        "total_usd": 0,
        "idle_usd": 0.0,
        "usd_per_1k_requests": null,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/legacy-reports/genai": {
    "daily": [],
    "top": [],
    "error_taxonomy": [],
    "agent_steps": [],
    "quality": [],
    "feedback": [],
    "feedback_recent": []
  },
  "api/apps/legacy-reports/drift": {
    "reports": []
  },
  "api/apps/legacy-reports/analytics": {
    "daily": [],
    "users": [],
    "mtd_usd": 0
  },
  "api/apps/legacy-reports/events": {
    "events": []
  },
  "api/apps/legacy-reports/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": []
  },
  "api/apps/legacy-reports/cohorts": {
    "cohorts": []
  },
  "api/apps/legacy-reports/rum": {
    "routes": []
  },
  "api/apps/legacy-reports/guardrails": {
    "findings": [],
    "templates": []
  },
  "api/apps/legacy-reports/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/legacy-reports/telemetry-health": {
    "health": null
  },
  "api/apps/legacy-reports/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": null,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": []
  },
  "api/apps/legacy-reports": {
    "uptime_24h": null,
    "p95_ms": null,
    "error_rate_1h": null,
    "checks_24h": 0,
    "compute_state": "STOPPED",
    "last": null,
    "ttfb_ms": null,
    "series": []
  },
  "api/apps/legacy-reports/synthetics": {
    "interval_s": 1800,
    "live": null,
    "browser": []
  },
  "api/apps/legacy-reports/ops": {
    "config": {
      "tags_json": "{\"team\": \"Finance\", \"cost_center\": \"CC-120\", \"env\": \"dev\", \"tier\": \"t1\"}",
      "budget_usd_month": 600,
      "auto_stop": "none",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "warehouse",
        "sql_warehouse": {
          "id": "wh-7d1a",
          "permission": "CAN_USE"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 0
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/console/trace/0000000000000000000000000000006f": {
    "trace_id": "0000000000000000000000000000006f",
    "app": "label-studio-lite",
    "root": "GET /api/report",
    "started_at": "2026-10-30T09:27:00Z",
    "duration_ms": 6420,
    "status": "error",
    "user_hash": "u_9b2e41c07a3d",
    "session_id": "s_51f0aa21",
    "spans": [
      {
        "id": "s1",
        "parent": null,
        "name": "POST /api/chat",
        "kind": "SERVER",
        "service": "label-studio-lite",
        "start_ms": 0,
        "duration_ms": 6420,
        "status": "error",
        "attrs": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        }
      },
      {
        "id": "s2",
        "parent": "s1",
        "name": "agent.run",
        "kind": "AGENT",
        "service": "label-studio-lite",
        "start_ms": 12,
        "duration_ms": 6380,
        "status": "error",
        "attrs": {
          "mlflow.spanType": "AGENT"
        }
      },
      {
        "id": "s3",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "label-studio-lite",
        "start_ms": 30,
        "duration_ms": 1840,
        "status": "ok",
        "attrs": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        }
      },
      {
        "id": "s4",
        "parent": "s2",
        "name": "tool policy_lookup",
        "kind": "TOOL",
        "service": "label-studio-lite",
        "start_ms": 1890,
        "duration_ms": 2950,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s5",
        "parent": "s4",
        "name": "GET /api/policies/{id}",
        "kind": "CLIENT",
        "service": "label-studio-lite",
        "start_ms": 1900,
        "duration_ms": 2920,
        "status": "ok",
        "attrs": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        }
      },
      {
        "id": "s6",
        "parent": "s5",
        "name": "GET /api/policies/{id}",
        "kind": "SERVER",
        "service": "label-studio-lite",
        "start_ms": 1930,
        "duration_ms": 2860,
        "status": "ok",
        "attrs": {}
      },
      {
        "id": "s7",
        "parent": "s6",
        "name": "sql.execute",
        "kind": "CLIENT",
        "service": "label-studio-lite",
        "start_ms": 1950,
        "duration_ms": 2710,
        "status": "ok",
        "attrs": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        }
      },
      {
        "id": "s8",
        "parent": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "kind": "LLM",
        "service": "label-studio-lite",
        "start_ms": 4860,
        "duration_ms": 1530,
        "status": "error",
        "attrs": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        }
      }
    ],
    "logs": [
      {
        "ts_ms": 1890,
        "severity": "INFO",
        "service": "claims-assistant",
        "body": "calling tool policy_lookup id=POL-***"
      },
      {
        "ts_ms": 4850,
        "severity": "WARN",
        "service": "doc-intake",
        "body": "slow query 2710 ms on wh-7d1a (cold start)"
      },
      {
        "ts_ms": 6390,
        "severity": "ERROR",
        "service": "claims-assistant",
        "body": "RateLimitError: 429 QPM limit exceeded [fingerprint a90d33e1c7b2]"
      }
    ]
  },
  "api/apps/label-studio-lite/logs": {
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0000000000000000000000000000006f"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0000000000000000000000000000006f"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006f"
      }
    ]
  },
  "api/apps/label-studio-lite/errors": {
    "groups": [
      {
        "fingerprint": "demo-11",
        "occurrences": 23,
        "first_seen": "2026-10-30T09:27:00Z",
        "last_seen": "2026-10-30T09:27:00Z",
        "sample": "Demo dependency timeout"
      }
    ],
    "failed_requests": [
      {
        "trace_id": "0000000000000000000000000000006f",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ],
    "error_logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006f"
      }
    ]
  },
  "api/apps/label-studio-lite/traces": {
    "traces": [
      {
        "trace_id": "0000000000000000000000000000006f",
        "name": "GET /api/report",
        "route": "/api/report",
        "duration_ms": 6420,
        "status": "error",
        "time": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/label-studio-lite/agent-traces": {
    "experiment": null,
    "traces": []
  },
  "api/apps/label-studio-lite/agent-traces/tr-demo-11": {
    "mlflow": {
      "info": {
        "state": "ERROR",
        "preview": "Check claim coverage",
        "response_preview": "Retry suggested"
      }
    },
    "client_request_id": "demo-request",
    "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId=tr-demo-11",
    "otel_spans": [
      {
        "span_id": "s1",
        "parent_span_id": null,
        "name": "POST /api/chat",
        "service_name": "label-studio-lite",
        "span_type": "SERVER",
        "status": "error",
        "attributes": {
          "http.route": "/api/chat",
          "http.response.status_code": 500,
          "app.version": "2.11.3"
        },
        "start_time_unix_nano": "1793352420000000000",
        "end_time_unix_nano": "1793352426420000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s2",
        "parent_span_id": "s1",
        "name": "agent.run",
        "service_name": "label-studio-lite",
        "span_type": "AGENT",
        "status": "error",
        "attributes": {
          "mlflow.spanType": "AGENT"
        },
        "start_time_unix_nano": "1793352420012000000",
        "end_time_unix_nano": "1793352426392000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s3",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "label-studio-lite",
        "span_type": "LLM",
        "status": "ok",
        "attributes": {
          "gen_ai.usage.input_tokens": 3120,
          "gen_ai.usage.output_tokens": 188,
          "monitor.llm.ttft_ms": 690
        },
        "start_time_unix_nano": "1793352420030000000",
        "end_time_unix_nano": "1793352421870000000",
        "in_tokens": 3120,
        "out_tokens": 188
      },
      {
        "span_id": "s4",
        "parent_span_id": "s2",
        "name": "tool policy_lookup",
        "service_name": "label-studio-lite",
        "span_type": "TOOL",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421890000000",
        "end_time_unix_nano": "1793352424840000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s5",
        "parent_span_id": "s4",
        "name": "GET /api/policies/{id}",
        "service_name": "label-studio-lite",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "server.address": "doc-intake-1008.aws.databricksapps.com"
        },
        "start_time_unix_nano": "1793352421900000000",
        "end_time_unix_nano": "1793352424820000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s6",
        "parent_span_id": "s5",
        "name": "GET /api/policies/{id}",
        "service_name": "label-studio-lite",
        "span_type": "SERVER",
        "status": "ok",
        "attributes": {},
        "start_time_unix_nano": "1793352421930000000",
        "end_time_unix_nano": "1793352424790000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s7",
        "parent_span_id": "s6",
        "name": "sql.execute",
        "service_name": "label-studio-lite",
        "span_type": "CLIENT",
        "status": "ok",
        "attributes": {
          "db.system.name": "databricks_sql",
          "db.namespace": "wh-7d1a",
          "db.response.returned_rows": 1
        },
        "start_time_unix_nano": "1793352421950000000",
        "end_time_unix_nano": "1793352424660000000",
        "in_tokens": null,
        "out_tokens": null
      },
      {
        "span_id": "s8",
        "parent_span_id": "s2",
        "name": "chat databricks-claude-sonnet-4-5",
        "service_name": "label-studio-lite",
        "span_type": "LLM",
        "status": "error",
        "attributes": {
          "error.type": "rate_limit",
          "gen_ai.usage.input_tokens": 0
        },
        "start_time_unix_nano": "1793352424860000000",
        "end_time_unix_nano": "1793352426390000000",
        "in_tokens": 0,
        "out_tokens": null
      }
    ],
    "logs": [
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "INFO",
        "body": "Request received",
        "trace_id": "0000000000000000000000000000006f"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "WARN",
        "body": "Retry budget almost exhausted",
        "trace_id": "0000000000000000000000000000006f"
      },
      {
        "time": "2026-10-30T09:27:00Z",
        "severity": "ERROR",
        "body": "Demo dependency timeout; request failed",
        "trace_id": "0000000000000000000000000000006f"
      }
    ]
  },
  "api/apps/label-studio-lite/requests": {
    "timeline": [
      {
        "ts": "2026-10-29T10:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 185.95
      },
      {
        "ts": "2026-10-29T11:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 240.07
      },
      {
        "ts": "2026-10-29T12:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 237.9
      },
      {
        "ts": "2026-10-29T13:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 235.6
      },
      {
        "ts": "2026-10-29T14:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 224.77
      },
      {
        "ts": "2026-10-29T15:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 238.83
      },
      {
        "ts": "2026-10-29T16:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 215.48
      },
      {
        "ts": "2026-10-29T17:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 181.71
      },
      {
        "ts": "2026-10-29T18:00:00Z",
        "requests": 1,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 155.16
      },
      {
        "ts": "2026-10-29T19:00:00Z",
        "requests": 1,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 153.1
      },
      {
        "ts": "2026-10-29T20:00:00Z",
        "requests": 1,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 143.0
      },
      {
        "ts": "2026-10-29T21:00:00Z",
        "requests": 1,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 198.19
      },
      {
        "ts": "2026-10-29T22:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 192.66
      },
      {
        "ts": "2026-10-29T23:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 231.94
      },
      {
        "ts": "2026-10-30T00:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 259.24
      },
      {
        "ts": "2026-10-30T01:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 265.81
      },
      {
        "ts": "2026-10-30T02:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 241.71
      },
      {
        "ts": "2026-10-30T03:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 214.72
      },
      {
        "ts": "2026-10-30T04:00:00Z",
        "requests": 2,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 202.41
      },
      {
        "ts": "2026-10-30T05:00:00Z",
        "requests": 1,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 156.26
      },
      {
        "ts": "2026-10-30T06:00:00Z",
        "requests": 1,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 173.39
      },
      {
        "ts": "2026-10-30T07:00:00Z",
        "requests": 1,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 142.74
      },
      {
        "ts": "2026-10-30T08:00:00Z",
        "requests": 1,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 174.23
      },
      {
        "ts": "2026-10-30T09:00:00Z",
        "requests": 1,
        "errors": 0,
        "p50_ms": 75,
        "p95_ms": 163.37
      }
    ],
    "routes": [
      {
        "route": "/api/report",
        "requests": 100,
        "errors": 3,
        "avg_ms": 310,
        "p50_ms": 200,
        "p95_ms": 900
      }
    ]
  },
  "api/apps/label-studio-lite/deps": {
    "deps": [
      {
        "dependency": "databricks_sql/wh-7d1a",
        "calls": 1420,
        "avg_ms": 150,
        "p95_ms": 560,
        "errors": 11
      }
    ]
  },
  "api/apps/label-studio-lite/timeline": {
    "events": [
      {
        "ts": "2026-10-30T09:27:00Z",
        "type": "deploy",
        "state": "SUCCEEDED",
        "rule": "deployment",
        "severity": "info",
        "message": "Demo release"
      }
    ],
    "releases": [
      {
        "deployment_id": "demo-current",
        "start_ts": "2026-10-30T09:27:00Z",
        "requests": 100,
        "p95_ms": 1200,
        "error_pct": 3,
        "tokens": 8000
      },
      {
        "deployment_id": "demo-previous",
        "start_ts": "2026-10-28T10:00:00Z",
        "requests": 800,
        "p95_ms": 600,
        "error_pct": 0,
        "tokens": 40000
      }
    ]
  },
  "api/apps/label-studio-lite/security": {
    "scan": {
      "name": "label-studio-lite",
      "quality_score": 91,
      "findings_critical": 0,
      "findings_high": 0,
      "findings_medium": 2,
      "findings_low": 1,
      "files": 25,
      "py_loc": 2300,
      "deps": 12,
      "deps_pinned": 10,
      "freshness_score": 76,
      "has_tests": true,
      "has_readme": true,
      "scanned_at": "2026-10-30T09:27:00Z",
      "deployment_id": "demo-deploy-11",
      "deps_json": "[{\"name\": \"example-python\", \"eco\": \"pypi\", \"version\": \"1.0.0\", \"latest\": \"2.0.0\", \"behind\": \"major\", \"vulns\": []}, {\"name\": \"example-web\", \"eco\": \"npm\", \"version\": \"3.1.0\", \"latest\": \"3.1.1\", \"behind\": \"patch\", \"vulns\": []}]",
      "policy_violations": 0,
      "has_npm": true
    },
    "findings": [
      {
        "severity": "medium",
        "kind": "dependency",
        "title": "Package update available",
        "detail": "Demo finding",
        "file": "requirements.txt",
        "line": 2
      }
    ]
  },
  "api/apps/label-studio-lite/review": {
    "review": {
      "name": "label-studio-lite",
      "verdict": "approve",
      "score_overall": 7.2,
      "summary": "Demo advisory: review dependency freshness and retry limits.",
      "model": "demo-reviewer",
      "reviewed_at": "2026-10-30T09:27:00Z",
      "files_reviewed": 14,
      "input_tokens": 1200,
      "output_tokens": 240,
      "strengths_json": "[\"Clear request boundaries\", \"Tested business logic\"]",
      "findings_json": "[{\"severity\":\"medium\",\"area\":\"reliability\",\"title\":\"Bound retries\",\"recommendation\":\"Set a retry budget.\"}]",
      "score_security": 8,
      "score_reliability": 8,
      "score_maintainability": 8,
      "score_cost": 8,
      "score_monitoring": 8
    },
    "overview": {
      "purpose": "Demo web for Data Science.",
      "tech_stack": [
        "Python",
        "FastAPI",
        "Node"
      ],
      "endpoints": [
        "GET /api/report",
        "GET /healthz"
      ]
    }
  },
  "api/apps/label-studio-lite/cost": {
    "daily": [
      {
        "date": "2026-10-01",
        "dbus": 0.5,
        "dbu_usd": 13.85,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-02",
        "dbus": 0.5,
        "dbu_usd": 14.39,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-03",
        "dbus": 0.5,
        "dbu_usd": 14.43,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-04",
        "dbus": 0.5,
        "dbu_usd": 14.71,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-05",
        "dbus": 0.5,
        "dbu_usd": 14.95,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-06",
        "dbus": 0.5,
        "dbu_usd": 14.78,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-07",
        "dbus": 0.5,
        "dbu_usd": 15.27,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-08",
        "dbus": 0.5,
        "dbu_usd": 12.97,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-09",
        "dbus": 0.5,
        "dbu_usd": 11.16,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-10",
        "dbus": 0.5,
        "dbu_usd": 11.86,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-11",
        "dbus": 0.5,
        "dbu_usd": 10.69,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-12",
        "dbus": 0.5,
        "dbu_usd": 8.7,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-13",
        "dbus": 0.5,
        "dbu_usd": 10.68,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-14",
        "dbus": 0.5,
        "dbu_usd": 10.62,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-15",
        "dbus": 0.5,
        "dbu_usd": 12.12,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-16",
        "dbus": 0.5,
        "dbu_usd": 13.13,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-17",
        "dbus": 0.5,
        "dbu_usd": 14.99,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-18",
        "dbus": 0.5,
        "dbu_usd": 15.79,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-19",
        "dbus": 0.5,
        "dbu_usd": 16.58,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-20",
        "dbus": 0.5,
        "dbu_usd": 15.09,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-21",
        "dbus": 0.5,
        "dbu_usd": 15.94,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-22",
        "dbus": 0.5,
        "dbu_usd": 14.65,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-23",
        "dbus": 0.5,
        "dbu_usd": 13.98,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-24",
        "dbus": 0.5,
        "dbu_usd": 11.89,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-25",
        "dbus": 0.5,
        "dbu_usd": 11.81,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-26",
        "dbus": 0.5,
        "dbu_usd": 10.09,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-27",
        "dbus": 0.5,
        "dbu_usd": 8.95,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-28",
        "dbus": 0.5,
        "dbu_usd": 9.01,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-29",
        "dbus": 0.5,
        "dbu_usd": 9.43,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      },
      {
        "date": "2026-10-30",
        "dbus": 0.5,
        "dbu_usd": 11.39,
        "ai_calls": 0,
        "ai_input_tokens": 0,
        "ai_output_tokens": 0
      }
    ],
    "forecast": {
      "forecast_30d_usd": 375.42,
      "days_observed": 30
    },
    "budget": 600,
    "mtd_usd": 381.05
  },
  "api/apps/label-studio-lite/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "label-studio-lite",
        "dbu_usd": 381.05,
        "ai_usd": 0,
        "total_usd": 381.05,
        "idle_usd": 354.38,
        "usd_per_1k_requests": 317.542,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/apps/label-studio-lite/genai": {
    "daily": [],
    "top": [],
    "error_taxonomy": [],
    "agent_steps": [],
    "quality": [],
    "feedback": [],
    "feedback_recent": []
  },
  "api/apps/label-studio-lite/drift": {
    "reports": []
  },
  "api/apps/label-studio-lite/analytics": {
    "daily": [
      {
        "date": "2026-10-24",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-25",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-26",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-27",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-28",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-29",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      },
      {
        "date": "2026-10-30",
        "requests": 100,
        "users": 20,
        "sessions": 30,
        "errors": 1,
        "avg_ms": 200
      }
    ],
    "users": [
      {
        "user_hash": "u_demo_91a",
        "first_seen": "2026-10-01",
        "last_seen": "2026-10-30T09:27:00Z",
        "requests": 80,
        "sessions": 10,
        "active_days": 7,
        "errors": 1,
        "tokens": 4000
      }
    ],
    "mtd_usd": 381.05
  },
  "api/apps/label-studio-lite/events": {
    "events": [
      {
        "event_name": "answer_shown",
        "app_version": "2.16.5",
        "events": 40,
        "sessions": 32,
        "last_seen": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/apps/label-studio-lite/funnels": {
    "specs": [
      {
        "funnel": "answer",
        "steps": [
          "ask_question",
          "answer_shown"
        ]
      }
    ],
    "steps": [
      {
        "funnel": "answer",
        "app_version": "2.16.5",
        "step_name": "ask_question",
        "sessions": 100,
        "dropoff_pct": 0
      },
      {
        "funnel": "answer",
        "app_version": "2.16.5",
        "step_name": "answer_shown",
        "sessions": 80,
        "dropoff_pct": 20
      }
    ]
  },
  "api/apps/label-studio-lite/cohorts": {
    "cohorts": [
      {
        "cohort_week": "2026-10-19",
        "week_number": 1,
        "cohort_size": 40,
        "retained_users": 30,
        "retention_pct": 75,
        "partial_week": true
      }
    ]
  },
  "api/apps/label-studio-lite/rum": {
    "routes": [
      {
        "date": "2026-10-30",
        "route": "/",
        "page_views": 200,
        "p75_lcp": 650,
        "p75_cls": 0.02,
        "p75_inp": 80,
        "js_errors": 1,
        "fingerprint": "rum-demo",
        "trace_id": "0000000000000000000000000000006f"
      }
    ]
  },
  "api/apps/label-studio-lite/guardrails": {
    "findings": [],
    "templates": []
  },
  "api/apps/label-studio-lite/product-config": {
    "outcome_event": "answer_shown",
    "token_budget_day": 100000,
    "throttle": "none",
    "tokens_today": 15000,
    "tokens_last_hour": 3000,
    "policy_updated_at": "2026-10-30T09:27:00Z"
  },
  "api/apps/label-studio-lite/telemetry-health": {
    "health": {
      "quality": "healthy",
      "envelope_coverage": 0.9,
      "orphan_ratio_24h": 0.01,
      "sampler_ratio": 1,
      "last_span_at": "2026-10-30T09:27:00Z",
      "last_log_at": "2026-10-30T09:27:00Z",
      "last_metric_at": "2026-10-30T09:27:00Z",
      "semconv_legacy_only": 0,
      "semconv_stable_only": 0.1,
      "semconv_both": 0.9,
      "gateway_vs_otel_tokens": 12,
      "token_date": "2026-10-29"
    }
  },
  "api/apps/label-studio-lite/slo": {
    "specs": [
      {
        "slo": "availability",
        "sli": "availability",
        "target": 0.999,
        "window_days": 28,
        "budget_remaining_pct": 94.4,
        "observed_since": "2026-10-02",
        "last_bucket": "2026-10-30T09:27:00Z"
      }
    ],
    "series": [
      {
        "slo": "availability",
        "date": "2026-10-10",
        "budget_remaining_pct": 100
      },
      {
        "slo": "availability",
        "date": "2026-10-11",
        "budget_remaining_pct": 80
      },
      {
        "slo": "availability",
        "date": "2026-10-12",
        "budget_remaining_pct": 60
      },
      {
        "slo": "availability",
        "date": "2026-10-13",
        "budget_remaining_pct": 40
      },
      {
        "slo": "availability",
        "date": "2026-10-14",
        "budget_remaining_pct": 20
      },
      {
        "slo": "availability",
        "date": "2026-10-15",
        "budget_remaining_pct": 0
      },
      {
        "slo": "availability",
        "date": "2026-10-16",
        "budget_remaining_pct": -20
      }
    ]
  },
  "api/apps/label-studio-lite": {
    "uptime_24h": 99.972,
    "p95_ms": 279,
    "error_rate_1h": 0,
    "checks_24h": 1440,
    "compute_state": "ACTIVE",
    "last": {
      "code": 200,
      "ms": 120
    },
    "ttfb_ms": 110,
    "series": [
      [
        1793350800,
        true,
        200,
        120
      ],
      [
        1793350860,
        true,
        200,
        132
      ],
      [
        1793350920,
        true,
        200,
        144
      ],
      [
        1793350980,
        false,
        502,
        156
      ],
      [
        1793351040,
        true,
        200,
        168
      ],
      [
        1793351100,
        true,
        200,
        180
      ],
      [
        1793351160,
        true,
        200,
        192
      ],
      [
        1793351220,
        true,
        200,
        204
      ]
    ]
  },
  "api/apps/label-studio-lite/synthetics": {
    "interval_s": 1800,
    "live": {
      "journey": "Report flow",
      "ok": true,
      "budget_ms": 2500,
      "within_budget": true,
      "ts": 1793352420,
      "steps": [
        {
          "name": "GET /api/report",
          "ok": true,
          "code": 200,
          "ms": 200,
          "detail": "Demo assertion"
        }
      ]
    },
    "browser": [
      {
        "run_ts": "2026-10-30T09:27:00Z",
        "journey": "browser-smoke",
        "ok": true,
        "status_code": 200,
        "latency_ms": 800,
        "detail": "Demo browser result",
        "vantage": "external",
        "failure_stage": null,
        "artifact": "/Volumes/demo/monitor/ui_tests/label-studio-lite/run"
      }
    ]
  },
  "api/apps/label-studio-lite/ops": {
    "config": {
      "tags_json": "{}",
      "budget_usd_month": 600,
      "auto_stop": "none",
      "idle_hours": 24,
      "capacity_path": "/monitor/capacity",
      "updated_at": "2026-10-30T09:27:00Z",
      "updated_by": "demo-operator"
    },
    "resources": [
      {
        "name": "model",
        "serving_endpoint": {
          "name": "claims-model",
          "permission": "CAN_QUERY"
        }
      }
    ],
    "deployments": [
      {
        "create_time": "2026-10-30T09:27:00Z",
        "deployment_id": "demo-current",
        "state": "SUCCEEDED",
        "mode": "SNAPSHOT"
      }
    ],
    "permissions": [
      {
        "principal": "operators",
        "principal_type": "group",
        "level": "CAN_MANAGE"
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-30T09:27:00Z",
        "user": "demo-operator",
        "action_name": "deploy",
        "status_code": "200"
      }
    ],
    "telemetry_volume": [
      {
        "signal": "spans",
        "rows_24h": 320
      }
    ],
    "job_health": [
      {
        "job_id": "101",
        "runs_7d": 7,
        "succeeded": 6,
        "avg_s": 60,
        "last_run": "2026-10-30T09:27:00Z"
      }
    ],
    "capacity": null
  },
  "api/actions/mute": {
    "mutes": [
      {
        "app": "legacy-reports",
        "rule": "*",
        "starts_at": "2026-10-29T22:30:00Z",
        "ends_at": "2026-10-31T05:30:00Z",
        "reason": "Night auto-stop",
        "created_by": "app_stopper",
        "id": "demo-mute"
      }
    ]
  },
  "api/console/identity": {
    "actor": "demo-operator",
    "admin": true,
    "reason": ""
  },
  "api/alerts": {
    "active": [
      {
        "id": "al-1042",
        "app": "fraud-triage",
        "rule": "app_down",
        "severity": "critical",
        "state": "firing",
        "since": "2026-10-30T08:52:00Z",
        "message": "Consecutive probe failures (HTTP 502) from internal + external vantage",
        "muted": false
      },
      {
        "id": "al-1041",
        "app": "fraud-triage",
        "rule": "slo_fast_burn",
        "severity": "critical",
        "state": "firing",
        "since": "2026-10-30T08:59:00Z",
        "message": "Availability SLO burning 21.3x over 1h and 5m windows (target 99.9%)",
        "muted": false
      },
      {
        "id": "al-1039",
        "app": "claims-assistant",
        "rule": "slo_slow_burn",
        "severity": "high",
        "state": "firing",
        "since": "2026-10-30T07:10:00Z",
        "message": "Latency SLO burning 6.8x over 6h and 30m windows (p95 > 1500 ms)",
        "muted": false
      },
      {
        "id": "al-1037",
        "app": "claims-assistant",
        "rule": "budget_burn",
        "severity": "warning",
        "state": "firing",
        "since": "2026-10-29T23:30:00Z",
        "message": "91% of monthly budget used on day 30 ($1,830 of $2,000)",
        "muted": false
      },
      {
        "id": "al-1036",
        "app": "claims-assistant",
        "rule": "prompt_drift",
        "severity": "info",
        "state": "firing",
        "since": "2026-10-29T11:50:00Z",
        "message": "31% of this week's prompts fall outside last week's clusters",
        "muted": false
      },
      {
        "id": "al-1035",
        "app": "forecast-studio",
        "rule": "telemetry_stale",
        "severity": "warning",
        "state": "firing",
        "since": "2026-10-30T05:50:00Z",
        "message": "No spans for 3h 50m while app is RUNNING (analytics-us worker stale)",
        "muted": false
      },
      {
        "id": "al-1033",
        "app": "supplier-portal",
        "rule": "review_reject",
        "severity": "high",
        "state": "firing",
        "since": "2026-10-28T09:10:00Z",
        "message": "AI code review rejected deployment 4.2.1: hard-coded secret + 3 high CVEs",
        "muted": false
      },
      {
        "id": "al-1031",
        "app": "fraud-triage",
        "rule": "critical_findings",
        "severity": "critical",
        "state": "firing",
        "since": "2026-10-27T13:10:00Z",
        "message": "CVE-2026-31337 (critical) in aiohttp 3.9.1",
        "muted": false
      },
      {
        "id": "al-1030",
        "app": "sales-cockpit",
        "rule": "permission_drift",
        "severity": "warning",
        "state": "firing",
        "since": "2026-10-29T21:50:00Z",
        "message": "Group 'all-contractors' gained CAN_MANAGE",
        "muted": false
      },
      {
        "id": "al-1028",
        "app": "label-studio-lite",
        "rule": "idle_cost",
        "severity": "info",
        "state": "firing",
        "since": "2026-10-26T22:10:00Z",
        "message": "No real traffic for 6 days; $214 idle compute this month",
        "muted": true
      }
    ],
    "recent": [
      {
        "id": "al-1042",
        "app": "fraud-triage",
        "rule": "app_down",
        "severity": "critical",
        "state": "firing",
        "since": "2026-10-30T08:52:00Z",
        "message": "Consecutive probe failures (HTTP 502) from internal + external vantage",
        "muted": false,
        "ts": "2026-10-30T08:52:00Z"
      },
      {
        "id": "al-1041",
        "app": "fraud-triage",
        "rule": "slo_fast_burn",
        "severity": "critical",
        "state": "firing",
        "since": "2026-10-30T08:59:00Z",
        "message": "Availability SLO burning 21.3x over 1h and 5m windows (target 99.9%)",
        "muted": false,
        "ts": "2026-10-30T08:59:00Z"
      },
      {
        "id": "al-1039",
        "app": "claims-assistant",
        "rule": "slo_slow_burn",
        "severity": "high",
        "state": "firing",
        "since": "2026-10-30T07:10:00Z",
        "message": "Latency SLO burning 6.8x over 6h and 30m windows (p95 > 1500 ms)",
        "muted": false,
        "ts": "2026-10-30T07:10:00Z"
      },
      {
        "id": "al-1037",
        "app": "claims-assistant",
        "rule": "budget_burn",
        "severity": "warning",
        "state": "firing",
        "since": "2026-10-29T23:30:00Z",
        "message": "91% of monthly budget used on day 30 ($1,830 of $2,000)",
        "muted": false,
        "ts": "2026-10-29T23:30:00Z"
      },
      {
        "id": "al-1036",
        "app": "claims-assistant",
        "rule": "prompt_drift",
        "severity": "info",
        "state": "firing",
        "since": "2026-10-29T11:50:00Z",
        "message": "31% of this week's prompts fall outside last week's clusters",
        "muted": false,
        "ts": "2026-10-29T11:50:00Z"
      },
      {
        "id": "al-1035",
        "app": "forecast-studio",
        "rule": "telemetry_stale",
        "severity": "warning",
        "state": "firing",
        "since": "2026-10-30T05:50:00Z",
        "message": "No spans for 3h 50m while app is RUNNING (analytics-us worker stale)",
        "muted": false,
        "ts": "2026-10-30T05:50:00Z"
      },
      {
        "id": "al-1033",
        "app": "supplier-portal",
        "rule": "review_reject",
        "severity": "high",
        "state": "firing",
        "since": "2026-10-28T09:10:00Z",
        "message": "AI code review rejected deployment 4.2.1: hard-coded secret + 3 high CVEs",
        "muted": false,
        "ts": "2026-10-28T09:10:00Z"
      },
      {
        "id": "al-1031",
        "app": "fraud-triage",
        "rule": "critical_findings",
        "severity": "critical",
        "state": "firing",
        "since": "2026-10-27T13:10:00Z",
        "message": "CVE-2026-31337 (critical) in aiohttp 3.9.1",
        "muted": false,
        "ts": "2026-10-27T13:10:00Z"
      },
      {
        "id": "al-1030",
        "app": "sales-cockpit",
        "rule": "permission_drift",
        "severity": "warning",
        "state": "firing",
        "since": "2026-10-29T21:50:00Z",
        "message": "Group 'all-contractors' gained CAN_MANAGE",
        "muted": false,
        "ts": "2026-10-29T21:50:00Z"
      },
      {
        "id": "al-1028",
        "app": "label-studio-lite",
        "rule": "idle_cost",
        "severity": "info",
        "state": "firing",
        "since": "2026-10-26T22:10:00Z",
        "message": "No real traffic for 6 days; $214 idle compute this month",
        "muted": true,
        "ts": "2026-10-26T22:10:00Z"
      },
      {
        "id": "al-1024",
        "app": "pricing-api",
        "rule": "anomaly_traffic",
        "severity": "info",
        "state": "resolved",
        "since": "2026-10-29T01:50:00Z",
        "message": "Traffic 3.4x above 7-day baseline (resolved after 40 min)",
        "muted": false,
        "ts": "2026-10-29T01:50:00Z"
      },
      {
        "id": "al-1019",
        "app": "hr-policy-bot",
        "rule": "slo_ticket",
        "severity": "warning",
        "state": "resolved",
        "since": "2026-10-27T09:50:00Z",
        "message": "Availability budget burn 1.2x over 3 days",
        "muted": false,
        "ts": "2026-10-27T09:50:00Z"
      }
    ]
  },
  "api/governance": {
    "configs": [
      {
        "name": "claims-assistant",
        "tags_json": "{\"team\": \"Claims\", \"cost_center\": \"CC-410\", \"env\": \"prod\", \"tier\": \"t1\"}",
        "budget_usd_month": 2000,
        "auto_stop": "none",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      },
      {
        "name": "pricing-api",
        "tags_json": "{\"team\": \"Pricing\", \"cost_center\": \"CC-220\", \"env\": \"prod\", \"tier\": \"t1\"}",
        "budget_usd_month": 900,
        "auto_stop": "night",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      },
      {
        "name": "sales-cockpit",
        "tags_json": "{\"team\": \"Sales Ops\", \"cost_center\": \"CC-150\", \"env\": \"prod\", \"tier\": \"t1\"}",
        "budget_usd_month": 600,
        "auto_stop": "idle",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      },
      {
        "name": "fraud-triage",
        "tags_json": "{\"team\": \"Risk\", \"cost_center\": \"CC-330\", \"env\": \"prod\", \"tier\": \"t1\"}",
        "budget_usd_month": 2400,
        "auto_stop": "none",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      },
      {
        "name": "supplier-portal",
        "tags_json": "{\"team\": \"Procurement\", \"cost_center\": \"CC-505\", \"env\": \"prod\", \"tier\": \"t1\"}",
        "budget_usd_month": 1000,
        "auto_stop": "none",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      },
      {
        "name": "hr-policy-bot",
        "tags_json": "{\"team\": \"People\", \"cost_center\": \"CC-610\", \"env\": \"prod\", \"tier\": \"t1\"}",
        "budget_usd_month": 3400,
        "auto_stop": "idle",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      },
      {
        "name": "forecast-studio",
        "tags_json": "{\"team\": \"Finance\", \"cost_center\": \"CC-120\", \"env\": \"prod\", \"tier\": \"t1\"}",
        "budget_usd_month": 1100,
        "auto_stop": "none",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      },
      {
        "name": "churn-explorer",
        "tags_json": "{\"team\": \"Marketing\", \"cost_center\": \"CC-140\", \"env\": \"prod\", \"tier\": \"t1\"}",
        "budget_usd_month": 700,
        "auto_stop": "idle",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      },
      {
        "name": "doc-intake",
        "tags_json": "{\"team\": \"Claims\", \"cost_center\": \"CC-410\", \"env\": \"prod\", \"tier\": \"t1\"}",
        "budget_usd_month": 800,
        "auto_stop": "night",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      },
      {
        "name": "ops-runbook-bot",
        "tags_json": "{\"team\": \"Platform\", \"cost_center\": \"CC-900\", \"env\": \"dev\", \"tier\": \"t1\"}",
        "budget_usd_month": 1400,
        "auto_stop": "night",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      },
      {
        "name": "legacy-reports",
        "tags_json": "{\"team\": \"Finance\", \"cost_center\": \"CC-120\", \"env\": \"dev\", \"tier\": \"t1\"}",
        "budget_usd_month": 600,
        "auto_stop": "none",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      },
      {
        "name": "label-studio-lite",
        "tags_json": "{}",
        "budget_usd_month": 600,
        "auto_stop": "none",
        "idle_hours": 24,
        "capacity_path": "/monitor/capacity",
        "updated_at": "2026-10-30T09:27:00Z",
        "updated_by": "demo-operator"
      }
    ],
    "mtd": [
      {
        "name": "claims-assistant",
        "mtd_usd": 312.87
      },
      {
        "name": "pricing-api",
        "mtd_usd": 529.93
      },
      {
        "name": "sales-cockpit",
        "mtd_usd": 397.92
      },
      {
        "name": "fraud-triage",
        "mtd_usd": 746.94
      },
      {
        "name": "supplier-portal",
        "mtd_usd": 749.66
      },
      {
        "name": "hr-policy-bot",
        "mtd_usd": 727.43
      },
      {
        "name": "forecast-studio",
        "mtd_usd": 735.54
      },
      {
        "name": "churn-explorer",
        "mtd_usd": 417.1
      },
      {
        "name": "doc-intake",
        "mtd_usd": 358.39
      },
      {
        "name": "ops-runbook-bot",
        "mtd_usd": 451.02
      },
      {
        "name": "legacy-reports",
        "mtd_usd": 0
      },
      {
        "name": "label-studio-lite",
        "mtd_usd": 381.05
      }
    ],
    "usage": [
      {
        "name": "claims-assistant",
        "peak_dau": 256,
        "requests_7d": 147000,
        "sessions_7d": 3072
      },
      {
        "name": "pricing-api",
        "peak_dau": 662,
        "requests_7d": 143717,
        "sessions_7d": 7944
      },
      {
        "name": "sales-cockpit",
        "peak_dau": 625,
        "requests_7d": 271467,
        "sessions_7d": 7500
      },
      {
        "name": "fraud-triage",
        "peak_dau": 257,
        "requests_7d": 63000,
        "sessions_7d": 3084
      },
      {
        "name": "supplier-portal",
        "peak_dau": 431,
        "requests_7d": 148099,
        "sessions_7d": 5172
      },
      {
        "name": "hr-policy-bot",
        "peak_dau": 606,
        "requests_7d": 267631,
        "sessions_7d": 7272
      },
      {
        "name": "forecast-studio",
        "peak_dau": 323,
        "requests_7d": 147000,
        "sessions_7d": 3876
      },
      {
        "name": "churn-explorer",
        "peak_dau": 610,
        "requests_7d": 290801,
        "sessions_7d": 7320
      },
      {
        "name": "doc-intake",
        "peak_dau": 408,
        "requests_7d": 197253,
        "sessions_7d": 4896
      },
      {
        "name": "ops-runbook-bot",
        "peak_dau": 362,
        "requests_7d": 106694,
        "sessions_7d": 4344
      },
      {
        "name": "legacy-reports",
        "peak_dau": 0,
        "requests_7d": 0,
        "sessions_7d": 0
      },
      {
        "name": "label-studio-lite",
        "peak_dau": 1,
        "requests_7d": 280,
        "sessions_7d": 12
      }
    ],
    "telemetry_active": [
      "claims-assistant",
      "pricing-api",
      "sales-cockpit",
      "fraud-triage",
      "supplier-portal",
      "hr-policy-bot",
      "forecast-studio",
      "churn-explorer",
      "doc-intake",
      "ops-runbook-bot",
      "label-studio-lite"
    ],
    "chargeback": [
      {
        "team": "Claims",
        "cost_center": "CC-410",
        "apps": 1,
        "mtd_usd": 312.87,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      },
      {
        "team": "Pricing",
        "cost_center": "CC-220",
        "apps": 1,
        "mtd_usd": 529.93,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      },
      {
        "team": "Sales Ops",
        "cost_center": "CC-150",
        "apps": 1,
        "mtd_usd": 397.92,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      },
      {
        "team": "Risk",
        "cost_center": "CC-330",
        "apps": 1,
        "mtd_usd": 746.94,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      },
      {
        "team": "Procurement",
        "cost_center": "CC-505",
        "apps": 1,
        "mtd_usd": 749.66,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      },
      {
        "team": "People",
        "cost_center": "CC-610",
        "apps": 1,
        "mtd_usd": 727.43,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      },
      {
        "team": "Finance",
        "cost_center": "CC-120",
        "apps": 1,
        "mtd_usd": 735.54,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      },
      {
        "team": "Marketing",
        "cost_center": "CC-140",
        "apps": 1,
        "mtd_usd": 417.1,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      },
      {
        "team": "Claims",
        "cost_center": "CC-410",
        "apps": 1,
        "mtd_usd": 358.39,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      },
      {
        "team": "Platform",
        "cost_center": "CC-900",
        "apps": 1,
        "mtd_usd": 451.02,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      },
      {
        "team": "Finance",
        "cost_center": "CC-120",
        "apps": 1,
        "mtd_usd": 0,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      },
      {
        "team": "Data Science",
        "cost_center": "CC-720",
        "apps": 1,
        "mtd_usd": 381.05,
        "mtd_tokens": 30000,
        "ai_calls": 1000
      }
    ],
    "audit": [
      {
        "event_time": "2026-10-29T21:50:00Z",
        "user": "contractor.x@partner.com",
        "action_name": "changePermissions",
        "app": "sales-cockpit",
        "status_code": 200
      },
      {
        "event_time": "2026-10-30T08:45:00Z",
        "user": "arjun.rao@contoso.com",
        "action_name": "deploy",
        "app": "fraud-triage",
        "status_code": 200
      },
      {
        "event_time": "2026-10-29T22:30:00Z",
        "user": "apps-monitor (SP)",
        "action_name": "stop",
        "app": "legacy-reports",
        "status_code": 200
      }
    ]
  },
  "api/unit-economics": {
    "days": 30,
    "apps": [
      {
        "name": "claims-assistant",
        "dbu_usd": 312.87,
        "ai_usd": 1612.9,
        "total_usd": 1830.4,
        "idle_usd": 59.22,
        "usd_per_1k_requests": 2.347,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      },
      {
        "name": "pricing-api",
        "dbu_usd": 529.93,
        "ai_usd": 58.78,
        "total_usd": 588.71,
        "idle_usd": 55.41,
        "usd_per_1k_requests": 0.956,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      },
      {
        "name": "sales-cockpit",
        "dbu_usd": 397.92,
        "ai_usd": 0,
        "total_usd": 397.92,
        "idle_usd": 22.24,
        "usd_per_1k_requests": 0.342,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      },
      {
        "name": "fraud-triage",
        "dbu_usd": 746.94,
        "ai_usd": 1422.77,
        "total_usd": 2169.71,
        "idle_usd": 55.68,
        "usd_per_1k_requests": 8.036,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      },
      {
        "name": "supplier-portal",
        "dbu_usd": 749.66,
        "ai_usd": 0,
        "total_usd": 749.66,
        "idle_usd": 249.84,
        "usd_per_1k_requests": 1.181,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      },
      {
        "name": "hr-policy-bot",
        "dbu_usd": 727.43,
        "ai_usd": 1715.0,
        "total_usd": 2442.43,
        "idle_usd": 131.56,
        "usd_per_1k_requests": 2.129,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      },
      {
        "name": "forecast-studio",
        "dbu_usd": 735.54,
        "ai_usd": 0,
        "total_usd": 735.54,
        "idle_usd": 44.88,
        "usd_per_1k_requests": 1.168,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      },
      {
        "name": "churn-explorer",
        "dbu_usd": 417.1,
        "ai_usd": 0,
        "total_usd": 417.1,
        "idle_usd": 135.95,
        "usd_per_1k_requests": 0.335,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      },
      {
        "name": "doc-intake",
        "dbu_usd": 358.39,
        "ai_usd": 45.9,
        "total_usd": 404.29,
        "idle_usd": 136.19,
        "usd_per_1k_requests": 0.478,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      },
      {
        "name": "ops-runbook-bot",
        "dbu_usd": 451.02,
        "ai_usd": 389.64,
        "total_usd": 840.66,
        "idle_usd": 84.84,
        "usd_per_1k_requests": 1.838,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      },
      {
        "name": "legacy-reports",
        "dbu_usd": 0,
        "ai_usd": 0,
        "total_usd": 0,
        "idle_usd": 0.0,
        "usd_per_1k_requests": null,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      },
      {
        "name": "label-studio-lite",
        "dbu_usd": 381.05,
        "ai_usd": 0,
        "total_usd": 381.05,
        "idle_usd": 354.38,
        "usd_per_1k_requests": 317.542,
        "usd_per_session": 0.02,
        "usd_per_user": 0.1,
        "usd_per_outcome": 0.05,
        "completions": 100,
        "unpriced_days": 0
      }
    ]
  },
  "api/leaderboard": {
    "formula": "Weighted mean of available scores out of 100: availability 25%, errors 20%, latency 15%, scan 15%, review 10%, cost 10%, adoption 5%. Availability = probe uptime; errors = 100 - error percentage; latency = min(100, 100 * 2500 ms / p95); scan = scan quality; review = review score * 10; cost = clamp(100 * (1 - weekly cost growth)); adoption = min(100, active users). Missing evidence is excluded and weights renormalized. Stopped apps excluded. Demo adoption uses the snapshot active users; production uses distinct users in 7 days.",
    "apps": [
      {
        "name": "claims-assistant",
        "score": 94.6,
        "coverage_pct": 100,
        "components": {
          "availability": 99.655,
          "errors": 94.66,
          "latency": 100,
          "scan": 85,
          "review": 80.0,
          "cost": 100,
          "adoption": 100
        }
      },
      {
        "name": "pricing-api",
        "score": 93.23,
        "coverage_pct": 100,
        "components": {
          "availability": 99.974,
          "errors": 99.42,
          "latency": 100,
          "scan": 67,
          "review": 83.0,
          "cost": 100,
          "adoption": 100
        }
      },
      {
        "name": "sales-cockpit",
        "score": 96.86,
        "coverage_pct": 100,
        "components": {
          "availability": 99.964,
          "errors": 99.62,
          "latency": 100,
          "scan": 87,
          "review": 89.0,
          "cost": 100,
          "adoption": 100
        }
      },
      {
        "name": "fraud-triage",
        "score": 75.53,
        "coverage_pct": 100,
        "components": {
          "availability": 91.489,
          "errors": 54.92,
          "latency": 43.8288920056101,
          "scan": 78,
          "review": 84.0,
          "cost": 100,
          "adoption": 100
        }
      },
      {
        "name": "supplier-portal",
        "score": 90.23,
        "coverage_pct": 100,
        "components": {
          "availability": 99.985,
          "errors": 99.42,
          "latency": 100,
          "scan": 75,
          "review": 41.0,
          "cost": 100,
          "adoption": 100
        }
      },
      {
        "name": "hr-policy-bot",
        "score": 91.97,
        "coverage_pct": 100,
        "components": {
          "availability": 99.954,
          "errors": 99.41,
          "latency": 100,
          "scan": 62,
          "review": 78.0,
          "cost": 100,
          "adoption": 100
        }
      },
      {
        "name": "forecast-studio",
        "score": 93.03,
        "coverage_pct": 100,
        "components": {
          "availability": 99.43,
          "errors": 96.59,
          "latency": 100,
          "scan": 69,
          "review": 85.0,
          "cost": 100,
          "adoption": 100
        }
      },
      {
        "name": "churn-explorer",
        "score": 96.46,
        "coverage_pct": 100,
        "components": {
          "availability": 99.976,
          "errors": 99.59,
          "latency": 100,
          "scan": 85,
          "review": 88.0,
          "cost": 100,
          "adoption": 100
        }
      },
      {
        "name": "doc-intake",
        "score": 95.16,
        "coverage_pct": 100,
        "components": {
          "availability": 99.952,
          "errors": 99.61,
          "latency": 100,
          "scan": 73,
          "review": 93.0,
          "cost": 100,
          "adoption": 100
        }
      },
      {
        "name": "ops-runbook-bot",
        "score": 94.7,
        "coverage_pct": 100,
        "components": {
          "availability": 99.951,
          "errors": 99.83,
          "latency": 100,
          "scan": 69,
          "review": 94.0,
          "cost": 100,
          "adoption": 100
        }
      },
      {
        "name": "label-studio-lite",
        "score": 90.86,
        "coverage_pct": 100,
        "components": {
          "availability": 99.972,
          "errors": 99.83,
          "latency": 100,
          "scan": 91,
          "review": 72.0,
          "cost": 100,
          "adoption": 1
        }
      }
    ]
  },
  "api/model-prices": {
    "prices": [
      {
        "model": "databricks-claude-sonnet-4-5",
        "input_usd_per_mtok": 3.0,
        "output_usd_per_mtok": 15.0,
        "source": "list",
        "effective_from": "2026-10-01"
      },
      {
        "model": "databricks-gpt-oss-120b",
        "input_usd_per_mtok": 0.15,
        "output_usd_per_mtok": 0.6,
        "source": "list",
        "effective_from": "2026-10-01"
      },
      {
        "model": "databricks-llama-4-maverick",
        "input_usd_per_mtok": 0.5,
        "output_usd_per_mtok": 1.5,
        "source": "list",
        "effective_from": "2026-10-01"
      }
    ]
  },
  "api/monitor/cost": {
    "daily": [
      {
        "date": "2026-10-30",
        "component": "warehouse",
        "usd": 4.5,
        "basis": "duration-share estimate"
      },
      {
        "date": "2026-10-30",
        "component": "review tokens",
        "usd": null,
        "input_tokens": 4000,
        "output_tokens": 500,
        "basis": "unpriced"
      }
    ],
    "storage": [
      {
        "table_name": "otel_spans",
        "size_bytes": 104857600,
        "measured_at": "2026-10-30T09:27:00Z"
      }
    ]
  },
  "api/reach/fleet": {
    "mode": "hub",
    "apps": [
      {
        "workspace_name": "prod-eu",
        "workspace_id": "1272983411735654",
        "name": "claims-assistant",
        "app_state": "RUNNING",
        "requests_7d": 147000,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 73.0,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      },
      {
        "workspace_name": "prod-eu",
        "workspace_id": "1272983411735654",
        "name": "pricing-api",
        "app_state": "RUNNING",
        "requests_7d": 143717,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 123.65,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      },
      {
        "workspace_name": "prod-eu",
        "workspace_id": "1272983411735654",
        "name": "sales-cockpit",
        "app_state": "RUNNING",
        "requests_7d": 271467,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 92.85,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      },
      {
        "workspace_name": "prod-eu",
        "workspace_id": "1272983411735654",
        "name": "fraud-triage",
        "app_state": "RUNNING",
        "requests_7d": 63000,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 174.29,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      },
      {
        "workspace_name": "prod-eu",
        "workspace_id": "1272983411735654",
        "name": "supplier-portal",
        "app_state": "RUNNING",
        "requests_7d": 148099,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 174.92,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      },
      {
        "workspace_name": "prod-eu",
        "workspace_id": "1272983411735654",
        "name": "hr-policy-bot",
        "app_state": "RUNNING",
        "requests_7d": 267631,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 169.73,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      },
      {
        "workspace_name": "analytics-us",
        "workspace_id": "7781204459918823",
        "name": "forecast-studio",
        "app_state": "RUNNING",
        "requests_7d": 147000,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 171.63,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      },
      {
        "workspace_name": "analytics-us",
        "workspace_id": "7781204459918823",
        "name": "churn-explorer",
        "app_state": "RUNNING",
        "requests_7d": 290801,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 97.32,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      },
      {
        "workspace_name": "prod-eu",
        "workspace_id": "1272983411735654",
        "name": "doc-intake",
        "app_state": "RUNNING",
        "requests_7d": 197253,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 83.62,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      },
      {
        "workspace_name": "dev-eu",
        "workspace_id": "3348812290431187",
        "name": "ops-runbook-bot",
        "app_state": "RUNNING",
        "requests_7d": 106694,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 105.24,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      },
      {
        "workspace_name": "prod-eu",
        "workspace_id": "1272983411735654",
        "name": "legacy-reports",
        "app_state": "STOPPED",
        "requests_7d": 0,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 0.0,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      },
      {
        "workspace_name": "dev-eu",
        "workspace_id": "3348812290431187",
        "name": "label-studio-lite",
        "app_state": "RUNNING",
        "requests_7d": 280,
        "errors_7d": 20,
        "dbus_7d": 4,
        "usd_7d": 88.91,
        "snapshot_ts": "2026-10-30T09:27:00Z"
      }
    ]
  }
};
