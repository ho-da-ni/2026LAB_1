# SPEC.md Section Structure (Template v2)

## 1) 문서 목적

`SPEC.md`는 Git diff + 정적 분석 evidence를 기준으로, 기능 단위 변경사항을 **검증 가능한 형태**로 기록한다.

---

## 2) 작성 원칙

- 변경 사실은 `changed_files.json`, 코드/설정 evidence, 정적 분석 결과로만 작성한다.
- 추정/가정 금지: 확인 불가 항목은 `UNKNOWN` 또는 `needs_review`로 표기한다.
- 동일 입력(`base/head`, 동일 필터)에서 동일 문서가 생성되도록 정렬 규칙을 고정한다.
- 서술형 설명과 팩트 표를 분리한다.

---

## 3) 문서 전체 섹션 구조

SPEC 문서는 아래 순서를 고정한다.

1. `# Change Specification Overview`
2. `## Metadata`
3. `## Diff Summary`
4. `## Feature Changes`
5. `## Interface/API Changes (Optional)`
6. `## Data/Schema Changes (Optional)`
7. `## Risk & Compatibility`
8. `## Validation Plan`
9. `## needs_review`
10. `## Appendix: Evidence Index`

---

## 4) 섹션별 상세 포맷

### 4.1 `# Change Specification Overview`

- 변경 대상(서비스/모듈)
- 변경 feature 수
- 변경 파일 수
- 생성 기준 시간

예시:

```md
# Change Specification Overview
- Project: `sample-service`
- Feature Change Count: `3`
- Changed Files: `14`
- Generated At: `2026-04-01T00:00:00Z`
```

### 4.2 `## Metadata`

필수 항목:

- `schema_version`
- `base/head/merge_base`
- `include_paths` / `exclude_paths`
- 입력 산출물 경로 (`changed_files.json`, `features.json`, `ir_merged.json`)

### 4.3 `## Diff Summary`

권장 테이블 컬럼:

- `path`
- `change_type` (`ADDED|MODIFIED|DELETED|RENAMED`)
- `language`
- `feature_id` (연결 가능 시)
- `evidence_ref`

정렬 기준:

- `path` 오름차순

### 4.4 `## Feature Changes`

각 feature는 아래 하위 섹션 구조를 강제한다.

```md
### {feature_name} (`{feature_id}`)

#### Change Intent
- 변경 목적(팩트 기반 요약)

#### Affected Files
- `path/to/file` (`ADDED|MODIFIED|DELETED`)

#### Behavior Delta
- Before: `...` | `UNKNOWN`
- After: `...` | `UNKNOWN`
- Trigger/Condition: `...` | `UNKNOWN`

#### Contract Delta
- Input Contract: `...` | `UNCHANGED` | `UNKNOWN`
- Output Contract: `...` | `UNCHANGED` | `UNKNOWN`
- Error/Exception Contract: `...` | `UNCHANGED` | `UNKNOWN`

#### Dependency/Impact
- Upstream Impact: `...` | `NONE` | `UNKNOWN`
- Downstream Impact: `...` | `NONE` | `UNKNOWN`

#### Evidence
- File: `...`
- Symbol: `...`
- Lines: `Lx-Ly`
- Diff Hunk: `@@ ... @@`

#### needs_review
- code: `needs_review.*`
- detail: `...`
```

정렬 기준:

- feature 섹션은 `(category, name, feature_id)` 오름차순

### 4.5 `## Interface/API Changes (Optional)`

- Endpoint 추가/수정/삭제 목록
- Method/Path/handler/feature_id 매핑
- Breaking 여부

### 4.6 `## Data/Schema Changes (Optional)`

- 테이블/컬럼/인덱스 변경
- DDL/매퍼 변경 evidence
- 마이그레이션 필요 여부

### 4.7 `## Risk & Compatibility`

권장 분류:

- `breaking_change`: `yes|no|unknown`
- `rollout_risk`: `low|medium|high|unknown`
- `rollback_plan`: `...` | `UNKNOWN`

### 4.8 `## Validation Plan`

최소 포함 항목:

- 실행한 검증 명령
- 기대 결과
- 실제 결과
- 실패 시 관찰된 에러

### 4.9 `## needs_review`

문서 전체 unresolved 항목 집계.

권장 컬럼:

- `code`
- `target` (`feature_id`, `path`, `endpoint_id` 등)
- `detail`
- `evidence_ref`

### 4.10 `## Appendix: Evidence Index`

evidence를 파일 기준으로 역추적 가능하게 요약한다.

- `file path`
- 참조 feature 개수
- 심볼 목록
- 라인 범위

---

## 5) 필수 체크리스트

- [ ] Metadata에 base/head/merge_base가 포함되었는가?
- [ ] Diff Summary의 경로 정렬이 고정되었는가?
- [ ] 모든 Feature Change에 evidence가 1건 이상 있는가?
- [ ] Contract Delta에 `UNCHANGED/UNKNOWN` 표기 규칙을 일관 적용했는가?
- [ ] Risk/Compatibility와 Validation Plan이 누락되지 않았는가?
- [ ] unresolved 항목을 `needs_review`로 분리했는가?

---

## 6) 금지 규칙

- evidence 없는 변경 주장 금지
- diff에 없는 변경 서술 금지
- 영향 범위 과장/추정 금지
- 정렬 기준 임의 변경 금지
