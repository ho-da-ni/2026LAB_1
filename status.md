# status.md

## Source of Truth: Task Board

| ID | Task | Status | 근거/비고 |
|---|---|---|---|
| W5-T01 | 중간공유 패키지/운영 문서 정비 | ✅ Done | `share_pack_mid/README.md`, `RUNBOOK.md`, `LIMITS.md` 반영 |
| W5-T02 | 3-command 데모 시나리오 고정 | ✅ Done | `detect-endpoints -> build-w4 -> generate api` 고정 |
| W5-T03 | 리허설 체크리스트/장애대응 문서화 | ✅ Done | RUNBOOK 절차 정리 |
| W5-T04 | 재현성 리허설(동일 입력/동일 해시) | ✅ Done | `API.md` 2회 생성 해시 동일 확인 |
| W5-T05 | 세션 상태/검증 로그 관리 | 🟡 In Progress | STATUS 누적 규칙 단순화 필요 |
| W4-T01 | `build-w4` 구현 | ✅ Done | `endpoints.json` 기반 `ir_merged.json`/`features.json` 생성 |
| W4-T03 | W4 산출물 결정론 규칙 연계 | ✅ Done | dedupe/정렬/evidence/feature_id 반영 |
| W4-T05 | `generate api` 고도화 | ✅ Done | feature 연계, wildcard/UNKNOWN needs_review 반영 |
| W4-T06 | API 문서 포맷 고정 | ✅ Done | 섹션/테이블 구조 결정론 유지 |
| W4-T08 | `generate spec` 구현 | ✅ Done | Overview/Metadata/Diff Summary/Feature Changes/Validation Plan/needs_review 생성 |
| W4-T09 | `validate` 품질 규칙 반영 | ✅ Done | strict/non-strict 자동 검증 |
| W3-T01 | Controller detection MVP | ✅ Done | fixture 기반 endpoint 추출 구현 |
| W3-T02 | endpoint_id 결정론 규칙 적용 | ✅ Done | `ep_` + sha1 16자리 |
| W3-T03 | CLI 산출물 생성 연계 | ✅ Done | `detect-endpoints` 실생성 확인 |
| W3-T04 | source evidence 기록 | ✅ Done | endpoint evidence 포함 |
| W3-T07 | W3 자동화 테스트 | ✅ Done | `tests/test_w3_controller_detection.py` |
| W3-T09 | fixture/golden/quality gate 확장 | ✅ Done | 10개 케이스 기준 자동 검증 통과 |
| W2-T01 | `analyze` 산출물 생성 | ✅ Done | `repo_meta.json`, `scan_index.json` |
| W2-T02 | `diff` 기본 동작/실패코드 | ✅ Done | exit code 3/5/7 반영 |
| W2-T03 | changed_files 안정 정렬 | ✅ Done | path/status/old_path 정렬 |
| W2-T04 | W2 산출물 테스트 | ✅ Done | pytest 자동화 |
| W2-T06 | 실패 계약 테스트 | ✅ Done | 예외/실패 시나리오 검증 |
| W2-T08 | include/exclude 정규화 | ✅ Done | S07 경로 패턴 케이스 통과 |
| W6-T01 | DB schema 수집/정규화/문서화 축 완성 | ✅ Done | `generate db-schema` JSON/Markdown 동시 생성 + fixture smoke test 반영 |
| W6-T02 | DB schema 검증 규칙 강화 | ✅ Done | `validate_db` integrity/metadata/tables/source_evidence/markdown marker 규칙 반영 |
| W6-DB-01 | DB 수집용 CLI 인자 규격 정의 | ✅ Done | `db_collect_cli_spec.md` 작성 완료 |
| W6-DB-02 | 접속 정보 전달/마스킹 정책 정의 | ✅ Done | `db_connection_policy.md` 작성 완료 |
| W6-DB-03 | Oracle 수집 대상/제외 범위 정의 | ✅ Done | `oracle_collection_scope.md` 작성 완료 |
| W6-DB-04 | DB IR 스키마 정의 | ✅ Done | `db_schema.spec.md` 작성 완료 |
| W6-DB-06 | Oracle metadata SQL spec 작성 | ✅ Done | `oracle_metadata_sql_spec.md`에 ALL_* 조회 SQL/필드 매핑 계약 고정 |
| NEXT-01 | `generate db-schema` 구현 | ✅ Done | W6 산출물 기준 완료, `tests/test_w6_db_schema_smoke.py` 추가 |
| NEXT-02 | S02/S06 CI 자동 판정기 | ⬜ Todo | 임시 repo/훅 의존 제거 필요 |
| NEXT-03 | 샘플 repo fixture 실제 추가 | ⬜ Todo | `examples/repo-sample` 필요 |
| OPS-01 | Codex 운영 규칙 고정 | ✅ Done | 루트 `AGENTS.md` 생성, README `status.md` 표기 통일 |
| NEXT-04 | 실DB collector 구현 | ✅ Done | `src/lab/db/oracle_collector.py` live query collector 추가, `collect_db.py` live 접속 경로 전환 |
| NEXT-05 | 실 Oracle 환경 검증 | ⬜ Todo | 실제 Oracle 접속 정보로 FAIL_FAST/정상 raw metadata 생성 재검증 필요 |
| NEXT-06 | Oracle raw metadata mapper/assembler 구현 | ✅ Done | table/column/comment mapper, PK/FK assembler, evidence/unknown/stable ID 테스트 보강 |

---

## 현재 목표
- `lab collect db` live Oracle query collector를 구현한 상태이며, 다음 0순위는 실제 Oracle 환경에서 접속 실패/정상 수집 E2E를 검증하는 것이다.

## 진행 중(핵심)
- `lab validate`의 리포트 포맷/스키마 세부 규칙 고도화(단일 CI fail-fast 기준 정교화).
- `status.md` 검증 명령 기록 정책(세션 누적 방식) 단순화.
- 실 Oracle 환경 검증 준비: `oracle_metadata_sql_spec.md` 기준 live query collector와 raw metadata mapper/assembler 구현은 완료됐고, 실제 DB credential/네트워크 환경에서 재검증해야 한다.
- S02/S06 전용 CI 자동 판정 스크립트 설계.

## 완료 하이라이트
- W2~W5 핵심 명령(`analyze`, `diff`, `detect-endpoints`, `build-w4`, `generate api`, `generate spec`, `validate`) 구현 및 테스트 연계 완료.
- LLM OFF E2E에서 정상 케이스/경고 케이스 모두 재현, strict/non-strict 정책 차이 검증 완료.
- W3 fixture/golden/quality gate 10케이스 자동 검증 체계 확정.
- W6 DB schema 축 완료: 정규화 강화, `DB_SCHEMA.md` Integrity 섹션 추가, `validate_db` 규칙 강화, fixture smoke test 추가.
- W6 DB 문서 계약 고정: `db_collect_cli_spec.md`, `db_connection_policy.md`, `oracle_collection_scope.md`, `db_schema.spec.md` 추가.
- Codex 운영 규칙 고정: 루트 `AGENTS.md`에 `status.md` 작업 시작/종료 갱신 의무와 완료 조건을 명시하고, README 표기를 실제 파일명 `status.md`로 통일.
- Oracle metadata SQL spec 고정: `oracle_metadata_sql_spec.md`에 table/column/PK/FK/table comment/column comment SQL과 `db_schema.json` 필드 매핑표를 작성.
- 실DB collector 구현: `src/lab/db/oracle_collector.py`를 추가해 `oracledb` 선택 의존성 기반 live Oracle 접속, owner-filtered ALL_* 조회, raw metadata/assembled tables 저장, secret-safe FAIL_FAST 경로를 구현.
- Oracle raw metadata mapper/assembler 구현: table/column/comment mapper와 PK/FK assembler를 분리하고 단일/복합 PK/FK, column order, evidence, unknown/needs_review, stable `table_id`/`fk_id` 테스트를 추가; `validate_db`의 `db_schema.schema.json` 재귀 검증과 owner fallback 정규화를 보강.

## 다음 액션(우선순위)
1. 실 Oracle 환경 검증: `pip install -e .[oracle]` 환경에서 잘못된 접속 정보 FAIL_FAST, 정상 접속 raw metadata 생성, password 미노출을 재검증.
2. live `db_collection.json` fixture를 추가해 `generate db-schema`/`validate_db` 회귀 테스트를 강화.
3. S02/S06 전용 검증을 CI 친화형 자동 판정 스크립트로 고정.
4. `examples/repo-sample` fixture 보강으로 문서/실행 환경 정합성 확보.
5. `status.md` 검증 로그 누적 규칙(요약 템플릿) 확정.
6. W6 validate rule 중 WARN/ERROR 경계(`source_evidence`) 정책 확정.

## 최근 검증 요약
- `PYTHONPATH=src pytest -q` 다회 실행 기준 최종 16 passed 확인.
- W5 3-command 데모 재실행 시 `API.md` 해시 동일 확인.
- LLM OFF full E2E(run3)에서 analyze → diff → generate api → validate → validate --strict 전 단계 성공.
- `PYTHONPATH=src pytest -q tests/test_w4_docs_and_quality.py::test_w4_generate_db_schema_outputs_json_and_markdown tests/test_w4_docs_and_quality.py::test_w4_validate_db_schema_markdown_sections_and_unknown_policy tests/test_w6_db_schema_smoke.py` 실행 결과 4 passed.
- `PYTHONPATH=src python -m lab generate db-schema --help`로 `--input/--json-output/--output` 계약 확인.
- `PYTHONPATH=src python -m lab generate db-schema --input tests/fixtures/db/sample_db_input.json --json-output <tmp>/db_schema.json --output <tmp>/DB_SCHEMA.md` smoke 실행으로 JSON/Markdown 동시 생성 확인.
- `rg -n 'STATUS[.]md|STATUS[[:space:]]검증' README.md status.md AGENTS.md share_pack_mid/README.md docs/VALIDATION_TEST_SCENARIOS.md docs/QUALITY_RULES.md || true` 실행 결과 README/status 운영 문서 범위에서 대문자 파일명 표기 없음 확인.
- `PYTHONPATH=src pytest -q` 실행 결과 32 passed 확인.
- `python - <<'PY' ...` 스펙 내용 점검 실행 결과 `oracle_metadata_sql_spec.md required content PASS` 확인(필수 ALL_* 뷰, 6개 SQL 섹션, owner filter, 주요 db_schema 매핑 필드 존재).
- `PYTHONPATH=src pytest -q` 재실행 결과 32 passed 확인.
- `PYTHONPATH=src pytest -q tests/test_w6_db_schema_smoke.py` 실행 결과 7 passed 확인(live collector fake driver 정상 수집/FAIL_FAST secret-safe 경로 포함).
- `python -m py_compile src/lab/db/oracle_collector.py src/lab/commands/collect_db.py` 실행 결과 PASS 확인.
- `PYTHONPATH=src pytest -q` 실행 결과 33 passed 확인.
- `git diff --check` 실행 결과 PASS 확인.
- `rg -n "placeholder[_]no[_]live[_]query" src tests *.md docs || true` 실행 결과 해당 legacy collection mode 문자열 없음 확인.
- `PYTHONPATH=src pytest -q tests/test_w6_db_schema_smoke.py` 재실행 결과 9 passed 확인(복합 PK/FK mapper/assembler, validate_db schema 계약 PASS 포함).
- `PYTHONPATH=src pytest -q` 재실행 결과 35 passed 확인.
- `python -m py_compile src/lab/db/oracle_collector.py src/lab/commands/collect_db.py src/lab/db/normalizer.py src/lab/quality/validate_db.py` 재실행 결과 PASS 확인.
- `git diff --check` 재실행 결과 PASS 확인.

## 결정사항 / 리스크
- 결정: `generated_at_utc`는 payload 유지, fingerprint 계산에서는 제외.
- 결정: S06 검증용 hidden test hook 유지(운영 경로 오염 방지).
- 결정: optional artifact 누락은 strict 실패가 아닌 INFO 처리.
- 결정: DB schema 문서(`DB_SCHEMA.md`)에 `## Integrity` 섹션을 필수 마커로 포함.
- 결정: `source_evidence` 비어있음은 현재 WARN(`QR-DB-006`)으로 검증.
- 리스크: quality gate 세부 스키마/리포트 규칙은 추가 고도화 필요.
- 리스크: 일부 검증이 임시 브랜치/임시 repo 생성에 의존.
- 리스크: DB 전용 validate 실행 시에도 `run_context.json`, `changed_files.json` 필수 요구로 UX 제약 존재.
- 리스크: 실제 Oracle 서버/계정/네트워크를 사용하는 live E2E 검증은 아직 미실행이며, 현재 자동 테스트는 fake driver 기반이다.


#### 2026-05-07 10:10
- Scope: OPS-01 Codex 운영 규칙 고정 및 `status.md` 파일명/운영 규칙 정리.
- Completed: 루트 `AGENTS.md`를 생성해 작업 시작 전/종료 전 `status.md` 읽기/갱신 의무와 Codex 작업 완료 조건을 명시함; README의 `status.md` 표기를 실제 파일명 `status.md`로 통일함; 다음 작업을 실DB collector 구현으로 재정렬함.
- Files changed: `AGENTS.md`, `README.md`, `status.md`.
- Validation: `rg -n 'STATUS[.]md|STATUS[[:space:]]검증' README.md status.md AGENTS.md share_pack_mid/README.md docs/VALIDATION_TEST_SCENARIOS.md docs/QUALITY_RULES.md || true` PASS (대문자 파일명 표기 없음); `PYTHONPATH=src pytest -q` PASS (32 passed).
- Status: PASS (문서/운영 규칙 반영 및 전체 테스트 통과; repo runnable).
- Risks / blockers: `src/lab/commands/collect_db.py`는 아직 placeholder로, 실DB 접속/Oracle 메타데이터 조회가 미구현 상태.
- Next actions: 다음 세션에서 실DB collector 구현을 시작하고, `src/lab/commands/collect_db.py` placeholder를 Oracle live metadata collector로 교체.


#### 2026-05-07 10:17
- Scope: W6-DB-06 Oracle metadata SQL spec 작성.
- Completed: `oracle_metadata_sql_spec.md`에 table 목록, column 목록, PK, FK, table comment, column comment 조회 SQL을 고정하고 각 SQL의 목적/입력/출력 컬럼/`db_schema.json` 매핑표를 작성함; 모든 SQL에 owner include 및 system owner exclude 필터를 명시함.
- Files changed: `oracle_metadata_sql_spec.md`, `status.md`.
- Validation: `python - <<'PY' ...` PASS (`oracle_metadata_sql_spec.md required content PASS`); `PYTHONPATH=src pytest -q` PASS (32 passed).
- Status: PASS (SQL spec 문서화 완료, repo runnable).
- Risks / blockers: `src/lab/commands/collect_db.py`는 여전히 placeholder이며 이번 작업은 SQL 계약 문서화까지만 완료함; 실제 Oracle 연결 환경 검증은 아직 미실행.
- Next actions: 실DB collector 구현에서 `oracle_metadata_sql_spec.md` SQL을 실행하고 결과를 `db_schema.spec.md`/`db_schema.schema.json` 구조로 정규화.


#### 2026-05-07 10:28
- Scope: NEXT-04 collect_db.py placeholder 제거 및 live Oracle query collector 구현.
- Completed: `src/lab/db/oracle_collector.py` 추가; `src/lab/commands/collect_db.py`를 live Oracle 접속/조회 경로로 전환; `ALL_TABLES`, `ALL_TAB_COLUMNS`, `ALL_CONSTRAINTS`, `ALL_CONS_COLUMNS`, `ALL_TAB_COMMENTS`, `ALL_COL_COMMENTS` owner-filtered raw metadata 수집 및 `db_collection.json` 저장 구현; optional `oracledb` 의존성 정책 문서화; fake driver 기반 정상/FAIL_FAST secret-safe 테스트 추가.
- Files changed: `AGENTS.md`, `db_collect_cli_spec.md`, `db_connection_policy.md`, `pyproject.toml`, `src/lab/commands/collect_db.py`, `src/lab/db/oracle_collector.py`, `src/lab/exit_codes.py`, `tests/test_w6_db_schema_smoke.py`, `status.md`.
- Validation: `python -m py_compile src/lab/db/oracle_collector.py src/lab/commands/collect_db.py` PASS; `PYTHONPATH=src pytest -q tests/test_w6_db_schema_smoke.py` PASS (7 passed); `PYTHONPATH=src pytest -q` PASS (33 passed); `git diff --check` PASS.
- Status: PASS (live collector implementation and automated fake-driver validation complete; repo runnable).
- Risks / blockers: 실제 Oracle 접속 환경이 없어 live DB E2E는 아직 미검증; 운영 실행 전 `pip install -e .[oracle]` 또는 `oracledb` 설치 필요.
- Next actions: 실제 Oracle 접속 정보로 FAIL_FAST/정상 수집/password 미노출을 재검증하고 live `db_collection.json` fixture 기반 `generate db-schema`/`validate_db` 테스트를 추가.


#### 2026-05-07 10:35
- Scope: NEXT-06 Oracle raw metadata mapper/assembler 구현.
- Completed: `src/lab/db/oracle_collector.py`의 raw row 조립 로직을 table mapper, column mapper, PK assembler, FK assembler, comment mapper/evidence helper로 분리함; stable `table_id`/`fk_id`, column order 보존, 단일/복합 PK/FK, evidence 누락 방지, unknown/needs_review 처리와 누락 컬럼 fallback을 보강함; `src/lab/quality/validate_db.py`에 `db_schema.schema.json` 재귀 검증을 추가하고 `src/lab/db/normalizer.py`에 owner fallback을 보강함; tests에 복합 PK/FK와 schema 계약 검증을 추가함.
- Files changed: `src/lab/db/oracle_collector.py`, `src/lab/db/normalizer.py`, `src/lab/quality/validate_db.py`, `tests/test_w6_db_schema_smoke.py`, `status.md`.
- Validation: `rg -n "placeholder[_]no[_]live[_]query" src tests *.md docs || true` PASS (legacy mode 문자열 없음); `PYTHONPATH=src pytest -q tests/test_w6_db_schema_smoke.py` PASS (9 passed); `PYTHONPATH=src pytest -q` PASS (35 passed); `python -m py_compile src/lab/db/oracle_collector.py src/lab/commands/collect_db.py src/lab/db/normalizer.py src/lab/quality/validate_db.py` PASS; `git diff --check` PASS.
- Status: PASS (mapper/assembler 구현 및 자동 검증 완료, repo runnable).
- Risks / blockers: 실제 Oracle 접속 환경 기반 검증은 아직 미실행; 현재 `db_schema.schema.json` 계약 검증은 fake/raw metadata 기반 `validate_db_schema_json` 자동 테스트로 수행.
- Next actions: 실제 Oracle 접속 정보로 live `db_collection.json`을 생성하고 `generate db-schema`/`validate_db` 및 JSON schema 검증을 재실행.

#### 2026-05-07 10:44
- Scope: W6-DB Markdown integrity marker alignment and CLI spec example correction.
- Completed: Added required `## Integrity` section to DB schema markdown renderer with the current JSON schema/run artifact validation policy; added `## Integrity` to DB markdown validation markers; updated DB collect CLI spec example B to include required `--owner`; added regression asserts for rendered integrity policy text and missing marker detection.
- Files changed: `db_collect_cli_spec.md`, `src/lab/db/renderer.py`, `src/lab/quality/validate_db.py`, `tests/test_w6_db_schema_smoke.py`, `tests/test_w4_docs_and_quality.py`, `status.md`.
- Validation: `PYTHONPATH=src pytest -q tests/test_w6_db_schema_smoke.py tests/test_w4_docs_and_quality.py` PASS (17 passed); `PYTHONPATH=src pytest -q` PASS (35 passed); `python -m py_compile src/lab/db/renderer.py src/lab/quality/validate_db.py` PASS; `git diff --check` PASS.
- Status: PASS (DB schema markdown integrity policy/validation markers aligned with generated output; repo runnable).
- Risks / blockers: Actual Oracle connection validation remains unrun in this environment; current live collector validation remains fake-driver based.
- Next actions: Validate against a real Oracle connection, then add live `db_collection.json` fixture coverage for `generate db-schema`/`validate_db`.

#### 2026-05-09 00:00
- Scope: W6-DB database target one-of validation.
- Completed: Added explicit `database.service_name`/`database.sid` one-of validation so exactly one non-empty target is accepted; mirrored the contract in `db_schema.schema.json`; allowed fixture metadata `service_name`/`sid` to flow through normalization; added regression coverage for service-only PASS, SID-only PASS, both-present FAIL, and both-null FAIL.
- Files changed: `db_schema.schema.json`, `src/lab/db/normalizer.py`, `src/lab/quality/validate_db.py`, `tests/fixtures/db/sample_db_input.json`, `tests/test_w6_db_schema_smoke.py`, `status.md`.
- Validation: `PYTHONPATH=src pytest -q tests/test_w6_db_schema_smoke.py::test_w6_db_schema_validate_database_target_one_of -q` PASS; `PYTHONPATH=src pytest -q` PASS (36 passed); `python -m py_compile src/lab/db/normalizer.py src/lab/quality/validate_db.py` PASS; `git diff --check` PASS.
- Status: PASS (database target one-of validation implemented and repo runnable).
- Risks / blockers: Actual Oracle connection validation remains unrun in this environment; current live collector validation remains fake-driver based.
- Next actions: Validate against a real Oracle connection, then add live `db_collection.json` fixture coverage for `generate db-schema`/`validate_db`.

#### 2026-05-09 - NEXT-05 실 Oracle 환경 검증
- Scope: Docker Oracle Free 컨테이너 기반 LAB live DB 수집 E2E 검증.
- DB Target:
  - host: localhost
  - port: 1521
  - service_name: FREEPDB1
  - username: LAB_USER
  - owner: LAB_USER
  - password: env `LAB_DB_PASSWORD`
- Completed:
  - Oracle 컨테이너 `DATABASE IS READY TO USE!` 확인.
  - `lab collect db` 실행 성공.
  - `artifacts/db/local-oracle/db_collection.json` 생성 확인.
- Files changed: `status.md`.
- Validation:
  - PASS: `lab collect db --host localhost --port 1521 --service-name FREEPDB1 --username LAB_USER --password-env LAB_DB_PASSWORD --owner LAB_USER --output-dir artifacts/db/local-oracle --timeout 60 --include-comments --format json`
- Status: PASS (Docker Oracle Free 기반 live DB 수집 E2E 검증 완료; `db_collection.json` 생성 확인; repo runnable state는 다음 generate/validate 단계 전).
- Risks / blockers: `db_collection.json`의 기대 테이블 포함 여부 및 `generate db-schema`/`validate_db` 단계는 아직 미확인.
- Next actions:
  - `db_collection.json` 내 `SAMPLE_DEPARTMENT`, `SAMPLE_USER`, `SAMPLE_API` 포함 여부 확인.
  - `lab generate db-schema` 실행.
  - `db_schema.json`, `DB_SCHEMA.md` 생성 확인.
