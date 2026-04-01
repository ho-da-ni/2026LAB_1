# FEATURES_SCHEMA (`features.json`) v1

`features.json`은 코드/설정/메타데이터에서 추출한 **기능 단위(feature)**를 정규화해 저장하는 산출물이다.
핵심 목표는 다음 3가지다.

- 기능 식별자(`feature_id`)의 결정론 보장
- 근거(`evidence`) 추적 가능성 보장
- 재실행 시 안정적인 diff(정렬/정규화 규칙)

---

## 1) Top-level 구조

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-04-01T00:00:00Z",
  "repo": {
    "base": "main",
    "head": "work",
    "merge_base": "abc123"
  },
  "features": [
    {
      "feature_id": "feat_9f4c1a4a2d0b8e11",
      "name": "Order API",
      "category": "api",
      "status": "active",
      "description": "주문 생성/조회 기능",
      "tags": ["order", "rest"],
      "owners": ["team-platform"],
      "signals": {
        "endpoints": ["ep_1234abcd", "ep_5678efgh"],
        "tables": ["orders", "order_items"],
        "jobs": []
      },
      "evidence": [
        {
          "type": "code",
          "source": {
            "file": "src/main/java/com/acme/order/OrderController.java",
            "symbol": "OrderController#create",
            "line_start": 42,
            "line_end": 88
          },
          "snippet_hash": "sha1:4f7...",
          "confidence": "high",
          "note": "POST /orders 매핑 확인"
        }
      ],
      "needs_review": []
    }
  ]
}
```

---

## 2) 필드 정의

### 2.1 top-level

- `schema_version` (string, required)
  - 스키마 버전. 변경 시 semver로 증가.
- `generated_at` (string, required)
  - UTC ISO-8601 타임스탬프.
- `repo` (object, required)
  - 산출 기준 브랜치/commit 메타.
- `features` (array, required)
  - feature 객체 목록. 비어 있을 수 있음.

### 2.2 feature 객체

- `feature_id` (string, required)
  - 형식: `feat_[0-9a-f]{16}` 권장.
  - canonical 입력 기반 결정론 ID.
- `name` (string, required)
  - 사람이 읽는 기능명.
- `category` (string, required)
  - 예: `api | batch | integration | ui | data | infra`.
- `status` (string, required)
  - `active | deprecated | experimental | unknown`.
- `description` (string, optional)
- `tags` (string[], optional)
- `owners` (string[], optional)
- `signals` (object, optional)
  - 기계적 연계 포인터(엔드포인트/테이블/잡 등).
- `evidence` (array, required)
  - feature 추론 근거. 최소 1건 권장(없으면 `needs_review` 기록).
- `needs_review` (array, optional)
  - 자동 확정 불가 사유.

### 2.3 evidence 객체 (핵심)

- `type` (string, required)
  - `code | config | sql | doc | runtime`.
- `source` (object, required)
  - `file` (string, required): repo-relative path
  - `symbol` (string, optional): 함수/클래스/쿼리 식별자
  - `line_start` (integer, optional)
  - `line_end` (integer, optional, `line_end >= line_start`)
- `snippet_hash` (string, optional)
  - 예: `sha1:<hex>`
- `confidence` (string, optional)
  - `high | medium | low`
- `note` (string, optional)

---

## 3) `feature_id` 생성 규칙

`feature_id`는 다음 canonical tuple을 sha1 해시한 뒤 앞 16 hex를 사용한다.

```text
(category, normalized_name, sorted(signals.endpoints), sorted(signals.tables), sorted(tags))
```

- prefix: `feat_`
- 예: `feat_` + `sha1(tuple_json)[:16]`
- 제외 필드: `description`, `owners`, `evidence`, `generated_at` (비본질 메타)
- 충돌 시: deterministic suffix(`_01`, `_02` ...)

---

## 4) 중복 제거(dedupe) 규칙

1. 1차 dedupe: 동일 `feature_id`
   - 가장 정보량이 큰 레코드 1건 유지(문자열 길이/배열 길이 기준)
2. 2차 dedupe: `category + normalized_name` 동일
   - signals/evidence/needs_review를 union 병합
3. evidence dedupe key
   - `(type, source.file, source.symbol, source.line_start, source.line_end, snippet_hash)`

자동 병합이 불가능한 경우:

- 동일 `feature_id`인데 category가 상충 → `needs_review.feature_category_conflict`
- 동일 이름인데 핵심 signals 완전 불일치 → `needs_review.feature_signal_conflict`

---

## 5) 정렬(sort) 규칙

- `features[]`: `(category, name, feature_id)` 오름차순
- `tags[]`, `owners[]`: ASCII 오름차순 + dedupe
- `signals.*[]`: ASCII 오름차순 + dedupe
- `evidence[]`: `(type, source.file, source.symbol, source.line_start, source.line_end)` 오름차순
- `needs_review[]`: `(code, target, detail)` 오름차순

---

## 6) 검증 규칙

- `feature_id`는 파일 내 유일해야 한다.
- `features[].name`은 빈 문자열 금지(trim 후 길이 > 0).
- `evidence[].source.file`은 경로 정규화 규칙 준수.
- `line_start`, `line_end`는 양의 정수.
- `evidence`가 비어 있으면 `needs_review.evidence_missing` 추가 권장.

---

## 7) 최소 JSON Schema 스켈레톤 (요약)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["schema_version", "generated_at", "repo", "features"],
  "properties": {
    "schema_version": { "type": "string" },
    "generated_at": { "type": "string", "format": "date-time" },
    "repo": {
      "type": "object",
      "required": ["base", "head", "merge_base"],
      "properties": {
        "base": { "type": "string" },
        "head": { "type": "string" },
        "merge_base": { "type": "string" }
      }
    },
    "features": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["feature_id", "name", "category", "status", "evidence"],
        "properties": {
          "feature_id": { "type": "string", "pattern": "^feat_[0-9a-f]{16}(?:_[0-9]{2})?$" },
          "name": { "type": "string", "minLength": 1 },
          "category": { "type": "string" },
          "status": { "type": "string" },
          "evidence": { "type": "array" }
        }
      }
    }
  }
}
```
