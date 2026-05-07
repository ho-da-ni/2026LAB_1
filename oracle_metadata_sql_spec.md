# Oracle metadata SQL spec (W6-DB-06)

## 1) Purpose

This document fixes the SQL contract that the real DB collector must use before implementing live Oracle metadata collection.
The collector output must be normalizable into `db_schema.json` as defined by `db_schema.schema.json` and `db_schema.spec.md`.

The contract covers exactly these metadata categories:

1. Table list
2. Column list
3. Primary keys
4. Foreign keys
5. Table comments
6. Column comments

---

## 2) Source dictionary views

The collector must use Oracle `ALL_*` dictionary views so that results are limited to objects visible to the connected user.

| Category | Required source view(s) | Notes |
|---|---|---|
| Tables | `ALL_TABLES` | Base table inventory for included owners. |
| Columns | `ALL_TAB_COLUMNS` | Column order, type, nullability, default. |
| PK | `ALL_CONSTRAINTS`, `ALL_CONS_COLUMNS` | `CONSTRAINT_TYPE = 'P'`. |
| FK | `ALL_CONSTRAINTS`, `ALL_CONS_COLUMNS` | `CONSTRAINT_TYPE = 'R'`, joined to referenced constraint columns. |
| Table comments | `ALL_TAB_COMMENTS` | `TABLE_TYPE = 'TABLE'` when available in result set. |
| Column comments | `ALL_COL_COMMENTS` | Column-level comments keyed by owner/table/column. |

`source.dictionary_views` in `db_schema.json` must include the sorted unique list:

```json
[
  "ALL_COL_COMMENTS",
  "ALL_CONS_COLUMNS",
  "ALL_CONSTRAINTS",
  "ALL_TAB_COLUMNS",
  "ALL_TAB_COMMENTS",
  "ALL_TABLES"
]
```

---

## 3) Common SQL contract

### 3.1 Input parameters

| Parameter | Required | Type | Description |
|---|---:|---|---|
| `:owners` | Yes | array/list of string | Included owner/schema names, normalized to uppercase before query execution. |
| `:system_owners` | Yes | array/list of string | Excluded Oracle/system owners, normalized to uppercase. |

The implementation may need to expand array binds into driver-specific placeholders, for example `IN (:owner_0, :owner_1)`.
The logical contract remains `IN (:owners)`.

### 3.2 Owner filter rule

Every SQL in this document must apply the target object owner filter:

```sql
<target_alias>.OWNER IN (:owners)
AND <target_alias>.OWNER NOT IN (:system_owners)
```

Where `ALL_CONSTRAINTS` is the target object source for PK/FK, the filter applies to `p.OWNER` or `fk.OWNER`.
Referenced objects in FK rows may point to owners outside `:owners`; they are recorded in `referenced_owner` but are not expanded into `tables[]` unless separately included by `:owners`.

### 3.3 Stable ordering

Each SQL must include deterministic `ORDER BY` clauses.
The normalizer must also sort final `tables[]`, `columns[]`, `primary_key.columns[]`, `foreign_keys[]`, and `foreign_keys[].column_mapping[]` deterministically after grouping.

### 3.4 Derived identifiers

| Derived field | Formula | Normalization |
|---|---|---|
| `tables[].table_id` | `owner || '.' || table_name` | Uppercase owner/table from Oracle dictionary rows. |
| `tables[].foreign_keys[].fk_id` | `owner || '.' || table_name || '.' || constraint_name` | Uppercase owner/table/constraint from Oracle dictionary rows. |

### 3.5 Evidence row convention

Every row mapped from an Oracle dictionary view must be retained in `evidence[].row_ref` with at least the selected SQL output columns needed to reproduce the mapping.
The `evidence` object must follow `db_schema.spec.md`:

| Evidence field | Source |
|---|---|
| `source_view` | View name such as `ALL_TABLES`, `ALL_TAB_COLUMNS`, `ALL_CONSTRAINTS`, `ALL_CONS_COLUMNS`, `ALL_TAB_COMMENTS`, `ALL_COL_COMMENTS`. |
| `owner` | SQL `owner`. |
| `object_name` | SQL `table_name`. |
| `column_name` | SQL `column_name`, `local_column`, or `referenced_column` when column-specific; otherwise `null`. |
| `constraint_name` | SQL `constraint_name` for PK/FK rows; otherwise `null`. |
| `row_ref` | The selected SQL output row or minimal stable subset. |

---

## 4) SQL definitions

## 4.1 Table list SQL

### Purpose

Collect the base table inventory for every included owner.
The result creates one `tables[]` object per `(owner, table_name)`.

### Inputs

- `:owners`
- `:system_owners`

### SQL

```sql
SELECT
  t.OWNER AS owner,
  t.TABLE_NAME AS table_name,
  t.STATUS AS table_status,
  t.TEMPORARY AS temporary,
  t.NESTED AS nested,
  t.IOT_TYPE AS iot_type
FROM ALL_TABLES t
WHERE t.OWNER IN (:owners)
  AND t.OWNER NOT IN (:system_owners)
ORDER BY t.OWNER, t.TABLE_NAME;
```

### Output columns

| Output column | Type/shape | Description |
|---|---|---|
| `owner` | string | Table owner/schema. |
| `table_name` | string | Table name. |
| `table_status` | string/null | Oracle table status. |
| `temporary` | string/null | Oracle `Y`/`N` temporary flag. |
| `nested` | string/null | Oracle `YES`/`NO` nested flag. |
| `iot_type` | string/null | Oracle index-organized table type. |

### Mapping to `db_schema.json`

| SQL output | `db_schema.json` field | Mapping rule |
|---|---|---|
| `owner` | `tables[].owner` | 1:1. |
| `table_name` | `tables[].table_name` | 1:1. |
| `owner`, `table_name` | `tables[].table_id` | `owner + '.' + table_name`. |
| row existence | `tables[].columns` | Initialized then populated from Column list SQL; table without columns is invalid and must set `needs_review=true`. |
| row existence | `tables[].primary_key` | Initialized to `null`, replaced from PK SQL when found. |
| row existence | `tables[].foreign_keys` | Initialized to `[]`, populated from FK SQL. |
| row existence | `tables[].table_comment` | Initialized to `null`, replaced from Table Comment SQL. |
| row existence | `tables[].needs_review` | `false` unless required related metadata is missing/inconsistent. |
| row existence | `tables[].unknown` | `false` when table row is complete. |
| full row | `tables[].evidence[]` | Add `source_view='ALL_TABLES'`, `owner`, `object_name=table_name`, `row_ref` with selected output columns. |
| `table_status`, `temporary`, `nested`, `iot_type` | `tables[].evidence[].row_ref.*` | Preserve as evidence-only metadata. |

---

## 4.2 Column list SQL

### Purpose

Collect column definitions for included owner tables, including column order, Oracle type metadata, nullability, and default expression.
The result creates one `tables[].columns[]` object per `(owner, table_name, column_name)`.

### Inputs

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
  c.NULLABLE AS nullable_flag,
  c.DATA_DEFAULT AS data_default
FROM ALL_TAB_COLUMNS c
WHERE c.OWNER IN (:owners)
  AND c.OWNER NOT IN (:system_owners)
ORDER BY c.OWNER, c.TABLE_NAME, c.COLUMN_ID, c.COLUMN_NAME;
```

### Output columns

| Output column | Type/shape | Description |
|---|---|---|
| `owner` | string | Table owner/schema. |
| `table_name` | string | Table name. |
| `column_name` | string | Column name. |
| `ordinal_position` | integer/null | Oracle `COLUMN_ID`; expected non-null for normal table columns. |
| `data_type` | string | Oracle data type. |
| `data_length` | integer/null | Byte length where applicable. |
| `data_precision` | integer/null | Numeric precision where applicable. |
| `data_scale` | integer/null | Numeric scale where applicable. |
| `nullable_flag` | string | Oracle `Y`/`N` nullability flag. |
| `data_default` | string/null | Oracle default expression. Driver may return CLOB/LONG-like value and must convert to string/null. |

### Mapping to `db_schema.json`

| SQL output | `db_schema.json` field | Mapping rule |
|---|---|---|
| `owner`, `table_name` | parent `tables[]` | Join on `tables[].owner` and `tables[].table_name`. |
| `column_name` | `tables[].columns[].name` | 1:1. |
| `ordinal_position` | `tables[].columns[].ordinal_position` | 1:1; if null, assign deterministic fallback and set `unknown=true`. |
| `data_type` | `tables[].columns[].data_type` | 1:1. |
| `data_length` | `tables[].columns[].data_length` | 1:1. |
| `data_precision` | `tables[].columns[].data_precision` | 1:1. |
| `data_scale` | `tables[].columns[].data_scale` | 1:1. |
| `nullable_flag` | `tables[].columns[].nullable` | `Y -> true`, `N -> false`; otherwise `false` with `unknown=true`. |
| `data_default` | `tables[].columns[].default` | 1:1 string/null after driver conversion. |
| row existence | `tables[].columns[].comment` | Initialized to `null`, replaced from Column Comment SQL. |
| row completeness | `tables[].columns[].needs_review` | `true` when required values are missing/inconsistent; otherwise `false`. |
| row completeness | `tables[].columns[].unknown` | `true` for missing/invalid required metadata; otherwise `false`. |
| full row | `tables[].columns[].evidence[]` | Add `source_view='ALL_TAB_COLUMNS'`, `owner`, `object_name=table_name`, `column_name`, `row_ref` with selected output columns. |

---

## 4.3 Primary key SQL

### Purpose

Collect primary key constraints and ordered primary key columns for included owner tables.
The result groups rows by `(owner, table_name, constraint_name)` into one `tables[].primary_key` object.

### Inputs

- `:owners`
- `:system_owners`

### SQL

```sql
SELECT
  p.OWNER AS owner,
  p.TABLE_NAME AS table_name,
  p.CONSTRAINT_NAME AS constraint_name,
  pc.COLUMN_NAME AS column_name,
  pc.POSITION AS column_position,
  p.STATUS AS constraint_status,
  p.DEFERRABLE AS deferrable,
  p.DEFERRED AS deferred
FROM ALL_CONSTRAINTS p
JOIN ALL_CONS_COLUMNS pc
  ON pc.OWNER = p.OWNER
 AND pc.TABLE_NAME = p.TABLE_NAME
 AND pc.CONSTRAINT_NAME = p.CONSTRAINT_NAME
WHERE p.CONSTRAINT_TYPE = 'P'
  AND p.OWNER IN (:owners)
  AND p.OWNER NOT IN (:system_owners)
ORDER BY p.OWNER, p.TABLE_NAME, p.CONSTRAINT_NAME, pc.POSITION, pc.COLUMN_NAME;
```

### Output columns

| Output column | Type/shape | Description |
|---|---|---|
| `owner` | string | PK table owner/schema. |
| `table_name` | string | PK table name. |
| `constraint_name` | string | PK constraint name. |
| `column_name` | string | PK column name. |
| `column_position` | integer | PK column order within the constraint. |
| `constraint_status` | string/null | Oracle constraint status. |
| `deferrable` | string/null | Oracle deferrable flag. |
| `deferred` | string/null | Oracle deferred flag. |

### Mapping to `db_schema.json`

| SQL output | `db_schema.json` field | Mapping rule |
|---|---|---|
| `owner`, `table_name` | parent `tables[]` | Join on `tables[].owner` and `tables[].table_name`. |
| `constraint_name` | `tables[].primary_key.constraint_name` | 1:1 for grouped PK object. |
| `column_name` ordered by `column_position` | `tables[].primary_key.columns[]` | Ordered array. |
| grouped rows | `tables[].primary_key.evidence[]` | Add at least one `ALL_CONSTRAINTS` evidence row and `ALL_CONS_COLUMNS` evidence rows with `constraint_name`, `column_name`, and `row_ref`. |
| grouped row completeness | `tables[].primary_key.needs_review` | `false` unless duplicate PK groups or missing columns are detected. |
| grouped row completeness | `tables[].primary_key.unknown` | `false` unless required values are missing/inconsistent. |
| no row for table | `tables[].primary_key` | `null`. |
| `constraint_status`, `deferrable`, `deferred`, `column_position` | `tables[].primary_key.evidence[].row_ref.*` | Preserve as evidence-only metadata. |

---

## 4.4 Foreign key SQL

### Purpose

Collect foreign key constraints for included owner tables and map local FK columns to referenced PK/unique constraint columns by ordinal position.
The result groups rows by `(owner, table_name, constraint_name)` into `tables[].foreign_keys[]`.

### Inputs

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
  pk.CONSTRAINT_NAME AS referenced_constraint_name,
  pkc.COLUMN_NAME AS referenced_column,
  fk.STATUS AS constraint_status,
  fk.DELETE_RULE AS delete_rule,
  fk.DEFERRABLE AS deferrable,
  fk.DEFERRED AS deferred
FROM ALL_CONSTRAINTS fk
JOIN ALL_CONS_COLUMNS fkc
  ON fkc.OWNER = fk.OWNER
 AND fkc.TABLE_NAME = fk.TABLE_NAME
 AND fkc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
JOIN ALL_CONSTRAINTS pk
  ON pk.OWNER = fk.R_OWNER
 AND pk.CONSTRAINT_NAME = fk.R_CONSTRAINT_NAME
JOIN ALL_CONS_COLUMNS pkc
  ON pkc.OWNER = pk.OWNER
 AND pkc.TABLE_NAME = pk.TABLE_NAME
 AND pkc.CONSTRAINT_NAME = pk.CONSTRAINT_NAME
 AND pkc.POSITION = fkc.POSITION
WHERE fk.CONSTRAINT_TYPE = 'R'
  AND fk.OWNER IN (:owners)
  AND fk.OWNER NOT IN (:system_owners)
ORDER BY fk.OWNER, fk.TABLE_NAME, fk.CONSTRAINT_NAME, fkc.POSITION, fkc.COLUMN_NAME;
```

### Output columns

| Output column | Type/shape | Description |
|---|---|---|
| `owner` | string | Local FK table owner/schema. |
| `table_name` | string | Local FK table name. |
| `constraint_name` | string | FK constraint name. |
| `local_column` | string | Local FK column. |
| `column_position` | integer | FK column order within the constraint. |
| `referenced_owner` | string | Referenced constraint owner. |
| `referenced_table` | string | Referenced table name. |
| `referenced_constraint_name` | string | Referenced PK/unique constraint name. |
| `referenced_column` | string | Referenced column paired by `column_position`. |
| `constraint_status` | string/null | Oracle FK status. |
| `delete_rule` | string/null | Oracle FK delete rule. |
| `deferrable` | string/null | Oracle deferrable flag. |
| `deferred` | string/null | Oracle deferred flag. |

### Mapping to `db_schema.json`

| SQL output | `db_schema.json` field | Mapping rule |
|---|---|---|
| `owner`, `table_name` | parent `tables[]` | Join on `tables[].owner` and `tables[].table_name`. |
| `owner`, `table_name`, `constraint_name` | `tables[].foreign_keys[].fk_id` | `owner + '.' + table_name + '.' + constraint_name`. |
| `constraint_name` | `tables[].foreign_keys[].constraint_name` | 1:1. |
| `local_column` ordered by `column_position` | `tables[].foreign_keys[].columns[]` | Ordered array. |
| `referenced_owner` | `tables[].foreign_keys[].referenced_owner` | 1:1. |
| `referenced_table` | `tables[].foreign_keys[].referenced_table` | 1:1. |
| `local_column`, `referenced_column` ordered by `column_position` | `tables[].foreign_keys[].column_mapping[]` | Objects `{local_column, referenced_column}`. |
| grouped rows | `tables[].foreign_keys[].evidence[]` | Add `ALL_CONSTRAINTS` evidence for FK/referenced constraint and `ALL_CONS_COLUMNS` evidence for local/referenced columns. |
| grouped row completeness | `tables[].foreign_keys[].needs_review` | `false` unless referenced metadata or column pairs are incomplete. |
| grouped row completeness | `tables[].foreign_keys[].unknown` | `false` unless required values are missing/inconsistent. |
| no row for table | `tables[].foreign_keys` | Empty array `[]`. |
| `referenced_constraint_name`, `constraint_status`, `delete_rule`, `deferrable`, `deferred`, `column_position` | `tables[].foreign_keys[].evidence[].row_ref.*` | Preserve as evidence-only metadata. |

---

## 4.5 Table comment SQL

### Purpose

Collect table comments for included owner tables.
The result updates `tables[].table_comment` and adds comment evidence.

### Inputs

- `:owners`
- `:system_owners`

### SQL

```sql
SELECT
  tc.OWNER AS owner,
  tc.TABLE_NAME AS table_name,
  tc.TABLE_TYPE AS table_type,
  tc.COMMENTS AS table_comment
FROM ALL_TAB_COMMENTS tc
WHERE tc.OWNER IN (:owners)
  AND tc.OWNER NOT IN (:system_owners)
  AND tc.TABLE_TYPE = 'TABLE'
ORDER BY tc.OWNER, tc.TABLE_NAME;
```

### Output columns

| Output column | Type/shape | Description |
|---|---|---|
| `owner` | string | Table owner/schema. |
| `table_name` | string | Table name. |
| `table_type` | string | Expected `TABLE`. |
| `table_comment` | string/null | Table comment. |

### Mapping to `db_schema.json`

| SQL output | `db_schema.json` field | Mapping rule |
|---|---|---|
| `owner`, `table_name` | parent `tables[]` | Join on `tables[].owner` and `tables[].table_name`. |
| `table_comment` | `tables[].table_comment` | 1:1; null remains null. |
| full row | `tables[].evidence[]` | Add `source_view='ALL_TAB_COMMENTS'`, `owner`, `object_name=table_name`, `row_ref` with selected output columns. |
| `table_type` | `tables[].evidence[].row_ref.table_type` | Preserve as evidence-only metadata. |

---

## 4.6 Column comment SQL

### Purpose

Collect column comments for included owner table columns.
The result updates `tables[].columns[].comment` and adds comment evidence.

### Inputs

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

### Output columns

| Output column | Type/shape | Description |
|---|---|---|
| `owner` | string | Table owner/schema. |
| `table_name` | string | Table name. |
| `column_name` | string | Column name. |
| `column_comment` | string/null | Column comment. |

### Mapping to `db_schema.json`

| SQL output | `db_schema.json` field | Mapping rule |
|---|---|---|
| `owner`, `table_name`, `column_name` | parent `tables[].columns[]` | Join on table and column keys. |
| `column_comment` | `tables[].columns[].comment` | 1:1; null remains null. |
| full row | `tables[].columns[].evidence[]` | Add `source_view='ALL_COL_COMMENTS'`, `owner`, `object_name=table_name`, `column_name`, `row_ref` with selected output columns. |

---

## 5) Top-level `db_schema.json` mapping

Some required `db_schema.json` fields are not directly produced by individual SQL result rows.
The collector must populate them as follows.

| `db_schema.json` field | Source | Rule |
|---|---|---|
| `schema_version` | Constant | `w6.db_schema.v1`. |
| `source.collector` | Collector implementation | Stable collector name/version, for example `lab.collect_db.oracle.v1`. |
| `source.collected_at` | Runtime clock | UTC ISO-8601 timestamp at collection completion. |
| `source.dictionary_views` | This SQL spec | Sorted unique list from Section 2. |
| `database.vendor` | Collector constant | `oracle`. |
| `database.host` | CLI `--host` | 1:1, never include password. |
| `database.port` | CLI `--port` | 1:1. |
| `database.service_name` | CLI `--service-name` | String or `null`. |
| `database.sid` | CLI `--sid` | String or `null`. |
| `owners` | CLI `--owner` / normalized include list | Uppercase included owners after removing `:system_owners`; min length 1. |
| `tables` | SQL Sections 4.1-4.6 | Merge by owner/table keys; deterministic order by `owner`, `table_name`. |
| `notes` | Collector validation | Empty array when no notes; otherwise factual strings about skipped/unknown metadata. |
| `needs_review` | Collector validation | `true` if any nested object has `needs_review=true` or collector detected incomplete metadata; otherwise `false`. |

---

## 6) End-to-end field coverage matrix

| `db_schema.spec.md` field | Producing SQL/source | Coverage rule |
|---|---|---|
| `tables[].table_id` | Table list SQL | Derived from `owner`, `table_name`. |
| `tables[].owner` | Table list SQL | Required. |
| `tables[].table_name` | Table list SQL | Required. |
| `tables[].table_comment` | Table comment SQL | Null when no comment row/comment value. |
| `tables[].columns[].name` | Column list SQL | Required. |
| `tables[].columns[].ordinal_position` | Column list SQL | Required; fallback only with `unknown=true`. |
| `tables[].columns[].data_type` | Column list SQL | Required. |
| `tables[].columns[].data_length` | Column list SQL | Optional/null. |
| `tables[].columns[].data_precision` | Column list SQL | Optional/null. |
| `tables[].columns[].data_scale` | Column list SQL | Optional/null. |
| `tables[].columns[].nullable` | Column list SQL | Derived from `nullable_flag`. |
| `tables[].columns[].default` | Column list SQL | Optional/null. |
| `tables[].columns[].comment` | Column comment SQL | Optional/null. |
| `tables[].primary_key.constraint_name` | PK SQL | Required when PK exists; otherwise `primary_key=null`. |
| `tables[].primary_key.columns[]` | PK SQL | Ordered by `column_position`. |
| `tables[].foreign_keys[].fk_id` | FK SQL | Derived from `owner`, `table_name`, `constraint_name`. |
| `tables[].foreign_keys[].constraint_name` | FK SQL | Required when FK exists. |
| `tables[].foreign_keys[].columns[]` | FK SQL | Ordered local columns. |
| `tables[].foreign_keys[].referenced_owner` | FK SQL | Required when FK exists. |
| `tables[].foreign_keys[].referenced_table` | FK SQL | Required when FK exists. |
| `tables[].foreign_keys[].column_mapping[]` | FK SQL | Ordered local/reference pairs. |
| `*.evidence[]` | All SQLs | At least one evidence object for every table/column/PK/FK. |
| `*.needs_review` | Collector validation | Boolean generated after merge/validation. |
| `*.unknown` | Collector validation | Boolean generated after required-field and consistency checks. |

---

## 7) Implementation checklist

- [x] Table list SQL defines purpose, inputs, output columns, owner filter, and mapping.
- [x] Column list SQL defines purpose, inputs, output columns, owner filter, and mapping.
- [x] PK SQL defines purpose, inputs, output columns, owner filter, and mapping.
- [x] FK SQL defines purpose, inputs, output columns, owner filter, and mapping.
- [x] Table comment SQL defines purpose, inputs, output columns, owner filter, and mapping.
- [x] Column comment SQL defines purpose, inputs, output columns, owner filter, and mapping.
- [x] Required views are fixed to `ALL_TABLES`, `ALL_TAB_COLUMNS`, `ALL_CONSTRAINTS`, `ALL_CONS_COLUMNS`, `ALL_TAB_COMMENTS`, and `ALL_COL_COMMENTS`.
- [x] Every SQL applies owner include and system-owner exclude filters.
- [x] `db_schema.spec.md` required fields are covered by direct, derived, or collector-runtime mappings.
