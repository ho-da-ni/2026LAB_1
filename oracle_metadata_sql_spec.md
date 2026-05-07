# Oracle 메타데이터 수집 SQL 명세 (W6-DB-06)

## 1) 목적
구현 전에 Oracle 원천 메타데이터 조회 계약(SQL/파라미터/결과 컬럼)을 고정하여, `db_schema.json` 생성에 필요한 입력이 일관되게 수집되도록 한다.

---

## 2) 공통 규약

### 2.1 공통 입력 파라미터
- `:owners` (필수): 수집 대상 owner 목록(대문자 정규화)
- `:system_owners` (필수): 제외할 시스템 스키마 목록 (`SYS`, `SYSTEM`, `XDB`, ...)

### 2.2 공통 필터 규칙
모든 SQL은 아래 조건을 포함해야 한다.
- `OWNER IN (:owners)`
- `OWNER NOT IN (:system_owners)`

> 우선순위는 `exclude > include` 이므로, include에 있어도 `:system_owners`에 포함되면 제외한다.

### 2.3 네이밍/매핑 규칙
- SQL 결과 컬럼 alias는 가능하면 IR 필드명과 동일하게 고정한다.
- 파생 필드(`table_id`, `fk_id`)는 결과 컬럼 조합으로 생성한다.
  - `table_id = owner || '.' || table_name`
  - `fk_id = owner || '.' || table_name || '.' || constraint_name`

---

## 3) SQL 범주별 명세

## 3.1 Table 목록 조회

### 목적
수집 대상 테이블의 기본 식별자와 상태 정보를 조회한다.

### 입력 파라미터
- `:owners`
- `:system_owners`

### SQL
```sql
SELECT
  t.OWNER AS owner,
  t.TABLE_NAME AS table_name,
  t.STATUS AS table_status,
  t.TEMPORARY AS is_temporary,
  t.NESTED AS is_nested
FROM ALL_TABLES t
WHERE t.OWNER IN (:owners)
  AND t.OWNER NOT IN (:system_owners)
ORDER BY t.OWNER, t.TABLE_NAME;
```

### 결과 컬럼 → `db_schema.json` 매핑
| SQL 컬럼 | IR 필드 | 매핑 방식 |
|---|---|---|
| `owner` | `tables[].owner` | 1:1 |
| `table_name` | `tables[].table_name` | 1:1 |
| `(owner, table_name)` | `tables[].table_id` | 파생: `owner + '.' + table_name` |
| `table_status` | `tables[].evidence[].row_ref.table_status` | 1:1(row_ref) |
| `is_temporary` | `tables[].evidence[].row_ref.is_temporary` | 1:1(row_ref) |
| `is_nested` | `tables[].evidence[].row_ref.is_nested` | 1:1(row_ref) |

---

## 3.2 Column 목록 조회

### 목적
각 테이블의 컬럼 정의(순서/타입/nullable/default)를 조회한다.

### 입력 파라미터
- `:owners`
- `:system_owners`

### SQL
```sql
SELECT
  c.OWNER AS owner,
  c.TABLE_NAME AS table_name,
  c.COLUMN_NAME AS column_name,
  c.COLUMN_ID AS ordinal_position,
  c.DATA_TYPE AS data_type,
  c.DATA_LENGTH AS data_length,
  c.DATA_PRECISION AS data_precision,
  c.DATA_SCALE AS data_scale,
  CASE c.NULLABLE WHEN 'Y' THEN 1 ELSE 0 END AS nullable,
  c.DATA_DEFAULT AS data_default
FROM ALL_TAB_COLUMNS c
WHERE c.OWNER IN (:owners)
  AND c.OWNER NOT IN (:system_owners)
ORDER BY c.OWNER, c.TABLE_NAME, c.COLUMN_ID;
```

### 결과 컬럼 → `db_schema.json` 매핑
| SQL 컬럼 | IR 필드 | 매핑 방식 |
|---|---|---|
| `owner` | `tables[].owner` | 조인키 |
| `table_name` | `tables[].table_name` | 조인키 |
| `column_name` | `tables[].columns[].name` | 1:1 |
| `ordinal_position` | `tables[].columns[].ordinal_position` | 1:1 |
| `data_type` | `tables[].columns[].data_type` | 1:1 |
| `data_length` | `tables[].columns[].data_length` | 1:1 |
| `data_precision` | `tables[].columns[].data_precision` | 1:1 |
| `data_scale` | `tables[].columns[].data_scale` | 1:1 |
| `nullable` | `tables[].columns[].nullable` | `1=true`, `0=false` |
| `data_default` | `tables[].columns[].default` | 1:1 |

---

## 3.3 PK 조회

### 목적
테이블별 PK 제약명과 PK 컬럼 순서를 조회한다.

### 입력 파라미터
- `:owners`
- `:system_owners`

### SQL
```sql
SELECT
  p.OWNER AS owner,
  p.TABLE_NAME AS table_name,
  p.CONSTRAINT_NAME AS constraint_name,
  pc.COLUMN_NAME AS column_name,
  pc.POSITION AS column_position
FROM ALL_CONSTRAINTS p
JOIN ALL_CONS_COLUMNS pc
  ON pc.OWNER = p.OWNER
 AND pc.CONSTRAINT_NAME = p.CONSTRAINT_NAME
WHERE p.CONSTRAINT_TYPE = 'P'
  AND p.OWNER IN (:owners)
  AND p.OWNER NOT IN (:system_owners)
ORDER BY p.OWNER, p.TABLE_NAME, p.CONSTRAINT_NAME, pc.POSITION;
```

### 결과 컬럼 → `db_schema.json` 매핑
| SQL 컬럼 | IR 필드 | 매핑 방식 |
|---|---|---|
| `owner` | `tables[].owner` | 조인키 |
| `table_name` | `tables[].table_name` | 조인키 |
| `constraint_name` | `tables[].primary_key.constraint_name` | 1:1 |
| `column_name`(ordered) | `tables[].primary_key.columns[]` | `column_position` 순서대로 배열화 |
| `column_position` | 정렬 제어용 | 배열 생성 시 사용 |

---

## 3.4 FK 조회

### 목적
FK 제약, 로컬/참조 테이블, 컬럼 매핑(순서 포함)을 조회한다.

### 입력 파라미터
- `:owners`
- `:system_owners`

### SQL
```sql
SELECT
  fk.OWNER AS owner,
  fk.TABLE_NAME AS table_name,
  fk.CONSTRAINT_NAME AS constraint_name,
  fkc.COLUMN_NAME AS local_column,
  fkc.POSITION AS column_position,
  pk.OWNER AS referenced_owner,
  pk.TABLE_NAME AS referenced_table,
  pkc.COLUMN_NAME AS referenced_column
FROM ALL_CONSTRAINTS fk
JOIN ALL_CONS_COLUMNS fkc
  ON fkc.OWNER = fk.OWNER
 AND fkc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
JOIN ALL_CONSTRAINTS pk
  ON pk.OWNER = fk.R_OWNER
 AND pk.CONSTRAINT_NAME = fk.R_CONSTRAINT_NAME
JOIN ALL_CONS_COLUMNS pkc
  ON pkc.OWNER = pk.OWNER
 AND pkc.CONSTRAINT_NAME = pk.CONSTRAINT_NAME
 AND pkc.POSITION = fkc.POSITION
WHERE fk.CONSTRAINT_TYPE = 'R'
  AND fk.OWNER IN (:owners)
  AND fk.OWNER NOT IN (:system_owners)
ORDER BY fk.OWNER, fk.TABLE_NAME, fk.CONSTRAINT_NAME, fkc.POSITION;
```

### 결과 컬럼 → `db_schema.json` 매핑
| SQL 컬럼 | IR 필드 | 매핑 방식 |
|---|---|---|
| `owner` | `tables[].owner` | 조인키 |
| `table_name` | `tables[].table_name` | 조인키 |
| `constraint_name` | `tables[].foreign_keys[].constraint_name` | 1:1 |
| `(owner, table_name, constraint_name)` | `tables[].foreign_keys[].fk_id` | 파생: `owner + '.' + table_name + '.' + constraint_name` |
| `local_column`(ordered) | `tables[].foreign_keys[].columns[]` | `column_position` 순서대로 배열화 |
| `referenced_owner` | `tables[].foreign_keys[].referenced_owner` | 1:1 |
| `referenced_table` | `tables[].foreign_keys[].referenced_table` | 1:1 |
| `(local_column, referenced_column)` | `tables[].foreign_keys[].column_mapping[]` | 객체 배열로 매핑 |
| `column_position` | 정렬 제어용 | 배열 생성 시 사용 |

---

## 3.5 Table Comment 조회

### 목적
테이블 코멘트를 조회한다.

### 입력 파라미터
- `:owners`
- `:system_owners`

### SQL
```sql
SELECT
  tc.OWNER AS owner,
  tc.TABLE_NAME AS table_name,
  tc.COMMENTS AS table_comment
FROM ALL_TAB_COMMENTS tc
WHERE tc.OWNER IN (:owners)
  AND tc.OWNER NOT IN (:system_owners)
ORDER BY tc.OWNER, tc.TABLE_NAME;
```

### 결과 컬럼 → `db_schema.json` 매핑
| SQL 컬럼 | IR 필드 | 매핑 방식 |
|---|---|---|
| `owner` | `tables[].owner` | 조인키 |
| `table_name` | `tables[].table_name` | 조인키 |
| `table_comment` | `tables[].table_comment` | 1:1 |

---

## 3.6 Column Comment 조회

### 목적
컬럼 코멘트를 조회한다.

### 입력 파라미터
- `:owners`
- `:system_owners`

### SQL
```sql
SELECT
  cc.OWNER AS owner,
  cc.TABLE_NAME AS table_name,
  cc.COLUMN_NAME AS column_name,
  cc.COMMENTS AS column_comment
FROM ALL_COL_COMMENTS cc
WHERE cc.OWNER IN (:owners)
  AND cc.OWNER NOT IN (:system_owners)
ORDER BY cc.OWNER, cc.TABLE_NAME, cc.COLUMN_NAME;
```

### 결과 컬럼 → `db_schema.json` 매핑
| SQL 컬럼 | IR 필드 | 매핑 방식 |
|---|---|---|
| `owner` | `tables[].owner` | 조인키 |
| `table_name` | `tables[].table_name` | 조인키 |
| `column_name` | `tables[].columns[].name` | 조인키 |
| `column_comment` | `tables[].columns[].comment` | 1:1 |

---

## 4) 검증 체크리스트

## 4.1 SQL 결과 컬럼 ↔ IR 필드 1:1 매핑 검토
- [ ] Table/Column/PK/FK/Table Comment/Column Comment 각 SQL에 대해 매핑 테이블이 존재한다.
- [ ] `tables[].owner`, `tables[].table_name`, `tables[].columns[].name` 조인 키가 모든 범주에서 일관된다.
- [ ] 파생 필드(`table_id`, `fk_id`) 생성식이 고정되어 있다.

## 4.2 owner filter 적용 여부 확인
- [ ] 6개 SQL 모두 `OWNER IN (:owners)`를 포함한다.
- [ ] 6개 SQL 모두 `OWNER NOT IN (:system_owners)`를 포함한다.
- [ ] include/exclude 충돌 시 exclude 우선 원칙을 따른다.

