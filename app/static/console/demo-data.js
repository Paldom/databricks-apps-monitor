window.MOCK = {
  "generated_at": "2026-10-30T09:30:00Z",
  "product": "Apps Monitor",
  "workspaces": [
    {
      "id": "1272983411735654",
      "name": "prod-eu",
      "region": "westeurope",
      "role": "hub",
      "status": "OK",
      "last_run": "2026-10-30T09:18:00Z"
    },
    {
      "id": "3348812290431187",
      "name": "dev-eu",
      "region": "westeurope",
      "role": "feeder",
      "status": "OK",
      "last_run": "2026-10-30T09:21:00Z"
    },
    {
      "id": "7781204459918823",
      "name": "analytics-us",
      "region": "eastus2",
      "role": "feeder",
      "status": "STALE",
      "last_run": "2026-10-30T05:50:00Z"
    }
  ],
  "apps": [
    {
      "id": "app-001",
      "name": "claims-assistant",
      "workspace": "prod-eu",
      "team": "Claims",
      "cost_center": "CC-410",
      "owner": "maria.kovacs@contoso.com",
      "kind": "agent",
      "health": "degraded",
      "status": "RUNNING",
      "version": "2.1.1",
      "deployed_at": "2026-10-27T11:30:00Z",
      "url": "https://claims-assistant-1000.aws.databricksapps.com",
      "sdk_version": null,
      "telemetry": {
        "otel_export": true,
        "envelope_coverage_pct": 72.1,
        "last_span_age_s": 12,
        "sampler_ratio": 0.2,
        "orphan_span_pct": 2.5
      },
      "last24h": {
        "requests": 21000,
        "error_rate_pct": 5.34,
        "p50_ms": 540,
        "p95_ms": 1874,
        "p99_ms": 4230,
        "uptime_pct": 99.655,
        "active_users": 256
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          886,
          1063,
          1087,
          1108,
          988,
          999,
          796,
          717,
          695,
          592,
          671,
          773,
          887,
          995,
          1096,
          1024,
          1077,
          930,
          805,
          803,
          697,
          677,
          685,
          771
        ],
        "p95_ms": [
          1603.11,
          1673.71,
          1982.49,
          1822.12,
          1729.5,
          1566.58,
          1604.08,
          1155.08,
          1099.75,
          1122.57,
          1115.95,
          1292.62,
          1540.04,
          1526.64,
          1828.26,
          1748.43,
          1764.59,
          1848.99,
          1469.85,
          1484.96,
          1016.31,
          1146.17,
          2594.77,
          4054.72
        ],
        "error_rate_pct": [
          2.86,
          3.28,
          3.89,
          4.64,
          2.98,
          2.74,
          2.71,
          3.22,
          1.58,
          2.9,
          2.1,
          2.97,
          3.59,
          3.49,
          4.36,
          4.83,
          3.57,
          4.55,
          2.9,
          3.04,
          2.5,
          1.8,
          8.73,
          16.66
        ]
      },
      "slo": {
        "availability_target": 99.9,
        "attainment_28d": 99.655,
        "error_budget_remaining_pct": -245.0,
        "latency_threshold_ms": 1500
      },
      "cost": {
        "mtd_usd": 1830.4,
        "dbu_usd": 312.87,
        "ai_usd": 1612.9,
        "idle_usd": 59.22,
        "budget_usd_month": 2000,
        "forecast_usd_month": 2290.0,
        "daily_30d": [
          49.25,
          51.55,
          58.64,
          60.64,
          60.42,
          62.27,
          60.42,
          57.51,
          55.26,
          47.63,
          41.3,
          38.45,
          37.97,
          41.91,
          52.04,
          51.87,
          66.25,
          65.25,
          69.84,
          69.74,
          72.29,
          69.48,
          61.47,
          53.78,
          55.67,
          52.71,
          48.19,
          50.07,
          50.94,
          60.77
        ],
        "usd_per_1k_requests": 2.347
      },
      "genai": {
        "models": [
          "databricks-claude-sonnet-4-5",
          "databricks-llama-4-maverick"
        ],
        "calls_24h": 4220,
        "input_tokens_24h": 16784984,
        "output_tokens_24h": 880748,
        "ttft_p95_ms": 925,
        "quality": {
          "relevance": 7.6,
          "faithfulness": 6.6,
          "toxicity": 0.0
        },
        "feedback": {
          "avg_stars": 3.6,
          "count_7d": 39
        },
        "error_classes_24h": {
          "rate_limit": 23,
          "timeout": 19,
          "policy": 0,
          "schema": 1,
          "server": 1
        },
        "guardrail_findings_7d": {
          "pii": 4,
          "jailbreak": 1,
          "toxicity": 0
        },
        "prompt_drift_novel_share": 0.31
      },
      "security": {
        "cve": {
          "critical": 0,
          "high": 0,
          "medium": 4,
          "low": 3
        },
        "secrets": 0,
        "review_verdict": "approve",
        "review_score": 8.0,
        "quality_score": 85,
        "outdated_packages": 1,
        "last_scan": "2026-10-29T17:30:00Z"
      },
      "governance": {
        "tags_complete": true,
        "auto_stop": "none",
        "permission_drift": false
      },
      "workspace_id": "1272983411735654",
      "description": "Demo agent for Claims.",
      "tags": {
        "team": "Claims",
        "cost_center": "CC-410",
        "env": "prod",
        "tier": "t1"
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
      "probe": {
        "uptime_24h": 99.655,
        "p95_ms": 180,
        "error_rate_1h": 0,
        "checks_24h": 1440
      },
      "usage_7d": {
        "peak_dau": 256,
        "requests_7d": 147000,
        "sessions_7d": 3072
      },
      "cost_7d": {
        "usd_7d": 73.0,
        "ai_calls_7d": 29540,
        "tokens_7d": 117494888
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "claims-assistant",
        "verdict": "approve",
        "score_overall": 8.0,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    },
    {
      "id": "app-002",
      "name": "pricing-api",
      "workspace": "prod-eu",
      "team": "Pricing",
      "cost_center": "CC-220",
      "owner": "tom.becker@contoso.com",
      "kind": "api",
      "health": "healthy",
      "status": "RUNNING",
      "version": "3.2.2",
      "deployed_at": "2026-10-30T07:30:00Z",
      "url": "https://pricing-api-1001.aws.databricksapps.com",
      "sdk_version": "0.1.0",
      "telemetry": {
        "otel_export": true,
        "envelope_coverage_pct": 92.2,
        "last_span_age_s": 95,
        "sampler_ratio": 0.2,
        "orphan_span_pct": 1.0
      },
      "last24h": {
        "requests": 20531,
        "error_rate_pct": 0.58,
        "p50_ms": 117,
        "p95_ms": 325,
        "p99_ms": 550,
        "uptime_pct": 99.974,
        "active_users": 662
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          805,
          1040,
          1017,
          1102,
          1112,
          1007,
          821,
          773,
          600,
          701,
          673,
          818,
          831,
          915,
          1048,
          1070,
          1064,
          982,
          905,
          793,
          618,
          597,
          653,
          800
        ],
        "p95_ms": [
          240.49,
          292.03,
          331.31,
          356.82,
          335.15,
          290.7,
          240.09,
          234.33,
          193.59,
          215.06,
          218.21,
          217.72,
          290.84,
          265.23,
          290.43,
          323.06,
          305.74,
          291.37,
          291.54,
          234.67,
          171.33,
          221.6,
          193.57,
          236.8
        ],
        "error_rate_pct": [
          0.43,
          0.3,
          0.4,
          0.48,
          0.35,
          0.48,
          0.33,
          0.34,
          0.18,
          0.36,
          0.32,
          0.3,
          0.4,
          0.3,
          0.34,
          0.55,
          0.31,
          0.41,
          0.34,
          0.34,
          0.3,
          0.28,
          0.27,
          0.41
        ]
      },
      "slo": {
        "availability_target": 99.9,
        "attainment_28d": 99.974,
        "error_budget_remaining_pct": 74.0,
        "latency_threshold_ms": 800
      },
      "cost": {
        "mtd_usd": 588.71,
        "dbu_usd": 529.93,
        "ai_usd": 58.78,
        "idle_usd": 55.41,
        "budget_usd_month": 900,
        "forecast_usd_month": 677.98,
        "daily_30d": [
          17.75,
          22.79,
          24.16,
          22.73,
          25.48,
          22.46,
          24.42,
          19.45,
          20.07,
          14.89,
          14.25,
          14.75,
          15.99,
          15.29,
          17.8,
          20.94,
          19.9,
          24.21,
          25.85,
          25.14,
          25.11,
          22.57,
          21.93,
          20.09,
          15.29,
          14.01,
          14.79,
          16.42,
          17.06,
          18.05
        ],
        "usd_per_1k_requests": 0.956
      },
      "genai": null,
      "security": {
        "cve": {
          "critical": 0,
          "high": 0,
          "medium": 1,
          "low": 1
        },
        "secrets": 0,
        "review_verdict": "approve",
        "review_score": 8.3,
        "quality_score": 67,
        "outdated_packages": 8,
        "last_scan": "2026-10-30T07:30:00Z"
      },
      "governance": {
        "tags_complete": true,
        "auto_stop": "night",
        "permission_drift": false
      },
      "workspace_id": "1272983411735654",
      "description": "Demo api for Pricing.",
      "tags": {
        "team": "Pricing",
        "cost_center": "CC-220",
        "env": "prod",
        "tier": "t1"
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
      "probe": {
        "uptime_24h": 99.974,
        "p95_ms": 189,
        "error_rate_1h": 0,
        "checks_24h": 1440
      },
      "usage_7d": {
        "peak_dau": 662,
        "requests_7d": 143717,
        "sessions_7d": 7944
      },
      "cost_7d": {
        "usd_7d": 123.65,
        "ai_calls_7d": 0,
        "tokens_7d": 0
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "pricing-api",
        "verdict": "approve",
        "score_overall": 8.3,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    },
    {
      "id": "app-003",
      "name": "sales-cockpit",
      "workspace": "prod-eu",
      "team": "Sales Ops",
      "cost_center": "CC-150",
      "owner": "lena.wolf@contoso.com",
      "kind": "web",
      "health": "healthy",
      "status": "RUNNING",
      "version": "1.16.7",
      "deployed_at": "2026-10-22T11:30:00Z",
      "url": "https://sales-cockpit-1002.aws.databricksapps.com",
      "sdk_version": "0.2.0",
      "telemetry": {
        "otel_export": true,
        "envelope_coverage_pct": 92.8,
        "last_span_age_s": 12,
        "sampler_ratio": 1.0,
        "orphan_span_pct": 2.0
      },
      "last24h": {
        "requests": 38781,
        "error_rate_pct": 0.38,
        "p50_ms": 110,
        "p95_ms": 368,
        "p99_ms": 754,
        "uptime_pct": 99.964,
        "active_users": 625
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          1650,
          1721,
          1894,
          2022,
          2065,
          1820,
          1534,
          1421,
          1388,
          1350,
          1403,
          1541,
          1520,
          1801,
          1939,
          1985,
          1906,
          1873,
          1593,
          1321,
          1202,
          1090,
          1356,
          1556
        ],
        "p95_ms": [
          304.96,
          321.35,
          339.97,
          341.3,
          355.76,
          349.36,
          264.53,
          285.93,
          205.84,
          233.15,
          210.33,
          272.79,
          330.76,
          324.12,
          352.35,
          357.45,
          328.12,
          321.33,
          282.48,
          254.56,
          245.61,
          212.29,
          231.94,
          242.55
        ],
        "error_rate_pct": [
          0.3,
          0.2,
          0.34,
          0.24,
          0.33,
          0.19,
          0.19,
          0.26,
          0.13,
          0.21,
          0.23,
          0.25,
          0.25,
          0.32,
          0.26,
          0.29,
          0.28,
          0.26,
          0.2,
          0.17,
          0.22,
          0.12,
          0.24,
          0.16
        ]
      },
      "slo": {
        "availability_target": 99.9,
        "attainment_28d": 99.964,
        "error_budget_remaining_pct": 64.0,
        "latency_threshold_ms": 800
      },
      "cost": {
        "mtd_usd": 397.92,
        "dbu_usd": 397.92,
        "ai_usd": 0,
        "idle_usd": 22.24,
        "budget_usd_month": 600,
        "forecast_usd_month": 401.55,
        "daily_30d": [
          12.63,
          14.9,
          14.99,
          15.79,
          15.56,
          14.84,
          16.52,
          13.74,
          13.68,
          11.64,
          9.18,
          10.52,
          11.27,
          12.04,
          11.28,
          12.42,
          15.76,
          16.07,
          16.5,
          15.78,
          15.99,
          15.67,
          13.34,
          13.38,
          12.63,
          9.16,
          8.69,
          10.13,
          12.07,
          11.95
        ],
        "usd_per_1k_requests": 0.342
      },
      "genai": null,
      "security": {
        "cve": {
          "critical": 0,
          "high": 0,
          "medium": 1,
          "low": 3
        },
        "secrets": 0,
        "review_verdict": "approve",
        "review_score": 8.9,
        "quality_score": 87,
        "outdated_packages": 10,
        "last_scan": "2026-10-29T17:30:00Z"
      },
      "governance": {
        "tags_complete": true,
        "auto_stop": "idle",
        "permission_drift": true
      },
      "workspace_id": "1272983411735654",
      "description": "Demo web for Sales Ops.",
      "tags": {
        "team": "Sales Ops",
        "cost_center": "CC-150",
        "env": "prod",
        "tier": "t1"
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
      "probe": {
        "uptime_24h": 99.964,
        "p95_ms": 198,
        "error_rate_1h": 0,
        "checks_24h": 1440
      },
      "usage_7d": {
        "peak_dau": 625,
        "requests_7d": 271467,
        "sessions_7d": 7500
      },
      "cost_7d": {
        "usd_7d": 92.85,
        "ai_calls_7d": 0,
        "tokens_7d": 0
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "sales-cockpit",
        "verdict": "approve",
        "score_overall": 8.9,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    },
    {
      "id": "app-004",
      "name": "fraud-triage",
      "workspace": "prod-eu",
      "team": "Risk",
      "cost_center": "CC-330",
      "owner": "arjun.rao@contoso.com",
      "kind": "agent",
      "health": "down",
      "status": "RUNNING",
      "version": "3.1.2",
      "deployed_at": "2026-10-30T07:30:00Z",
      "url": "https://fraud-triage-1003.aws.databricksapps.com",
      "sdk_version": "0.2.0",
      "telemetry": {
        "otel_export": true,
        "envelope_coverage_pct": 88.8,
        "last_span_age_s": 51,
        "sampler_ratio": 1.0,
        "orphan_span_pct": 1.0
      },
      "last24h": {
        "requests": 9000,
        "error_rate_pct": 45.08,
        "p50_ms": 1820,
        "p95_ms": 5704,
        "p99_ms": 10033,
        "uptime_pct": 91.489,
        "active_users": 257
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          387,
          413,
          457,
          504,
          464,
          436,
          341,
          305,
          276,
          244,
          284,
          315,
          411,
          409,
          421,
          497,
          435,
          398,
          363,
          297,
          277,
          293,
          275,
          349
        ],
        "p95_ms": [
          4096.44,
          5495.28,
          5144.88,
          5803.02,
          5430.21,
          4905.04,
          4711.13,
          3518.78,
          4097.31,
          3825.38,
          3181.95,
          4440.91,
          4887.23,
          5243.75,
          5852.69,
          5955.75,
          5544.53,
          4887.39,
          4698.62,
          3587.53,
          3945.84,
          3667.68,
          7582.85,
          11897.68
        ],
        "error_rate_pct": [
          30.67,
          30.53,
          40.3,
          38.37,
          34.14,
          36.07,
          18.32,
          27.03,
          26.56,
          24.09,
          29.42,
          26.24,
          19.57,
          22.17,
          35.38,
          42.1,
          30.68,
          29.55,
          18.95,
          14.99,
          21.76,
          15.68,
          73.28,
          100.0
        ]
      },
      "slo": {
        "availability_target": 99.9,
        "attainment_28d": 91.489,
        "error_budget_remaining_pct": -8411.0,
        "latency_threshold_ms": 1500
      },
      "cost": {
        "mtd_usd": 2169.71,
        "dbu_usd": 746.94,
        "ai_usd": 1422.77,
        "idle_usd": 55.68,
        "budget_usd_month": 2400,
        "forecast_usd_month": 2757.14,
        "daily_30d": [
          78.08,
          74.57,
          87.85,
          95.76,
          93.54,
          96.85,
          92.94,
          77.57,
          77.76,
          63.35,
          64.5,
          59.75,
          66.74,
          60.42,
          80.0,
          80.1,
          85.87,
          102.26,
          101.27,
          108.91,
          103.15,
          102.56,
          95.61,
          86.09,
          71.2,
          70.58,
          68.27,
          76.85,
          69.58,
          79.73
        ],
        "usd_per_1k_requests": 8.036
      },
      "genai": {
        "models": [
          "databricks-llama-4-maverick",
          "databricks-claude-sonnet-4-5"
        ],
        "calls_24h": 5906,
        "input_tokens_24h": 4880790,
        "output_tokens_24h": 2183675,
        "ttft_p95_ms": 735,
        "quality": {
          "relevance": 7.5,
          "faithfulness": 6.7,
          "toxicity": 0.3
        },
        "feedback": {
          "avg_stars": 4.6,
          "count_7d": 82
        },
        "error_classes_24h": {
          "rate_limit": 24,
          "timeout": 6,
          "policy": 1,
          "schema": 1,
          "server": 4
        },
        "guardrail_findings_7d": {
          "pii": 0,
          "jailbreak": 0,
          "toxicity": 0
        },
        "prompt_drift_novel_share": 0.24
      },
      "security": {
        "cve": {
          "critical": 1,
          "high": 2,
          "medium": 3,
          "low": 2
        },
        "secrets": 0,
        "review_verdict": "approve_with_comments",
        "review_score": 8.4,
        "quality_score": 78,
        "outdated_packages": 7,
        "last_scan": "2026-10-29T18:30:00Z"
      },
      "governance": {
        "tags_complete": true,
        "auto_stop": "none",
        "permission_drift": false
      },
      "workspace_id": "1272983411735654",
      "description": "Demo agent for Risk.",
      "tags": {
        "team": "Risk",
        "cost_center": "CC-330",
        "env": "prod",
        "tier": "t1"
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
      "probe": {
        "uptime_24h": 91.489,
        "p95_ms": 207,
        "error_rate_1h": 100,
        "checks_24h": 1440
      },
      "usage_7d": {
        "peak_dau": 257,
        "requests_7d": 63000,
        "sessions_7d": 3084
      },
      "cost_7d": {
        "usd_7d": 174.29,
        "ai_calls_7d": 41342,
        "tokens_7d": 34165530
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "fraud-triage",
        "verdict": "approve_with_comments",
        "score_overall": 8.4,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    },
    {
      "id": "app-005",
      "name": "supplier-portal",
      "workspace": "prod-eu",
      "team": "Procurement",
      "cost_center": "CC-505",
      "owner": "nina.horvath@contoso.com",
      "kind": "web",
      "health": "healthy",
      "status": "RUNNING",
      "version": "2.15.7",
      "deployed_at": "2026-10-27T11:30:00Z",
      "url": "https://supplier-portal-1004.aws.databricksapps.com",
      "sdk_version": "0.2.0",
      "telemetry": {
        "otel_export": true,
        "envelope_coverage_pct": 74.8,
        "last_span_age_s": 95,
        "sampler_ratio": 0.2,
        "orphan_span_pct": 2.7
      },
      "last24h": {
        "requests": 21157,
        "error_rate_pct": 0.58,
        "p50_ms": 89,
        "p95_ms": 212,
        "p99_ms": 425,
        "uptime_pct": 99.985,
        "active_users": 431
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          922,
          977,
          1051,
          1035,
          1043,
          961,
          853,
          753,
          768,
          608,
          605,
          814,
          838,
          915,
          1053,
          1167,
          998,
          1067,
          927,
          834,
          652,
          582,
          719,
          795
        ],
        "p95_ms": [
          154.71,
          210.77,
          203.62,
          204.18,
          217.9,
          202.89,
          166.54,
          128.43,
          143.97,
          122.96,
          148.81,
          150.7,
          157.03,
          173.02,
          224.7,
          208.22,
          211.19,
          175.48,
          185.27,
          147.79,
          150.35,
          129.32,
          118.92,
          144.79
        ],
        "error_rate_pct": [
          0.3,
          0.33,
          0.48,
          0.47,
          0.4,
          0.33,
          0.34,
          0.34,
          0.18,
          0.29,
          0.17,
          0.3,
          0.42,
          0.4,
          0.41,
          0.4,
          0.48,
          0.37,
          0.36,
          0.25,
          0.2,
          0.27,
          0.23,
          0.27
        ]
      },
      "slo": {
        "availability_target": 99.9,
        "attainment_28d": 99.985,
        "error_budget_remaining_pct": 85.0,
        "latency_threshold_ms": 800
      },
      "cost": {
        "mtd_usd": 749.66,
        "dbu_usd": 749.66,
        "ai_usd": 0,
        "idle_usd": 249.84,
        "budget_usd_month": 1000,
        "forecast_usd_month": 782.89,
        "daily_30d": [
          22.59,
          29.38,
          29.05,
          32.16,
          29.75,
          29.25,
          29.92,
          26.28,
          24.06,
          20.62,
          20.51,
          18.92,
          20.5,
          22.09,
          20.41,
          26.97,
          26.95,
          30.36,
          30.59,
          30.26,
          31.97,
          31.0,
          24.42,
          23.32,
          22.63,
          21.1,
          21.12,
          19.0,
          18.21,
          24.6
        ],
        "usd_per_1k_requests": 1.181
      },
      "genai": null,
      "security": {
        "cve": {
          "critical": 0,
          "high": 3,
          "medium": 4,
          "low": 6
        },
        "secrets": 1,
        "review_verdict": "reject",
        "review_score": 4.1,
        "quality_score": 75,
        "outdated_packages": 12,
        "last_scan": "2026-10-30T05:30:00Z"
      },
      "governance": {
        "tags_complete": false,
        "auto_stop": "none",
        "permission_drift": false
      },
      "workspace_id": "1272983411735654",
      "description": "Demo web for Procurement.",
      "tags": {
        "team": "Procurement",
        "cost_center": "CC-505",
        "env": "prod",
        "tier": "t1"
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
      "probe": {
        "uptime_24h": 99.985,
        "p95_ms": 216,
        "error_rate_1h": 0,
        "checks_24h": 1440
      },
      "usage_7d": {
        "peak_dau": 431,
        "requests_7d": 148099,
        "sessions_7d": 5172
      },
      "cost_7d": {
        "usd_7d": 174.92,
        "ai_calls_7d": 0,
        "tokens_7d": 0
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "supplier-portal",
        "verdict": "reject",
        "score_overall": 4.1,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    },
    {
      "id": "app-006",
      "name": "hr-policy-bot",
      "workspace": "prod-eu",
      "team": "People",
      "cost_center": "CC-610",
      "owner": "sam.okafor@contoso.com",
      "kind": "agent",
      "health": "healthy",
      "status": "RUNNING",
      "version": "1.0.2",
      "deployed_at": "2026-10-30T04:30:00Z",
      "url": "https://hr-policy-bot-1005.aws.databricksapps.com",
      "sdk_version": "0.2.0",
      "telemetry": {
        "otel_export": true,
        "envelope_coverage_pct": 89.4,
        "last_span_age_s": 51,
        "sampler_ratio": 1.0,
        "orphan_span_pct": 3.8
      },
      "last24h": {
        "requests": 38233,
        "error_rate_pct": 0.59,
        "p50_ms": 87,
        "p95_ms": 206,
        "p99_ms": 445,
        "uptime_pct": 99.954,
        "active_users": 606
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          1636,
          1855,
          1814,
          1854,
          1946,
          1819,
          1557,
          1306,
          1280,
          1039,
          1185,
          1381,
          1739,
          1838,
          2060,
          1983,
          1853,
          1712,
          1740,
          1459,
          1187,
          1042,
          1248,
          1450
        ],
        "p95_ms": [
          161.5,
          175.4,
          207.38,
          223.52,
          189.22,
          166.2,
          158.13,
          140.93,
          136.64,
          111.16,
          141.36,
          154.05,
          165.0,
          173.26,
          219.84,
          198.24,
          213.66,
          174.31,
          153.32,
          154.93,
          120.67,
          142.22,
          128.95,
          131.32
        ],
        "error_rate_pct": [
          0.29,
          0.38,
          0.47,
          0.55,
          0.35,
          0.37,
          0.29,
          0.42,
          0.19,
          0.16,
          0.17,
          0.28,
          0.45,
          0.49,
          0.49,
          0.56,
          0.53,
          0.36,
          0.28,
          0.41,
          0.34,
          0.16,
          0.32,
          0.28
        ]
      },
      "slo": {
        "availability_target": 99.9,
        "attainment_28d": 99.954,
        "error_budget_remaining_pct": 54.0,
        "latency_threshold_ms": 1500
      },
      "cost": {
        "mtd_usd": 2442.43,
        "dbu_usd": 727.43,
        "ai_usd": 1715.0,
        "idle_usd": 131.56,
        "budget_usd_month": 3400,
        "forecast_usd_month": 2648.8,
        "daily_30d": [
          76.03,
          82.5,
          94.89,
          101.38,
          113.14,
          97.87,
          106.54,
          86.88,
          81.02,
          80.94,
          75.41,
          66.8,
          62.16,
          74.47,
          81.3,
          100.46,
          99.05,
          110.74,
          125.37,
          113.32,
          117.4,
          118.06,
          108.83,
          87.46,
          78.55,
          72.61,
          83.92,
          74.86,
          88.88,
          100.83
        ],
        "usd_per_1k_requests": 2.129
      },
      "genai": {
        "models": [
          "databricks-gpt-oss-120b",
          "databricks-llama-4-maverick"
        ],
        "calls_24h": 861,
        "input_tokens_24h": 4192181,
        "output_tokens_24h": 301739,
        "ttft_p95_ms": 2391,
        "quality": {
          "relevance": 7.3,
          "faithfulness": 7.8,
          "toxicity": 0.6
        },
        "feedback": {
          "avg_stars": 4.5,
          "count_7d": 112
        },
        "error_classes_24h": {
          "rate_limit": 16,
          "timeout": 13,
          "policy": 6,
          "schema": 7,
          "server": 1
        },
        "guardrail_findings_7d": {
          "pii": 3,
          "jailbreak": 0,
          "toxicity": 0
        },
        "prompt_drift_novel_share": 0.02
      },
      "security": {
        "cve": {
          "critical": 0,
          "high": 0,
          "medium": 2,
          "low": 2
        },
        "secrets": 0,
        "review_verdict": "approve",
        "review_score": 7.8,
        "quality_score": 62,
        "outdated_packages": 4,
        "last_scan": "2026-10-29T09:30:00Z"
      },
      "governance": {
        "tags_complete": true,
        "auto_stop": "idle",
        "permission_drift": false
      },
      "workspace_id": "1272983411735654",
      "description": "Demo agent for People.",
      "tags": {
        "team": "People",
        "cost_center": "CC-610",
        "env": "prod",
        "tier": "t1"
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
      "probe": {
        "uptime_24h": 99.954,
        "p95_ms": 225,
        "error_rate_1h": 0,
        "checks_24h": 1440
      },
      "usage_7d": {
        "peak_dau": 606,
        "requests_7d": 267631,
        "sessions_7d": 7272
      },
      "cost_7d": {
        "usd_7d": 169.73,
        "ai_calls_7d": 6027,
        "tokens_7d": 29345267
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "hr-policy-bot",
        "verdict": "approve",
        "score_overall": 7.8,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    },
    {
      "id": "app-007",
      "name": "forecast-studio",
      "workspace": "analytics-us",
      "team": "Finance",
      "cost_center": "CC-120",
      "owner": "julia.mendes@contoso.com",
      "kind": "web",
      "health": "degraded",
      "status": "RUNNING",
      "version": "1.16.3",
      "deployed_at": "2026-10-27T11:30:00Z",
      "url": "https://forecast-studio-1006.aws.databricksapps.com",
      "sdk_version": "0.2.0",
      "telemetry": {
        "otel_export": true,
        "envelope_coverage_pct": 77.4,
        "last_span_age_s": 13800,
        "sampler_ratio": 0.2,
        "orphan_span_pct": 0.2
      },
      "last24h": {
        "requests": 21000,
        "error_rate_pct": 3.41,
        "p50_ms": 682,
        "p95_ms": 2231,
        "p99_ms": 3991,
        "uptime_pct": 99.43,
        "active_users": 323
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          883,
          925,
          1052,
          1025,
          990,
          1006,
          824,
          752,
          771,
          739,
          628,
          701,
          868,
          1053,
          1018,
          1100,
          1112,
          1030,
          924,
          730,
          647,
          616,
          643,
          724
        ],
        "p95_ms": [
          1757.76,
          1867.68,
          2053.2,
          2133.44,
          2353.08,
          1868.8,
          1590.62,
          1450.89,
          1285.02,
          1350.34,
          1465.15,
          1383.46,
          1768.7,
          1801.32,
          1950.12,
          2401.82,
          2051.24,
          1984.83,
          1728.52,
          1729.86,
          1279.2,
          1137.98,
          3004.92,
          4831.42
        ],
        "error_rate_pct": [
          1.63,
          1.72,
          2.51,
          2.12,
          2.63,
          2.68,
          2.27,
          1.12,
          1.79,
          1.82,
          1.4,
          1.16,
          1.83,
          1.68,
          3.17,
          1.93,
          2.81,
          2.87,
          2.48,
          2.23,
          1.48,
          1.36,
          6.03,
          9.74
        ]
      },
      "slo": {
        "availability_target": 99.5,
        "attainment_28d": 99.43,
        "error_budget_remaining_pct": -14.0,
        "latency_threshold_ms": 800
      },
      "cost": {
        "mtd_usd": 735.54,
        "dbu_usd": 735.54,
        "ai_usd": 0,
        "idle_usd": 44.88,
        "budget_usd_month": 1100,
        "forecast_usd_month": 835.07,
        "daily_30d": [
          24.44,
          26.56,
          30.52,
          31.15,
          28.92,
          29.99,
          28.87,
          25.29,
          22.12,
          23.31,
          20.03,
          18.02,
          16.49,
          21.17,
          23.91,
          24.1,
          24.65,
          30.38,
          31.83,
          31.32,
          29.29,
          27.65,
          27.96,
          22.92,
          19.23,
          17.31,
          16.41,
          19.07,
          19.3,
          23.36
        ],
        "usd_per_1k_requests": 1.168
      },
      "genai": null,
      "security": {
        "cve": {
          "critical": 0,
          "high": 0,
          "medium": 1,
          "low": 0
        },
        "secrets": 0,
        "review_verdict": "approve",
        "review_score": 8.5,
        "quality_score": 69,
        "outdated_packages": 10,
        "last_scan": "2026-10-29T07:30:00Z"
      },
      "governance": {
        "tags_complete": true,
        "auto_stop": "none",
        "permission_drift": false
      },
      "workspace_id": "7781204459918823",
      "description": "Demo web for Finance.",
      "tags": {
        "team": "Finance",
        "cost_center": "CC-120",
        "env": "prod",
        "tier": "t1"
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
      "probe": {
        "uptime_24h": 99.43,
        "p95_ms": 234,
        "error_rate_1h": 0,
        "checks_24h": 1440
      },
      "usage_7d": {
        "peak_dau": 323,
        "requests_7d": 147000,
        "sessions_7d": 3876
      },
      "cost_7d": {
        "usd_7d": 171.63,
        "ai_calls_7d": 0,
        "tokens_7d": 0
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "forecast-studio",
        "verdict": "approve",
        "score_overall": 8.5,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    },
    {
      "id": "app-008",
      "name": "churn-explorer",
      "workspace": "analytics-us",
      "team": "Marketing",
      "cost_center": "CC-140",
      "owner": "kai.lindqvist@contoso.com",
      "kind": "web",
      "health": "healthy",
      "status": "RUNNING",
      "version": "1.3.6",
      "deployed_at": "2026-10-27T11:30:00Z",
      "url": "https://churn-explorer-1007.aws.databricksapps.com",
      "sdk_version": "0.2.0",
      "telemetry": {
        "otel_export": true,
        "envelope_coverage_pct": 79.0,
        "last_span_age_s": 12,
        "sampler_ratio": 1.0,
        "orphan_span_pct": 1.9
      },
      "last24h": {
        "requests": 41543,
        "error_rate_pct": 0.41,
        "p50_ms": 98,
        "p95_ms": 269,
        "p99_ms": 462,
        "uptime_pct": 99.976,
        "active_users": 610
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          1878,
          1909,
          2246,
          2205,
          2218,
          1830,
          1830,
          1418,
          1323,
          1418,
          1470,
          1405,
          1633,
          1913,
          2112,
          2123,
          1975,
          1860,
          1809,
          1652,
          1197,
          1320,
          1445,
          1355
        ],
        "p95_ms": [
          233.4,
          221.53,
          267.15,
          271.69,
          268.63,
          231.67,
          210.9,
          192.75,
          164.61,
          169.95,
          165.75,
          184.98,
          189.56,
          248.5,
          261.23,
          254.76,
          275.97,
          257.16,
          212.96,
          171.06,
          167.17,
          140.26,
          148.62,
          184.57
        ],
        "error_rate_pct": [
          0.18,
          0.27,
          0.3,
          0.23,
          0.32,
          0.21,
          0.28,
          0.26,
          0.19,
          0.11,
          0.19,
          0.2,
          0.32,
          0.22,
          0.36,
          0.39,
          0.34,
          0.33,
          0.2,
          0.29,
          0.19,
          0.26,
          0.26,
          0.16
        ]
      },
      "slo": {
        "availability_target": 99.5,
        "attainment_28d": 99.976,
        "error_budget_remaining_pct": 95.2,
        "latency_threshold_ms": 800
      },
      "cost": {
        "mtd_usd": 417.1,
        "dbu_usd": 417.1,
        "ai_usd": 0,
        "idle_usd": 135.95,
        "budget_usd_month": 700,
        "forecast_usd_month": 529.78,
        "daily_30d": [
          12.7,
          14.9,
          17.2,
          16.26,
          18.46,
          16.29,
          16.82,
          13.63,
          13.19,
          13.03,
          10.08,
          9.79,
          10.61,
          10.82,
          11.2,
          13.02,
          14.38,
          17.7,
          17.71,
          18.46,
          15.99,
          16.74,
          13.56,
          13.27,
          12.24,
          10.5,
          11.48,
          10.75,
          11.54,
          13.55
        ],
        "usd_per_1k_requests": 0.335
      },
      "genai": null,
      "security": {
        "cve": {
          "critical": 0,
          "high": 0,
          "medium": 0,
          "low": 2
        },
        "secrets": 0,
        "review_verdict": "approve_with_comments",
        "review_score": 8.8,
        "quality_score": 85,
        "outdated_packages": 11,
        "last_scan": "2026-10-29T07:30:00Z"
      },
      "governance": {
        "tags_complete": false,
        "auto_stop": "idle",
        "permission_drift": false
      },
      "workspace_id": "7781204459918823",
      "description": "Demo web for Marketing.",
      "tags": {
        "team": "Marketing",
        "cost_center": "CC-140",
        "env": "prod",
        "tier": "t1"
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
      "probe": {
        "uptime_24h": 99.976,
        "p95_ms": 243,
        "error_rate_1h": 0,
        "checks_24h": 1440
      },
      "usage_7d": {
        "peak_dau": 610,
        "requests_7d": 290801,
        "sessions_7d": 7320
      },
      "cost_7d": {
        "usd_7d": 97.32,
        "ai_calls_7d": 0,
        "tokens_7d": 0
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "churn-explorer",
        "verdict": "approve_with_comments",
        "score_overall": 8.8,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    },
    {
      "id": "app-009",
      "name": "doc-intake",
      "workspace": "prod-eu",
      "team": "Claims",
      "cost_center": "CC-410",
      "owner": "maria.kovacs@contoso.com",
      "kind": "api",
      "health": "healthy",
      "status": "RUNNING",
      "version": "3.9.9",
      "deployed_at": "2026-10-13T17:30:00Z",
      "url": "https://doc-intake-1008.aws.databricksapps.com",
      "sdk_version": "0.1.0",
      "telemetry": {
        "otel_export": true,
        "envelope_coverage_pct": 92.0,
        "last_span_age_s": 12,
        "sampler_ratio": 1.0,
        "orphan_span_pct": 0.9
      },
      "last24h": {
        "requests": 28179,
        "error_rate_pct": 0.39,
        "p50_ms": 109,
        "p95_ms": 266,
        "p99_ms": 520,
        "uptime_pct": 99.952,
        "active_users": 408
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          1204,
          1302,
          1396,
          1361,
          1426,
          1347,
          1067,
          923,
          936,
          835,
          925,
          1035,
          1154,
          1274,
          1342,
          1436,
          1505,
          1241,
          1060,
          1098,
          969,
          869,
          817,
          944
        ],
        "p95_ms": [
          221.6,
          227.15,
          275.45,
          290.85,
          235.26,
          256.47,
          233.69,
          191.24,
          170.9,
          165.02,
          167.66,
          185.82,
          194.98,
          212.82,
          235.55,
          240.74,
          242.15,
          221.27,
          234.7,
          165.18,
          172.72,
          167.94,
          150.62,
          181.58
        ],
        "error_rate_pct": [
          0.24,
          0.29,
          0.31,
          0.28,
          0.3,
          0.26,
          0.17,
          0.22,
          0.26,
          0.21,
          0.18,
          0.21,
          0.21,
          0.25,
          0.35,
          0.23,
          0.31,
          0.21,
          0.31,
          0.17,
          0.21,
          0.12,
          0.24,
          0.27
        ]
      },
      "slo": {
        "availability_target": 99.9,
        "attainment_28d": 99.952,
        "error_budget_remaining_pct": 52.0,
        "latency_threshold_ms": 800
      },
      "cost": {
        "mtd_usd": 404.29,
        "dbu_usd": 358.39,
        "ai_usd": 45.9,
        "idle_usd": 136.19,
        "budget_usd_month": 800,
        "forecast_usd_month": 429.88,
        "daily_30d": [
          12.27,
          15.21,
          16.46,
          17.18,
          17.95,
          17.67,
          14.91,
          15.33,
          13.84,
          10.38,
          10.58,
          9.24,
          11.36,
          11.89,
          11.3,
          12.56,
          15.97,
          15.15,
          16.38,
          17.1,
          16.07,
          16.41,
          15.31,
          14.07,
          12.42,
          10.66,
          10.05,
          10.35,
          9.64,
          10.83
        ],
        "usd_per_1k_requests": 0.478
      },
      "genai": null,
      "security": {
        "cve": {
          "critical": 0,
          "high": 0,
          "medium": 1,
          "low": 4
        },
        "secrets": 0,
        "review_verdict": "approve",
        "review_score": 9.3,
        "quality_score": 73,
        "outdated_packages": 6,
        "last_scan": "2026-10-29T13:30:00Z"
      },
      "governance": {
        "tags_complete": true,
        "auto_stop": "night",
        "permission_drift": false
      },
      "workspace_id": "1272983411735654",
      "description": "Demo api for Claims.",
      "tags": {
        "team": "Claims",
        "cost_center": "CC-410",
        "env": "prod",
        "tier": "t1"
      },
      "resources": [
        {
          "name": "analytics",
          "genie_space": {
            "id": "genie-demo"
          }
        }
      ],
      "probe": {
        "uptime_24h": 99.952,
        "p95_ms": 252,
        "error_rate_1h": 0,
        "checks_24h": 1440
      },
      "usage_7d": {
        "peak_dau": 408,
        "requests_7d": 197253,
        "sessions_7d": 4896
      },
      "cost_7d": {
        "usd_7d": 83.62,
        "ai_calls_7d": 0,
        "tokens_7d": 0
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "doc-intake",
        "verdict": "approve",
        "score_overall": 9.3,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    },
    {
      "id": "app-010",
      "name": "ops-runbook-bot",
      "workspace": "dev-eu",
      "team": "Platform",
      "cost_center": "CC-900",
      "owner": "dev.platform@contoso.com",
      "kind": "agent",
      "health": "healthy",
      "status": "RUNNING",
      "version": "1.4.0",
      "deployed_at": "2026-10-13T17:30:00Z",
      "url": "https://ops-runbook-bot-1009.aws.databricksapps.com",
      "sdk_version": "0.2.0",
      "telemetry": {
        "otel_export": true,
        "envelope_coverage_pct": 92.1,
        "last_span_age_s": 12,
        "sampler_ratio": 0.2,
        "orphan_span_pct": 4.6
      },
      "last24h": {
        "requests": 15242,
        "error_rate_pct": 0.17,
        "p50_ms": 55,
        "p95_ms": 186,
        "p99_ms": 436,
        "uptime_pct": 99.951,
        "active_users": 362
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          675,
          755,
          822,
          739,
          819,
          767,
          692,
          506,
          460,
          427,
          438,
          600,
          675,
          732,
          814,
          811,
          746,
          664,
          584,
          588,
          460,
          453,
          488,
          495
        ],
        "p95_ms": [
          139.75,
          159.31,
          189.04,
          181.09,
          174.35,
          184.66,
          148.94,
          143.27,
          120.98,
          94.15,
          113.34,
          127.84,
          158.96,
          161.7,
          188.63,
          187.41,
          170.47,
          180.88,
          133.58,
          142.1,
          104.32,
          93.05,
          105.5,
          139.95
        ],
        "error_rate_pct": [
          0.13,
          0.08,
          0.12,
          0.13,
          0.14,
          0.09,
          0.1,
          0.08,
          0.1,
          0.06,
          0.11,
          0.07,
          0.08,
          0.13,
          0.12,
          0.1,
          0.13,
          0.09,
          0.12,
          0.1,
          0.1,
          0.09,
          0.07,
          0.08
        ]
      },
      "slo": {
        "availability_target": 99.5,
        "attainment_28d": 99.951,
        "error_budget_remaining_pct": 90.2,
        "latency_threshold_ms": 1500
      },
      "cost": {
        "mtd_usd": 840.66,
        "dbu_usd": 451.02,
        "ai_usd": 389.64,
        "idle_usd": 84.84,
        "budget_usd_month": 1400,
        "forecast_usd_month": 1057.29,
        "daily_30d": [
          25.7,
          33.36,
          31.23,
          34.08,
          35.06,
          38.04,
          34.07,
          30.87,
          30.84,
          24.56,
          23.93,
          23.55,
          25.35,
          27.2,
          29.52,
          31.38,
          34.84,
          36.95,
          42.85,
          42.55,
          42.26,
          37.04,
          35.62,
          34.21,
          30.08,
          25.35,
          26.32,
          29.28,
          27.74,
          30.74
        ],
        "usd_per_1k_requests": 1.838
      },
      "genai": {
        "models": [
          "databricks-gpt-oss-120b",
          "databricks-llama-4-maverick"
        ],
        "calls_24h": 3436,
        "input_tokens_24h": 9925994,
        "output_tokens_24h": 1576046,
        "ttft_p95_ms": 1087,
        "quality": {
          "relevance": 7.4,
          "faithfulness": 9.2,
          "toxicity": 0.6
        },
        "feedback": {
          "avg_stars": 3.6,
          "count_7d": 182
        },
        "error_classes_24h": {
          "rate_limit": 6,
          "timeout": 6,
          "policy": 3,
          "schema": 2,
          "server": 1
        },
        "guardrail_findings_7d": {
          "pii": 2,
          "jailbreak": 2,
          "toxicity": 0
        },
        "prompt_drift_novel_share": 0.11
      },
      "security": {
        "cve": {
          "critical": 0,
          "high": 0,
          "medium": 2,
          "low": 6
        },
        "secrets": 0,
        "review_verdict": "approve_with_comments",
        "review_score": 9.4,
        "quality_score": 69,
        "outdated_packages": 11,
        "last_scan": "2026-10-30T04:30:00Z"
      },
      "governance": {
        "tags_complete": true,
        "auto_stop": "night",
        "permission_drift": false
      },
      "workspace_id": "3348812290431187",
      "description": "Demo agent for Platform.",
      "tags": {
        "team": "Platform",
        "cost_center": "CC-900",
        "env": "dev",
        "tier": "t1"
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
      "probe": {
        "uptime_24h": 99.951,
        "p95_ms": 261,
        "error_rate_1h": 0,
        "checks_24h": 1440
      },
      "usage_7d": {
        "peak_dau": 362,
        "requests_7d": 106694,
        "sessions_7d": 4344
      },
      "cost_7d": {
        "usd_7d": 105.24,
        "ai_calls_7d": 24052,
        "tokens_7d": 69481958
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "ops-runbook-bot",
        "verdict": "approve_with_comments",
        "score_overall": 9.4,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    },
    {
      "id": "app-011",
      "name": "legacy-reports",
      "workspace": "prod-eu",
      "team": "Finance",
      "cost_center": "CC-120",
      "owner": "julia.mendes@contoso.com",
      "kind": "web",
      "health": "stopped",
      "status": "STOPPED",
      "version": "4.14.0",
      "deployed_at": "2026-10-30T07:30:00Z",
      "url": "https://legacy-reports-1010.aws.databricksapps.com",
      "sdk_version": null,
      "telemetry": {
        "otel_export": false,
        "envelope_coverage_pct": 0,
        "last_span_age_s": null,
        "sampler_ratio": 1.0,
        "orphan_span_pct": 5.1
      },
      "last24h": {
        "requests": 0,
        "error_rate_pct": 0.0,
        "p50_ms": 0,
        "p95_ms": 0,
        "p99_ms": 0,
        "uptime_pct": null,
        "active_users": 0
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "p95_ms": [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "error_rate_pct": [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      },
      "slo": {
        "availability_target": 99.9,
        "attainment_28d": null,
        "error_budget_remaining_pct": null,
        "latency_threshold_ms": 800
      },
      "cost": {
        "mtd_usd": 0,
        "dbu_usd": 0,
        "ai_usd": 0,
        "idle_usd": 0.0,
        "budget_usd_month": 600,
        "forecast_usd_month": 0.0,
        "daily_30d": [
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ],
        "usd_per_1k_requests": null
      },
      "genai": null,
      "security": {
        "cve": {
          "critical": 0,
          "high": 0,
          "medium": 0,
          "low": 4
        },
        "secrets": 0,
        "review_verdict": "approve",
        "review_score": 8.4,
        "quality_score": 71,
        "outdated_packages": 14,
        "last_scan": "2026-10-29T12:30:00Z"
      },
      "governance": {
        "tags_complete": true,
        "auto_stop": "none",
        "permission_drift": false
      },
      "workspace_id": "1272983411735654",
      "description": "Demo web for Finance.",
      "tags": {
        "team": "Finance",
        "cost_center": "CC-120",
        "env": "dev",
        "tier": "t1"
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
      "probe": {
        "uptime_24h": null,
        "p95_ms": null,
        "error_rate_1h": null,
        "checks_24h": 0
      },
      "usage_7d": {
        "peak_dau": 0,
        "requests_7d": 0,
        "sessions_7d": 0
      },
      "cost_7d": {
        "usd_7d": 0.0,
        "ai_calls_7d": 0,
        "tokens_7d": 0
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "legacy-reports",
        "verdict": "approve",
        "score_overall": 8.4,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    },
    {
      "id": "app-012",
      "name": "label-studio-lite",
      "workspace": "dev-eu",
      "team": "Data Science",
      "cost_center": "CC-720",
      "owner": "ines.petit@contoso.com",
      "kind": "web",
      "health": "idle",
      "status": "RUNNING",
      "version": "2.16.5",
      "deployed_at": "2026-10-30T07:30:00Z",
      "url": "https://label-studio-lite-1011.aws.databricksapps.com",
      "sdk_version": null,
      "telemetry": {
        "otel_export": true,
        "envelope_coverage_pct": 86.2,
        "last_span_age_s": 95,
        "sampler_ratio": 0.2,
        "orphan_span_pct": 0.1
      },
      "last24h": {
        "requests": 40,
        "error_rate_pct": 0.17,
        "p50_ms": 75,
        "p95_ms": 250,
        "p99_ms": 450,
        "uptime_pct": 99.972,
        "active_users": 1
      },
      "series_24h": {
        "hours": [
          "2026-10-29T10:00:00Z",
          "2026-10-29T11:00:00Z",
          "2026-10-29T12:00:00Z",
          "2026-10-29T13:00:00Z",
          "2026-10-29T14:00:00Z",
          "2026-10-29T15:00:00Z",
          "2026-10-29T16:00:00Z",
          "2026-10-29T17:00:00Z",
          "2026-10-29T18:00:00Z",
          "2026-10-29T19:00:00Z",
          "2026-10-29T20:00:00Z",
          "2026-10-29T21:00:00Z",
          "2026-10-29T22:00:00Z",
          "2026-10-29T23:00:00Z",
          "2026-10-30T00:00:00Z",
          "2026-10-30T01:00:00Z",
          "2026-10-30T02:00:00Z",
          "2026-10-30T03:00:00Z",
          "2026-10-30T04:00:00Z",
          "2026-10-30T05:00:00Z",
          "2026-10-30T06:00:00Z",
          "2026-10-30T07:00:00Z",
          "2026-10-30T08:00:00Z",
          "2026-10-30T09:00:00Z"
        ],
        "requests": [
          2,
          2,
          2,
          2,
          2,
          2,
          2,
          2,
          1,
          1,
          1,
          1,
          2,
          2,
          2,
          2,
          2,
          2,
          2,
          1,
          1,
          1,
          1,
          1
        ],
        "p95_ms": [
          185.95,
          240.07,
          237.9,
          235.6,
          224.77,
          238.83,
          215.48,
          181.71,
          155.16,
          153.1,
          143.0,
          198.19,
          192.66,
          231.94,
          259.24,
          265.81,
          241.71,
          214.72,
          202.41,
          156.26,
          173.39,
          142.74,
          174.23,
          163.37
        ],
        "error_rate_pct": [
          0.09,
          0.1,
          0.12,
          0.11,
          0.09,
          0.13,
          0.09,
          0.07,
          0.07,
          0.08,
          0.08,
          0.1,
          0.11,
          0.11,
          0.15,
          0.15,
          0.09,
          0.14,
          0.13,
          0.11,
          0.06,
          0.1,
          0.09,
          0.06
        ]
      },
      "slo": {
        "availability_target": 99.5,
        "attainment_28d": 99.972,
        "error_budget_remaining_pct": 94.4,
        "latency_threshold_ms": 800
      },
      "cost": {
        "mtd_usd": 381.05,
        "dbu_usd": 381.05,
        "ai_usd": 0,
        "idle_usd": 354.38,
        "budget_usd_month": 600,
        "forecast_usd_month": 375.42,
        "daily_30d": [
          13.85,
          14.39,
          14.43,
          14.71,
          14.95,
          14.78,
          15.27,
          12.97,
          11.16,
          11.86,
          10.69,
          8.7,
          10.68,
          10.62,
          12.12,
          13.13,
          14.99,
          15.79,
          16.58,
          15.09,
          15.94,
          14.65,
          13.98,
          11.89,
          11.81,
          10.09,
          8.95,
          9.01,
          9.43,
          11.39
        ],
        "usd_per_1k_requests": 317.542
      },
      "genai": null,
      "security": {
        "cve": {
          "critical": 0,
          "high": 0,
          "medium": 0,
          "low": 3
        },
        "secrets": 0,
        "review_verdict": "approve",
        "review_score": 7.2,
        "quality_score": 91,
        "outdated_packages": 3,
        "last_scan": "2026-10-29T17:30:00Z"
      },
      "governance": {
        "tags_complete": false,
        "auto_stop": "none",
        "permission_drift": false
      },
      "workspace_id": "3348812290431187",
      "description": "Demo web for Data Science.",
      "tags": {},
      "resources": [
        {
          "name": "model",
          "serving_endpoint": {
            "name": "claims-model",
            "permission": "CAN_QUERY"
          }
        }
      ],
      "probe": {
        "uptime_24h": 99.972,
        "p95_ms": 279,
        "error_rate_1h": 0,
        "checks_24h": 1440
      },
      "usage_7d": {
        "peak_dau": 1,
        "requests_7d": 280,
        "sessions_7d": 12
      },
      "cost_7d": {
        "usd_7d": 88.91,
        "ai_calls_7d": 0,
        "tokens_7d": 0
      },
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
        "scanned_at": "2026-10-30T09:27:00Z",
        "has_npm": true
      },
      "review": {
        "name": "label-studio-lite",
        "verdict": "approve",
        "score_overall": 7.2,
        "summary": "Demo advisory: review dependency freshness and retry limits.",
        "model": "demo-reviewer",
        "reviewed_at": "2026-10-30T09:27:00Z"
      }
    }
  ],
  "alerts": [
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
    },
    {
      "id": "al-1024",
      "app": "pricing-api",
      "rule": "anomaly_traffic",
      "severity": "info",
      "state": "resolved",
      "since": "2026-10-29T01:50:00Z",
      "message": "Traffic 3.4x above 7-day baseline (resolved after 40 min)",
      "muted": false
    },
    {
      "id": "al-1019",
      "app": "hr-policy-bot",
      "rule": "slo_ticket",
      "severity": "warning",
      "state": "resolved",
      "since": "2026-10-27T09:50:00Z",
      "message": "Availability budget burn 1.2x over 3 days",
      "muted": false
    }
  ],
  "timeline": [
    {
      "ts": "2026-10-30T08:45:00Z",
      "type": "deploy",
      "app": "fraud-triage",
      "text": "Deployment 3.4.0 (git 9f2c1ab) by arjun.rao"
    },
    {
      "ts": "2026-10-30T08:52:00Z",
      "type": "alert",
      "app": "fraud-triage",
      "text": "app_down fired (critical)"
    },
    {
      "ts": "2026-10-30T08:59:00Z",
      "type": "alert",
      "app": "fraud-triage",
      "text": "slo_fast_burn fired (critical)"
    },
    {
      "ts": "2026-10-30T09:10:00Z",
      "type": "note",
      "app": "fraud-triage",
      "text": "Error group 7c1e: psycopg.OperationalError spiking since deploy"
    },
    {
      "ts": "2026-10-30T07:10:00Z",
      "type": "alert",
      "app": "claims-assistant",
      "text": "slo_slow_burn fired (high)"
    },
    {
      "ts": "2026-10-30T06:50:00Z",
      "type": "anomaly",
      "app": "claims-assistant",
      "text": "p95 2,410 ms vs 7-day baseline 980\u00b1210 ms"
    },
    {
      "ts": "2026-10-30T04:30:00Z",
      "type": "deploy",
      "app": "claims-assistant",
      "text": "Deployment 2.11.3 \u2014 prompt template v14"
    },
    {
      "ts": "2026-10-29T22:30:00Z",
      "type": "maintenance",
      "app": "legacy-reports",
      "text": "Night auto-stop (muted app_stopped until 06:00)"
    },
    {
      "ts": "2026-10-29T02:30:00Z",
      "type": "deploy",
      "app": "pricing-api",
      "text": "Deployment 1.18.2"
    }
  ],
  "error_groups": [
    {
      "fingerprint": "7c1e09a2b4f1",
      "app": "fraud-triage",
      "type": "psycopg.OperationalError",
      "message": "connection to Lakebase instance 'risk-db' timed out after 10s",
      "count_24h": 1874,
      "first_seen": "2026-10-30T08:46:00Z",
      "last_seen": "2026-10-30T09:29:20Z",
      "new_since_deploy": true,
      "sample_trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
      "route": "POST /api/score"
    },
    {
      "fingerprint": "a90d33e1c7b2",
      "app": "claims-assistant",
      "type": "RateLimitError",
      "message": "429 from databricks-claude-sonnet-4-5: QPM limit exceeded",
      "count_24h": 212,
      "first_seen": "2026-10-30T05:30:00Z",
      "last_seen": "2026-10-30T09:27:00Z",
      "new_since_deploy": true,
      "sample_trace_id": "0af7651916cd43dd8448eb211c80319c",
      "route": "POST /api/chat"
    },
    {
      "fingerprint": "1b77e0f2d3a8",
      "app": "claims-assistant",
      "type": "TimeoutError",
      "message": "tool 'policy_lookup' exceeded 30s",
      "count_24h": 64,
      "first_seen": "2026-10-24T09:30:00Z",
      "last_seen": "2026-10-30T09:21:00Z",
      "new_since_deploy": false,
      "sample_trace_id": "0af7651916cd43dd8448eb211c80319c",
      "route": "POST /api/chat"
    },
    {
      "fingerprint": "e4c2a1b9f0d3",
      "app": "forecast-studio",
      "type": "KeyError",
      "message": "'fiscal_week' missing from forecast payload",
      "count_24h": 37,
      "first_seen": "2026-10-28T09:30:00Z",
      "last_seen": "2026-10-30T05:30:00Z",
      "new_since_deploy": false,
      "sample_trace_id": null,
      "route": "GET /api/forecast"
    },
    {
      "fingerprint": "5d6e7f8a9b0c",
      "app": "sales-cockpit",
      "type": "BrowserError",
      "message": "TypeError: Cannot read properties of undefined (reading 'region') at Chart.tsx:88",
      "count_24h": 19,
      "first_seen": "2026-10-29T09:30:00Z",
      "last_seen": "2026-10-30T08:30:00Z",
      "new_since_deploy": false,
      "sample_trace_id": null,
      "route": "/pipeline"
    }
  ],
  "trace_example": {
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
  "synthetics": [
    {
      "app": "fraud-triage",
      "journey": "score a claim",
      "vantage": "internal",
      "ok": false,
      "failed_step": "POST /api/score",
      "failure_stage": "http",
      "last_run": "2026-10-30T09:26:00Z",
      "history": [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0
      ]
    },
    {
      "app": "fraud-triage",
      "journey": "score a claim",
      "vantage": "external",
      "ok": false,
      "failed_step": "POST /api/score",
      "failure_stage": "http",
      "last_run": "2026-10-30T09:24:00Z",
      "history": [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0
      ]
    },
    {
      "app": "claims-assistant",
      "journey": "ask a coverage question",
      "vantage": "internal",
      "ok": true,
      "failed_step": null,
      "failure_stage": null,
      "last_run": "2026-10-30T09:26:00Z",
      "history": [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1
      ]
    },
    {
      "app": "supplier-portal",
      "journey": "submit invoice",
      "vantage": "external",
      "ok": true,
      "failed_step": null,
      "failure_stage": null,
      "last_run": "2026-10-30T09:24:00Z",
      "history": [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1
      ]
    },
    {
      "app": "pricing-api",
      "journey": "quote + price",
      "vantage": "internal",
      "ok": true,
      "failed_step": null,
      "failure_stage": null,
      "last_run": "2026-10-30T09:26:00Z",
      "history": [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1
      ]
    }
  ],
  "funnel_example": {
    "app": "claims-assistant",
    "funnel": "claim question to answer",
    "by_version": {
      "2.11.3": [
        {
          "step": "open_chat",
          "sessions": 1840
        },
        {
          "step": "ask_question",
          "sessions": 1502
        },
        {
          "step": "tool_lookup",
          "sessions": 1210
        },
        {
          "step": "answer_shown",
          "sessions": 988
        },
        {
          "step": "thumbs_up",
          "sessions": 301
        }
      ],
      "2.11.2": [
        {
          "step": "open_chat",
          "sessions": 2120
        },
        {
          "step": "ask_question",
          "sessions": 1790
        },
        {
          "step": "tool_lookup",
          "sessions": 1480
        },
        {
          "step": "answer_shown",
          "sessions": 1391
        },
        {
          "step": "thumbs_up",
          "sessions": 462
        }
      ]
    }
  },
  "cohorts_example": {
    "app": "sales-cockpit",
    "weeks": [
      "2026-09-07",
      "2026-09-14",
      "2026-09-21",
      "2026-09-28",
      "2026-10-05"
    ],
    "retention_pct": [
      [
        100,
        62,
        51,
        47,
        44
      ],
      [
        100,
        58,
        49,
        45
      ],
      [
        100,
        66,
        55
      ],
      [
        100,
        60
      ],
      [
        100
      ]
    ],
    "sizes": [
      84,
      91,
      77,
      102,
      95
    ]
  },
  "cost": {
    "days": [
      "2026-10-01",
      "2026-10-02",
      "2026-10-03",
      "2026-10-04",
      "2026-10-05",
      "2026-10-06",
      "2026-10-07",
      "2026-10-08",
      "2026-10-09",
      "2026-10-10",
      "2026-10-11",
      "2026-10-12",
      "2026-10-13",
      "2026-10-14",
      "2026-10-15",
      "2026-10-16",
      "2026-10-17",
      "2026-10-18",
      "2026-10-19",
      "2026-10-20",
      "2026-10-21",
      "2026-10-22",
      "2026-10-23",
      "2026-10-24",
      "2026-10-25",
      "2026-10-26",
      "2026-10-27",
      "2026-10-28",
      "2026-10-29",
      "2026-10-30"
    ],
    "by_team": {
      "Claims": [
        61.52,
        66.76,
        75.1,
        77.82,
        78.37,
        79.94,
        75.33,
        72.84,
        69.1,
        58.01,
        51.88,
        47.69,
        49.33,
        53.8,
        63.34,
        64.43,
        82.22,
        80.4,
        86.22,
        86.84,
        88.36,
        85.89,
        76.78,
        67.85,
        68.09,
        63.37,
        58.24,
        60.42,
        60.58,
        71.6
      ],
      "Data Science": [
        13.85,
        14.39,
        14.43,
        14.71,
        14.95,
        14.78,
        15.27,
        12.97,
        11.16,
        11.86,
        10.69,
        8.7,
        10.68,
        10.62,
        12.12,
        13.13,
        14.99,
        15.79,
        16.58,
        15.09,
        15.94,
        14.65,
        13.98,
        11.89,
        11.81,
        10.09,
        8.95,
        9.01,
        9.43,
        11.39
      ],
      "Finance": [
        24.44,
        26.56,
        30.52,
        31.15,
        28.92,
        29.99,
        28.87,
        25.29,
        22.12,
        23.31,
        20.03,
        18.02,
        16.49,
        21.17,
        23.91,
        24.1,
        24.65,
        30.38,
        31.83,
        31.32,
        29.29,
        27.65,
        27.96,
        22.92,
        19.23,
        17.31,
        16.41,
        19.07,
        19.3,
        23.36
      ],
      "Marketing": [
        12.7,
        14.9,
        17.2,
        16.26,
        18.46,
        16.29,
        16.82,
        13.63,
        13.19,
        13.03,
        10.08,
        9.79,
        10.61,
        10.82,
        11.2,
        13.02,
        14.38,
        17.7,
        17.71,
        18.46,
        15.99,
        16.74,
        13.56,
        13.27,
        12.24,
        10.5,
        11.48,
        10.75,
        11.54,
        13.55
      ],
      "People": [
        76.03,
        82.5,
        94.89,
        101.38,
        113.14,
        97.87,
        106.54,
        86.88,
        81.02,
        80.94,
        75.41,
        66.8,
        62.16,
        74.47,
        81.3,
        100.46,
        99.05,
        110.74,
        125.37,
        113.32,
        117.4,
        118.06,
        108.83,
        87.46,
        78.55,
        72.61,
        83.92,
        74.86,
        88.88,
        100.83
      ],
      "Platform": [
        25.7,
        33.36,
        31.23,
        34.08,
        35.06,
        38.04,
        34.07,
        30.87,
        30.84,
        24.56,
        23.93,
        23.55,
        25.35,
        27.2,
        29.52,
        31.38,
        34.84,
        36.95,
        42.85,
        42.55,
        42.26,
        37.04,
        35.62,
        34.21,
        30.08,
        25.35,
        26.32,
        29.28,
        27.74,
        30.74
      ],
      "Pricing": [
        17.75,
        22.79,
        24.16,
        22.73,
        25.48,
        22.46,
        24.42,
        19.45,
        20.07,
        14.89,
        14.25,
        14.75,
        15.99,
        15.29,
        17.8,
        20.94,
        19.9,
        24.21,
        25.85,
        25.14,
        25.11,
        22.57,
        21.93,
        20.09,
        15.29,
        14.01,
        14.79,
        16.42,
        17.06,
        18.05
      ],
      "Procurement": [
        22.59,
        29.38,
        29.05,
        32.16,
        29.75,
        29.25,
        29.92,
        26.28,
        24.06,
        20.62,
        20.51,
        18.92,
        20.5,
        22.09,
        20.41,
        26.97,
        26.95,
        30.36,
        30.59,
        30.26,
        31.97,
        31.0,
        24.42,
        23.32,
        22.63,
        21.1,
        21.12,
        19.0,
        18.21,
        24.6
      ],
      "Risk": [
        78.08,
        74.57,
        87.85,
        95.76,
        93.54,
        96.85,
        92.94,
        77.57,
        77.76,
        63.35,
        64.5,
        59.75,
        66.74,
        60.42,
        80.0,
        80.1,
        85.87,
        102.26,
        101.27,
        108.91,
        103.15,
        102.56,
        95.61,
        86.09,
        71.2,
        70.58,
        68.27,
        76.85,
        69.58,
        79.73
      ],
      "Sales Ops": [
        12.63,
        14.9,
        14.99,
        15.79,
        15.56,
        14.84,
        16.52,
        13.74,
        13.68,
        11.64,
        9.18,
        10.52,
        11.27,
        12.04,
        11.28,
        12.42,
        15.76,
        16.07,
        16.5,
        15.78,
        15.99,
        15.67,
        13.34,
        13.38,
        12.63,
        9.16,
        8.69,
        10.13,
        12.07,
        11.95
      ]
    },
    "model_prices": [
      {
        "model": "databricks-claude-sonnet-4-5",
        "input_usd_per_mtok": 3.0,
        "output_usd_per_mtok": 15.0,
        "source": "list"
      },
      {
        "model": "databricks-gpt-oss-120b",
        "input_usd_per_mtok": 0.15,
        "output_usd_per_mtok": 0.6,
        "source": "list"
      },
      {
        "model": "databricks-llama-4-maverick",
        "input_usd_per_mtok": 0.5,
        "output_usd_per_mtok": 1.5,
        "source": "list"
      }
    ],
    "monitor_self_cost_mtd_usd": 186.4,
    "monitor_self_cost_pct_of_fleet": 2.1
  },
  "maintenance_windows": [
    {
      "app": "legacy-reports",
      "rule": "*",
      "starts_at": "2026-10-29T22:30:00Z",
      "ends_at": "2026-10-31T05:30:00Z",
      "reason": "Night auto-stop",
      "created_by": "app_stopper",
      "id": "demo-mute"
    }
  ],
  "governance": {
    "audit_events": [
      {
        "ts": "2026-10-29T21:50:00Z",
        "user": "contractor.x@partner.com",
        "action": "changePermissions",
        "app": "sales-cockpit",
        "detail": "all-contractors -> CAN_MANAGE"
      },
      {
        "ts": "2026-10-30T08:45:00Z",
        "user": "arjun.rao@contoso.com",
        "action": "deploy",
        "app": "fraud-triage",
        "detail": "3.4.0"
      },
      {
        "ts": "2026-10-29T22:30:00Z",
        "user": "apps-monitor (SP)",
        "action": "stop",
        "app": "legacy-reports",
        "detail": "night auto-stop"
      }
    ],
    "required_tags": [
      "team",
      "cost_center",
      "env",
      "tier"
    ]
  },
  "notes": {
    "health_values": "healthy | degraded | down | stopped (intentionally) | idle (running, no real traffic)",
    "costs": "dbu_usd = compute at list price from system.billing.usage; ai_usd = exact tokens x model list price (estimate)",
    "slo": "error_budget_remaining_pct < 0 means budget exhausted"
  },
  "traces": {},
  "sources": {
    "demo": "ok"
  },
  "genie_url": null,
  "topology": {
    "nodes": [
      {
        "id": "app:app-001",
        "app": "app-001",
        "label": "claims-assistant",
        "type": "app",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": "degraded",
        "dependents": []
      },
      {
        "id": "app:app-002",
        "app": "app-002",
        "label": "pricing-api",
        "type": "app",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": "healthy",
        "dependents": []
      },
      {
        "id": "app:app-003",
        "app": "app-003",
        "label": "sales-cockpit",
        "type": "app",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": "healthy",
        "dependents": []
      },
      {
        "id": "app:app-004",
        "app": "app-004",
        "label": "fraud-triage",
        "type": "app",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": "down",
        "dependents": []
      },
      {
        "id": "app:app-005",
        "app": "app-005",
        "label": "supplier-portal",
        "type": "app",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": "healthy",
        "dependents": []
      },
      {
        "id": "app:app-006",
        "app": "app-006",
        "label": "hr-policy-bot",
        "type": "app",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": "healthy",
        "dependents": []
      },
      {
        "id": "app:app-007",
        "app": "app-007",
        "label": "forecast-studio",
        "type": "app",
        "workspace_id": "7781204459918823",
        "workspace": "analytics-us",
        "health": "degraded",
        "dependents": []
      },
      {
        "id": "app:app-008",
        "app": "app-008",
        "label": "churn-explorer",
        "type": "app",
        "workspace_id": "7781204459918823",
        "workspace": "analytics-us",
        "health": "healthy",
        "dependents": []
      },
      {
        "id": "app:app-009",
        "app": "app-009",
        "label": "doc-intake",
        "type": "app",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": "healthy",
        "dependents": [
          "app:app-001",
          "app:app-010"
        ]
      },
      {
        "id": "app:app-010",
        "app": "app-010",
        "label": "ops-runbook-bot",
        "type": "app",
        "workspace_id": "3348812290431187",
        "workspace": "dev-eu",
        "health": "healthy",
        "dependents": []
      },
      {
        "id": "app:app-011",
        "app": "app-011",
        "label": "legacy-reports",
        "type": "app",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": "stopped",
        "dependents": []
      },
      {
        "id": "app:app-012",
        "app": "app-012",
        "label": "label-studio-lite",
        "type": "app",
        "workspace_id": "3348812290431187",
        "workspace": "dev-eu",
        "health": "idle",
        "dependents": []
      },
      {
        "id": "resource:1272983411735654:sql_warehouse:wh-7d1a",
        "label": "wh-7d1a",
        "type": "sql_warehouse",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": null,
        "dependents": [
          "app:app-001",
          "app:app-002",
          "app:app-003",
          "app:app-004",
          "app:app-005",
          "app:app-006",
          "app:app-009",
          "app:app-011"
        ]
      },
      {
        "id": "resource:1272983411735654:serving_endpoint:claims-model",
        "label": "claims-model",
        "type": "serving_endpoint",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": null,
        "dependents": [
          "app:app-001",
          "app:app-002"
        ]
      },
      {
        "id": "resource:1272983411735654:job:101",
        "label": "101",
        "type": "job",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": null,
        "dependents": [
          "app:app-001",
          "app:app-003"
        ]
      },
      {
        "id": "resource:1272983411735654:experiment:201",
        "label": "201",
        "type": "experiment",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": null,
        "dependents": [
          "app:app-001"
        ]
      },
      {
        "id": "resource:1272983411735654:database:risk-db",
        "label": "risk-db",
        "type": "database",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": null,
        "dependents": [
          "app:app-001",
          "app:app-004",
          "app:app-005"
        ]
      },
      {
        "id": "resource:1272983411735654:postgres:claims-db",
        "label": "claims-db",
        "type": "postgres",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": null,
        "dependents": [
          "app:app-001",
          "app:app-006"
        ]
      },
      {
        "id": "resource:1272983411735654:uc_securable:demo.claims.documents",
        "label": "demo.claims.documents",
        "type": "uc_securable",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": null,
        "dependents": [
          "app:app-001"
        ]
      },
      {
        "id": "resource:1272983411735654:secret:app-secrets",
        "label": "app-secrets",
        "type": "secret",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": null,
        "dependents": [
          "app:app-001"
        ]
      },
      {
        "id": "resource:1272983411735654:genie_space:genie-demo",
        "label": "genie-demo",
        "type": "genie_space",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": null,
        "dependents": [
          "app:app-001",
          "app:app-009"
        ]
      },
      {
        "id": "resource:7781204459918823:uc_securable:demo.claims.documents",
        "label": "demo.claims.documents",
        "type": "uc_securable",
        "workspace_id": "7781204459918823",
        "workspace": "analytics-us",
        "health": null,
        "dependents": [
          "app:app-007"
        ]
      },
      {
        "id": "resource:7781204459918823:secret:app-secrets",
        "label": "app-secrets",
        "type": "secret",
        "workspace_id": "7781204459918823",
        "workspace": "analytics-us",
        "health": null,
        "dependents": [
          "app:app-008"
        ]
      },
      {
        "id": "resource:3348812290431187:serving_endpoint:claims-model",
        "label": "claims-model",
        "type": "serving_endpoint",
        "workspace_id": "3348812290431187",
        "workspace": "dev-eu",
        "health": null,
        "dependents": [
          "app:app-012"
        ]
      },
      {
        "id": "resource:1272983411735654:external:api.example.invalid",
        "label": "api.example.invalid",
        "type": "external",
        "workspace_id": "1272983411735654",
        "workspace": "prod-eu",
        "health": null,
        "dependents": [
          "app:app-001"
        ]
      },
      {
        "id": "resource:7781204459918823:sql_warehouse:wh-7d1a",
        "label": "wh-7d1a",
        "type": "sql_warehouse",
        "workspace_id": "7781204459918823",
        "workspace": "analytics-us",
        "health": null,
        "dependents": [
          "app:app-007",
          "app:app-008"
        ]
      },
      {
        "id": "resource:3348812290431187:sql_warehouse:wh-7d1a",
        "label": "wh-7d1a",
        "type": "sql_warehouse",
        "workspace_id": "3348812290431187",
        "workspace": "dev-eu",
        "health": null,
        "dependents": [
          "app:app-010",
          "app:app-012"
        ]
      }
    ],
    "edges": [
      {
        "source": "app:app-001",
        "target": "resource:1272983411735654:sql_warehouse:wh-7d1a",
        "declared": true,
        "observed": true,
        "calls": 1200.0,
        "errors": 0.0,
        "avg_ms": 150.0,
        "p95_ms": 560.0,
        "error_pct": 0.0,
        "bindings": [
          {
            "name": "warehouse",
            "sql_warehouse": {
              "id": "wh-7d1a",
              "permission": "CAN_USE"
            }
          }
        ],
        "peers": [
          "databricks_sql/wh-7d1a"
        ]
      },
      {
        "source": "app:app-001",
        "target": "resource:1272983411735654:serving_endpoint:claims-model",
        "declared": true,
        "observed": true,
        "calls": 800.0,
        "errors": 15.0,
        "avg_ms": 1100.0,
        "p95_ms": 2300.0,
        "error_pct": 1.875,
        "bindings": [
          {
            "name": "model",
            "serving_endpoint": {
              "name": "claims-model",
              "permission": "CAN_QUERY"
            }
          }
        ],
        "peers": [
          "https://workspace.invalid/serving-endpoints/claims-model/invocations"
        ]
      },
      {
        "source": "app:app-001",
        "target": "resource:1272983411735654:job:101",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "refresh",
            "job": {
              "id": "101",
              "permission": "CAN_MANAGE_RUN"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-001",
        "target": "resource:1272983411735654:experiment:201",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "traces",
            "experiment": {
              "experiment_id": "201",
              "permission": "CAN_EDIT"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-001",
        "target": "resource:1272983411735654:database:risk-db",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "risk-store",
            "database": {
              "instance_name": "risk-db",
              "permission": "CAN_CONNECT_AND_CREATE"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-001",
        "target": "resource:1272983411735654:postgres:claims-db",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "claims-store",
            "postgres": {
              "database": "claims-db",
              "branch": "production"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-001",
        "target": "resource:1272983411735654:uc_securable:demo.claims.documents",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "documents",
            "uc_securable": {
              "securable_full_name": "demo.claims.documents",
              "securable_type": "TABLE"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-001",
        "target": "resource:1272983411735654:secret:app-secrets",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "credentials",
            "secret": {
              "scope": "app-secrets",
              "key": "api-key"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-001",
        "target": "resource:1272983411735654:genie_space:genie-demo",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "analytics",
            "genie_space": {
              "id": "genie-demo"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-001",
        "target": "app:app-009",
        "declared": true,
        "observed": true,
        "calls": 420.0,
        "errors": 4.0,
        "avg_ms": 600.0,
        "p95_ms": 2900.0,
        "error_pct": 0.9523809523809523,
        "bindings": [
          {
            "name": "intake",
            "app": {
              "name": "doc-intake",
              "url": "https://doc-intake-1008.aws.databricksapps.com",
              "permission": "CAN_USE"
            }
          }
        ],
        "peers": [
          "https://doc-intake-1008.aws.databricksapps.com/api/policies"
        ]
      },
      {
        "source": "app:app-002",
        "target": "resource:1272983411735654:serving_endpoint:claims-model",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "model",
            "serving_endpoint": {
              "name": "claims-model",
              "permission": "CAN_QUERY"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-003",
        "target": "resource:1272983411735654:job:101",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "refresh",
            "job": {
              "id": "101",
              "permission": "CAN_MANAGE_RUN"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-004",
        "target": "resource:1272983411735654:sql_warehouse:wh-7d1a",
        "declared": true,
        "observed": true,
        "calls": 1260.0,
        "errors": 3.0,
        "avg_ms": 150.0,
        "p95_ms": 560.0,
        "error_pct": 0.23809523809523808,
        "bindings": [
          {
            "name": "warehouse",
            "sql_warehouse": {
              "id": "wh-7d1a",
              "permission": "CAN_USE"
            }
          }
        ],
        "peers": [
          "databricks_sql/wh-7d1a"
        ]
      },
      {
        "source": "app:app-004",
        "target": "resource:1272983411735654:database:risk-db",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "risk-store",
            "database": {
              "instance_name": "risk-db",
              "permission": "CAN_CONNECT_AND_CREATE"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-005",
        "target": "resource:1272983411735654:database:risk-db",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "risk-store",
            "database": {
              "instance_name": "risk-db",
              "permission": "CAN_CONNECT_AND_CREATE"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-006",
        "target": "resource:1272983411735654:postgres:claims-db",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "claims-store",
            "postgres": {
              "database": "claims-db",
              "branch": "production"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-007",
        "target": "resource:7781204459918823:uc_securable:demo.claims.documents",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "documents",
            "uc_securable": {
              "securable_full_name": "demo.claims.documents",
              "securable_type": "TABLE"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-008",
        "target": "resource:7781204459918823:secret:app-secrets",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "credentials",
            "secret": {
              "scope": "app-secrets",
              "key": "api-key"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-009",
        "target": "resource:1272983411735654:genie_space:genie-demo",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "analytics",
            "genie_space": {
              "id": "genie-demo"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-010",
        "target": "app:app-009",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "intake",
            "app": {
              "name": "doc-intake",
              "url": "https://doc-intake-1008.aws.databricksapps.com",
              "permission": "CAN_USE"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-011",
        "target": "resource:1272983411735654:sql_warehouse:wh-7d1a",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "warehouse",
            "sql_warehouse": {
              "id": "wh-7d1a",
              "permission": "CAN_USE"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-012",
        "target": "resource:3348812290431187:serving_endpoint:claims-model",
        "declared": true,
        "observed": false,
        "calls": null,
        "errors": null,
        "avg_ms": null,
        "p95_ms": null,
        "error_pct": null,
        "bindings": [
          {
            "name": "model",
            "serving_endpoint": {
              "name": "claims-model",
              "permission": "CAN_QUERY"
            }
          }
        ],
        "peers": []
      },
      {
        "source": "app:app-001",
        "target": "resource:1272983411735654:external:api.example.invalid",
        "declared": false,
        "observed": true,
        "calls": 70.0,
        "errors": 0.0,
        "avg_ms": 100.0,
        "p95_ms": 180.0,
        "error_pct": 0.0,
        "bindings": [],
        "peers": [
          "api.example.invalid"
        ]
      },
      {
        "source": "app:app-002",
        "target": "resource:1272983411735654:sql_warehouse:wh-7d1a",
        "declared": false,
        "observed": true,
        "calls": 1220.0,
        "errors": 1.0,
        "avg_ms": 150.0,
        "p95_ms": 560.0,
        "error_pct": 0.08196721311475409,
        "bindings": [],
        "peers": [
          "databricks_sql/wh-7d1a"
        ]
      },
      {
        "source": "app:app-003",
        "target": "resource:1272983411735654:sql_warehouse:wh-7d1a",
        "declared": false,
        "observed": true,
        "calls": 1240.0,
        "errors": 2.0,
        "avg_ms": 150.0,
        "p95_ms": 560.0,
        "error_pct": 0.16129032258064516,
        "bindings": [],
        "peers": [
          "databricks_sql/wh-7d1a"
        ]
      },
      {
        "source": "app:app-005",
        "target": "resource:1272983411735654:sql_warehouse:wh-7d1a",
        "declared": false,
        "observed": true,
        "calls": 1280.0,
        "errors": 4.0,
        "avg_ms": 150.0,
        "p95_ms": 560.0,
        "error_pct": 0.3125,
        "bindings": [],
        "peers": [
          "databricks_sql/wh-7d1a"
        ]
      },
      {
        "source": "app:app-006",
        "target": "resource:1272983411735654:sql_warehouse:wh-7d1a",
        "declared": false,
        "observed": true,
        "calls": 1300.0,
        "errors": 5.0,
        "avg_ms": 150.0,
        "p95_ms": 560.0,
        "error_pct": 0.38461538461538464,
        "bindings": [],
        "peers": [
          "databricks_sql/wh-7d1a"
        ]
      },
      {
        "source": "app:app-007",
        "target": "resource:7781204459918823:sql_warehouse:wh-7d1a",
        "declared": false,
        "observed": true,
        "calls": 1320.0,
        "errors": 6.0,
        "avg_ms": 150.0,
        "p95_ms": 560.0,
        "error_pct": 0.45454545454545453,
        "bindings": [],
        "peers": [
          "databricks_sql/wh-7d1a"
        ]
      },
      {
        "source": "app:app-008",
        "target": "resource:7781204459918823:sql_warehouse:wh-7d1a",
        "declared": false,
        "observed": true,
        "calls": 1340.0,
        "errors": 7.0,
        "avg_ms": 150.0,
        "p95_ms": 560.0,
        "error_pct": 0.5223880597014925,
        "bindings": [],
        "peers": [
          "databricks_sql/wh-7d1a"
        ]
      },
      {
        "source": "app:app-009",
        "target": "resource:1272983411735654:sql_warehouse:wh-7d1a",
        "declared": false,
        "observed": true,
        "calls": 1360.0,
        "errors": 8.0,
        "avg_ms": 150.0,
        "p95_ms": 560.0,
        "error_pct": 0.5882352941176471,
        "bindings": [],
        "peers": [
          "databricks_sql/wh-7d1a"
        ]
      },
      {
        "source": "app:app-010",
        "target": "resource:3348812290431187:sql_warehouse:wh-7d1a",
        "declared": false,
        "observed": true,
        "calls": 1380.0,
        "errors": 9.0,
        "avg_ms": 150.0,
        "p95_ms": 560.0,
        "error_pct": 0.6521739130434783,
        "bindings": [],
        "peers": [
          "databricks_sql/wh-7d1a"
        ]
      },
      {
        "source": "app:app-012",
        "target": "resource:3348812290431187:sql_warehouse:wh-7d1a",
        "declared": false,
        "observed": true,
        "calls": 1420.0,
        "errors": 11.0,
        "avg_ms": 150.0,
        "p95_ms": 560.0,
        "error_pct": 0.7746478873239436,
        "bindings": [],
        "peers": [
          "databricks_sql/wh-7d1a"
        ]
      }
    ],
    "period": "7 days",
    "latency_basis": "Worst daily p95 (not a combined 7-day percentile)"
  },
  "fleet_measures": {
    "real_p95_ms": 2300,
    "requests_24h": 320000,
    "probe_p95_ms": 270
  }
};
