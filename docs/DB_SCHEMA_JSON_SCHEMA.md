# db_schema.json Schema (v1.0.0)

`db_schema.json`은 DB 메타데이터를 정규화한 구조 산출물이다.
`DB_SCHEMA.md`는 이 JSON을 입력으로 렌더링한다.

## Top-level

```json
{
  "schema_version": "1.0.0",
  "metadata": {
    "generated_at_utc": "2026-04-01T00:00:00Z",
    "source_type": "UNKNOWN",
    "source_path": "UNKNOWN",
    "snapshot_id": "UNKNOWN",
    "collected_at_utc": "UNKNOWN"
  },
  "tables": [],
  "needs_review": [],
  "integrity": {
    "fingerprint": "UNKNOWN",
    "fingerprint_policy_version": "1.0.0",
    "fingerprint_policy": {
      "algorithm": "sha256",
      "normalization": "stable_json_canonicalization",
      "exclude": ["metadata.generated_at_utc", "integrity.fingerprint"]
    }
  }
}
```

## `tables[]`

```json
{
  "table_name": "users",
  "schema_name": "public",
  "columns": [
    {
      "name": "id",
      "data_type": "bigint",
      "nullable": false,
      "default": "UNKNOWN",
      "is_primary_key": true,
      "is_foreign_key": false,
      "references": {
        "table": "UNKNOWN",
        "column": "UNKNOWN"
      }
    }
  ],
  "primary_key": { "columns": ["id"] },
  "foreign_keys": [],
  "indexes": [],
  "source_evidence": [],
  "needs_review": []
}
```

## UNKNOWN / needs_review 정책

- 팩트 불확실 항목은 `UNKNOWN`으로 남긴다.
- `table_name=UNKNOWN`이면 `needs_review.table_name_unknown`를 추가한다.
- 컬럼이 비어 있으면 `needs_review.columns_missing`를 추가한다.
- 테이블 자체가 없으면 top-level `needs_review.db_schema.empty`를 추가한다.
