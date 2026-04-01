# API.md Section Structure (Template v2)

## 1) 문서 목적

소스 코드 정적 분석 및 메타데이터 기반으로 확인 가능한 API 정보를 **재현 가능하게** 기록한다.

---

## 2) 작성 원칙

- 확인되지 않은 endpoint는 작성하지 않는다.
- 추정값 금지: 근거가 없으면 `UNKNOWN` 또는 `needs_review`로 표기한다.
- 동일 입력에 대해 동일 문서가 생성되도록 정렬/표기 규칙을 고정한다.
- 각 endpoint는 반드시 source evidence를 포함한다.

---

## 3) 문서 전체 섹션 구조

API 문서는 아래 순서를 고정한다.

1. `# API Overview`
2. `## Metadata`
3. `## Endpoint Index`
4. `## Endpoints`
5. `## Data Models (Optional)`
6. `## Security/Auth Matrix (Optional)`
7. `## needs_review`
8. `## Appendix: Source Evidence Summary`

---

## 4) 섹션별 상세 포맷

### 4.1 `# API Overview`

- 문서 스코프(프로젝트/모듈)
- endpoint 총 개수
- 생성 기준(브랜치/커밋/생성 시각)

예시:

```md
# API Overview
- Project: `sample-service`
- Endpoint Count: `12`
- Generated At: `2026-04-01T00:00:00Z`
```

### 4.2 `## Metadata`

- `schema_version`
- `source` (`ir_merged.json` 경로)
- `base/head/merge_base`
- 필터(include/exclude) 적용 여부

### 4.3 `## Endpoint Index`

테이블 형태로 최소 컬럼 포함:

- `endpoint_id`
- `method`
- `path`
- `handler`
- `auth`
- `feature_id` (연계 가능 시)

정렬 기준:

- `(path, method, endpoint_id)` 오름차순

### 4.4 `## Endpoints`

각 endpoint는 아래 하위 섹션 구조를 강제한다.

```md
### {METHOD} {PATH} (`{endpoint_id}`)

#### Summary
- Handler: `...`
- Feature: `feat_...` | `UNKNOWN`
- Status: `active` | `deprecated` | `experimental` | `unknown`

#### Request
- Content-Type: `...`
- Path Params: `...`
- Query Params: `...`
- Headers: `...`
- Body Schema: `...` | `UNKNOWN`

#### Response
- Success: `...`
- Error: `...`
- Response Schema: `...` | `UNKNOWN`

#### Security
- Auth Required: `true|false|UNKNOWN`
- Roles/Scopes: `...` | `UNKNOWN`

#### Exceptions
- `ExceptionType` - 조건/메시지 요약
- 불명확 시 `UNKNOWN`

#### Source Evidence
- File: `path`
- Symbol: `...`
- Lines: `Lx-Ly`
- Annotation/Signature: `...`

#### needs_review
- code: `needs_review.*`
- detail: `...`
```

### 4.5 `## Data Models (Optional)`

- 요청/응답 DTO 스키마 요약
- 필드 타입/nullable/제약조건

### 4.6 `## Security/Auth Matrix (Optional)`

- 행: endpoint_id
- 열: 인증 필요 여부, role/scope, 근거 위치

### 4.7 `## needs_review`

문서 전체 unresolved 항목을 code 기준으로 집계한다.

권장 컬럼:

- `code`
- `endpoint_id` (또는 대상 path/method)
- `detail`
- `evidence_ref`

### 4.8 `## Appendix: Source Evidence Summary`

파일 단위로 evidence를 역인덱싱한다.

- `file path`
- 참조 endpoint 개수
- 심볼 목록

---

## 5) 필수 필드 체크리스트

각 endpoint 섹션에 아래 항목이 모두 있어야 한다.

- [ ] method
- [ ] path
- [ ] endpoint_id
- [ ] handler
- [ ] auth/security
- [ ] request/response 요약
- [ ] source evidence 1건 이상
- [ ] needs_review(없으면 `없음` 명시)

---

## 6) 금지 규칙

- 근거 없는 응답 코드/스키마/권한 추정 작성 금지
- endpoint_id 누락 금지
- source evidence 없는 endpoint 기재 금지
- 정렬 기준 임의 변경 금지
