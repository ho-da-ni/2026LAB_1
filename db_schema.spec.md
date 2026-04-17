# DB IR 스키마 정의 (W6-DB-04)

## 1) 목적
W6 단계에서 DB IR(`db_schema.json`)의 공통 계약을 고정해, 후속 문서 생성(DB_SCHEMA/API/SPEC) 및 Java endpoint/feature/API 병합 시 동일한 구조를 재사용할 수 있도록 한다.

---

## 2) W6-T01 기준
- W6-T01의 핵심은 `db_schema` 구조 정의이다.
- 기대 산출물은 `db_schema.json` 명세 문서이다.
- DoD 핵심은 `tables`, `columns`, `PK`, `FK`를 반드시 포함하는 것이다.

---

## 3) 스키마 개요

### 3.1 최상위(top-level) 구조

| 필드 | 타입 | 필수 여부 | 설명 |
|---|---|---|---|
| `schema_version` | string | 필수 | 스키마 버전(예: `w6.db_schema.v1`) |
| `source` | object | 필수 | 수집 출처/시점/도구 정보 |
| `database` | object | 필수 | DB 식별 정보(벤더/host/port/service_name/sid) |
| `owners` | array[string] | 필수 | 수집 대상 owner 목록(정규화된 대문자) |
| `tables` | array[object] | 필수 | 테이블 메타데이터 목록 |
| `notes` | array[string] | 선택 | 생성 시 참고 메모/제약 사항 |
| `needs_review` | boolean | 필수 | 문서 전체 검토 필요 여부 |

### 3.2 테이블(table) 구조

| 필드 | 타입 | 필수 여부 | 설명 |
|---|---|---|---|
| `table_id` | string | 필수 | 안정 식별자(stable identifier), 예: `OWNER.TABLE_NAME` |
| `owner` | string | 필수 | owner/schema 이름 |
| `table_name` | string | 필수 | 테이블명 |
| `table_comment` | string\|null | 선택 | 테이블 코멘트 |
| `columns` | array[object] | 필수 | 컬럼 목록 |
| `primary_key` | object\|null | 필수 | PK 정보(없으면 `null`) |
| `foreign_keys` | array[object] | 필수 | FK 목록(없으면 빈 배열) |
| `evidence` | array[object] | 필수 | Oracle dictionary 근거 레코드 |
| `needs_review` | boolean | 필수 | 테이블 단위 검토 필요 여부 |
| `unknown` | boolean | 필수 | 수집 불가/판단 불가 여부 |

### 3.3 컬럼(column) 구조

| 필드 | 타입 | 필수 여부 | 설명 |
|---|---|---|---|
| `name` | string | 필수 | 컬럼명 |
| `ordinal_position` | integer | 필수 | 컬럼 순서(1-base) |
| `data_type` | string | 필수 | 데이터 타입 |
| `data_length` | integer\|null | 선택 | 길이 |
| `data_precision` | integer\|null | 선택 | 정밀도 |
| `data_scale` | integer\|null | 선택 | 스케일 |
| `nullable` | boolean | 필수 | NULL 허용 여부 |
| `default` | string\|null | 선택 | 기본값(표현 가능한 원문) |
| `comment` | string\|null | 선택 | 컬럼 코멘트 |
| `needs_review` | boolean | 필수 | 컬럼 단위 검토 필요 여부 |
| `unknown` | boolean | 필수 | 수집 불가/판단 불가 여부 |
| `evidence` | array[object] | 필수 | Oracle dictionary 근거 레코드 |

### 3.4 PK/FK 구조

#### Primary Key

| 필드 | 타입 | 필수 여부 | 설명 |
|---|---|---|---|
| `constraint_name` | string | 필수 | PK 제약명 |
| `columns` | array[string] | 필수 | PK 컬럼 목록(순서 유지) |
| `evidence` | array[object] | 필수 | 근거 레코드 |
| `needs_review` | boolean | 필수 | 검토 필요 여부 |
| `unknown` | boolean | 필수 | 수집 불가/판단 불가 여부 |

#### Foreign Key

| 필드 | 타입 | 필수 여부 | 설명 |
|---|---|---|---|
| `fk_id` | string | 필수 | 안정 식별자(stable identifier), 예: `OWNER.TABLE.FK_NAME` |
| `constraint_name` | string | 필수 | FK 제약명 |
| `columns` | array[string] | 필수 | 로컬 FK 컬럼 목록 |
| `referenced_owner` | string | 필수 | 참조 대상 owner |
| `referenced_table` | string | 필수 | 참조 대상 테이블 |
| `column_mapping` | array[object] | 필수 | 로컬-원격 컬럼 매핑 |
| `evidence` | array[object] | 필수 | 근거 레코드 |
| `needs_review` | boolean | 필수 | 검토 필요 여부 |
| `unknown` | boolean | 필수 | 수집 불가/판단 불가 여부 |

`column_mapping` 원소 구조:
- `local_column` (string, 필수)
- `referenced_column` (string, 필수)

---

## 4) 안정 식별자(stable identifier) 규칙
- `table_id`: `"{OWNER}.{TABLE_NAME}"` (대문자 정규화)
- `fk_id`: `"{OWNER}.{TABLE_NAME}.{CONSTRAINT_NAME}"` (대문자 정규화)
- 동일 입력에서 동일 식별자가 재생성되어야 하며, 출력 순서와 무관하게 식별자가 변하면 안 된다.

---

## 5) evidence 규칙
- 모든 table/column/PK/FK는 1개 이상 evidence를 가진다(수집 실패 시 실패 원인 evidence라도 기록).
- evidence 객체 권장 필드:
  - `source_view` (예: `ALL_TABLES`, `ALL_TAB_COLUMNS`, `ALL_CONSTRAINTS`, `ALL_CONS_COLUMNS`, `ALL_TAB_COMMENTS`, `ALL_COL_COMMENTS`)
  - `owner`
  - `object_name`
  - `column_name` (해당 시)
  - `constraint_name` (해당 시)
  - `row_ref` (원천 row 식별용 키-값 축약)

---

## 6) unknown / needs_review 규칙
- `unknown=true`: 수집 불가 또는 판단 불가가 존재함을 의미.
- `needs_review=true`: 후속 수동 검토가 필요함을 의미.
- 전파 규칙:
  - 하위 요소에 `unknown=true`가 있으면 상위(table/top-level) `needs_review`를 `true`로 승격 가능.
  - 필수 필드 누락 또는 타입 불일치 발견 시 `needs_review=true`.

---

## 7) 샘플 JSON (최대 1개)

```json
{
  "schema_version": "w6.db_schema.v1",
  "source": {
    "collector": "lab collect db",
    "collected_at": "2026-04-17T00:00:00Z",
    "dictionary_views": [
      "ALL_TABLES",
      "ALL_TAB_COLUMNS",
      "ALL_CONSTRAINTS",
      "ALL_CONS_COLUMNS",
      "ALL_TAB_COMMENTS",
      "ALL_COL_COMMENTS"
    ]
  },
  "database": {
    "vendor": "oracle",
    "host": "db.internal.local",
    "port": 1521,
    "service_name": "ORCLPDB1"
  },
  "owners": ["APP"],
  "tables": [
    {
      "table_id": "APP.ORDERS",
      "owner": "APP",
      "table_name": "ORDERS",
      "table_comment": "주문 헤더",
      "columns": [
        {
          "name": "ORDER_ID",
          "ordinal_position": 1,
          "data_type": "NUMBER",
          "data_length": null,
          "data_precision": 19,
          "data_scale": 0,
          "nullable": false,
          "default": null,
          "comment": "주문 ID",
          "needs_review": false,
          "unknown": false,
          "evidence": [
            {
              "source_view": "ALL_TAB_COLUMNS",
              "owner": "APP",
              "object_name": "ORDERS",
              "column_name": "ORDER_ID",
              "row_ref": {"column_id": 1}
            },
            {
              "source_view": "ALL_COL_COMMENTS",
              "owner": "APP",
              "object_name": "ORDERS",
              "column_name": "ORDER_ID",
              "row_ref": {"comment_present": true}
            }
          ]
        }
      ],
      "primary_key": {
        "constraint_name": "PK_ORDERS",
        "columns": ["ORDER_ID"],
        "evidence": [
          {
            "source_view": "ALL_CONSTRAINTS",
            "owner": "APP",
            "object_name": "ORDERS",
            "constraint_name": "PK_ORDERS",
            "row_ref": {"constraint_type": "P"}
          }
        ],
        "needs_review": false,
        "unknown": false
      },
      "foreign_keys": [
        {
          "fk_id": "APP.ORDERS.FK_ORDERS_CUSTOMER",
          "constraint_name": "FK_ORDERS_CUSTOMER",
          "columns": ["CUSTOMER_ID"],
          "referenced_owner": "APP",
          "referenced_table": "CUSTOMERS",
          "column_mapping": [
            {
              "local_column": "CUSTOMER_ID",
              "referenced_column": "CUSTOMER_ID"
            }
          ],
          "evidence": [
            {
              "source_view": "ALL_CONSTRAINTS",
              "owner": "APP",
              "object_name": "ORDERS",
              "constraint_name": "FK_ORDERS_CUSTOMER",
              "row_ref": {"constraint_type": "R"}
            }
          ],
          "needs_review": false,
          "unknown": false
        }
      ],
      "evidence": [
        {
          "source_view": "ALL_TABLES",
          "owner": "APP",
          "object_name": "ORDERS",
          "row_ref": {"table_name": "ORDERS"}
        },
        {
          "source_view": "ALL_TAB_COMMENTS",
          "owner": "APP",
          "object_name": "ORDERS",
          "row_ref": {"comment_present": true}
        }
      ],
      "needs_review": false,
      "unknown": false
    }
  ],
  "notes": [],
  "needs_review": false
}
```

---

## 8) DoD
- 샘플 JSON 1개가 포함되어 있다.
- 필수/선택 필드 구분이 완료되어 있다.
- 후속 문서 생성 및 Java 병합에 필요한 최소 필드(`table_id`, `fk_id`, `evidence`, `unknown`)가 누락되지 않는다.

---

## 9) 검증

### 9.1 샘플 JSON 리뷰
- 타입, 필수 필드, PK/FK/columns 포함 여부를 수동 리뷰한다.

### 9.2 누락 필드 체크리스트 검증
- 체크리스트:
  - top-level: `schema_version`, `source`, `database`, `owners`, `tables`, `needs_review`
  - table: `table_id`, `owner`, `table_name`, `columns`, `primary_key`, `foreign_keys`, `evidence`, `needs_review`, `unknown`
  - column: `name`, `ordinal_position`, `data_type`, `nullable`, `needs_review`, `unknown`, `evidence`
  - PK/FK: `constraint_name`, `columns`, `referenced_owner`, `referenced_table`, `column_mapping`(FK), `unknown`

### 9.3 후속 문서 생성 최소 필드 역추적 검증
- 테이블 식별: `table_id`
- 관계 추적: `fk_id`, `referenced_owner`, `referenced_table`, `column_mapping`
- 신뢰성 추적: `evidence`, `unknown`, `needs_review`
