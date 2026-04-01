# QUALITY_RULES.md

IR/API/FEATURES/SPEC 산출물 품질 검증을 위한 상세 규칙을 정의한다.

---

## 1) 품질 규칙 적용 범위

- `artifacts/ir_merged.json`
- `artifacts/features.json`
- `docs/API.md`
- `docs/SPEC.md`

검증 단계:

1. 구조 검증 (필수 필드/타입)
2. 정규화 검증 (정렬/중복/포맷)
3. 의미 검증 (충돌/불확실성/근거 존재)

---

## 2) 규칙 레벨

- `ERROR`: 산출물 실패(파이프라인 실패)
- `WARN`: 산출물 생성은 허용, `needs_review` 필수
- `INFO`: 개선 권고

---

## 3) 상세 규칙 목록

## 3.1 공통 규칙

### QR-COMMON-001 (ERROR)
- 조건: required 필드 누락
- 조치: 생성 실패

### QR-COMMON-002 (ERROR)
- 조건: 배열 정렬/중복제거 규칙 위반
- 조치: 정렬/중복제거 재실행 후 재검증

### QR-COMMON-003 (WARN)
- 조건: 문자열 필드가 빈 문자열 또는 공백만 존재
- 조치: `UNKNOWN`으로 정규화 + `needs_review.empty_value`

---

## 3.2 `ir_merged.json` 규칙

### QR-IR-001 (ERROR)
- 조건: endpoint에 `endpoint_id`, `method`, `path`, `source_evidence` 중 하나라도 누락
- 조치: endpoint 생성 중단

### QR-IR-002 (WARN) — `method = UNKNOWN`
- 조건: method 확정 실패로 `UNKNOWN_METHOD` 또는 `UNKNOWN` 사용
- 조치: endpoint 유지 가능, `needs_review.method_unknown` 기록

### QR-IR-003 (WARN) — `http='*'`
- 조건: method가 `*` 또는 ALL-catch 형식으로만 존재
- 조치:
  - endpoint는 유지
  - `needs_review.http_wildcard` 추가
  - 가능한 method 추론 근거가 있으면 evidence note에 남김

### QR-IR-004 (ERROR) — Evidence 누락
- 조건: `source_evidence`가 비어 있음
- 조치:
  - endpoint drop 또는 생성 실패
  - 최소 1건 evidence 확보 전 확정 금지

### QR-IR-005 (WARN) — 경로/핸들러 충돌
- 조건: 동일 `METHOD + PATH`에 handler 2개 이상
- 조치: `needs_review.mapping_route_conflict` 기록, 자동 병합 금지

### QR-IR-006 (WARN) — Path 폭증
- 조건: 매핑 조합 수가 임계치 초과
- 조치: `needs_review.multi_path_expansion_overflow` 기록

---

## 3.3 `features.json` 규칙

### QR-FEAT-001 (ERROR)
- 조건: `feature_id` 형식 위반(`^feat_[0-9a-f]{16}(?:_[0-9]{2})?$`)
- 조치: feature 생성 실패

### QR-FEAT-002 (ERROR) — Evidence 누락
- 조건: `evidence` 배열이 비어 있음
- 조치:
  - feature 확정 금지
  - `needs_review.evidence_missing` 기록 후 제외(기본)

### QR-FEAT-003 (WARN) — 주요 필드 UNKNOWN
- 조건: `name/category/status` 중 하나가 `UNKNOWN`
- 조치: `needs_review.feature_unknown_core_field`

### QR-FEAT-004 (WARN)
- 조건: 동일 `feature_id`에서 category 상충
- 조치: `needs_review.feature_category_conflict`, 자동 병합 금지

### QR-FEAT-005 (WARN)
- 조건: 동일 `name+category`인데 signals 불일치
- 조치: `needs_review.feature_signal_conflict`

---

## 3.4 `API.md` 규칙

### QR-API-001 (ERROR)
- 조건: endpoint 섹션에 `method/path/endpoint_id` 중 누락
- 조치: 문서 생성 실패

### QR-API-002 (WARN) — `http='*'`
- 조건: endpoint 제목이 `* /path` 또는 wildcard method
- 조치: `needs_review.http_wildcard`를 endpoint 섹션에 기록

### QR-API-003 (WARN) — `UNKNOWN`
- 조건: Request/Response/Security 핵심 항목 `UNKNOWN`
- 조치: 허용하되 근거 파일/라인을 반드시 병기

### QR-API-004 (ERROR) — Source Evidence 누락
- 조건: endpoint 섹션에 Source Evidence 블록 없음
- 조치: 문서 생성 실패

---

## 3.5 `SPEC.md` 규칙

### QR-SPEC-001 (ERROR)
- 조건: Feature Change 항목에 Evidence 없음
- 조치: Feature Change 섹션 drop 또는 생성 실패

### QR-SPEC-002 (WARN) — `UNKNOWN`
- 조건: Before/After/Contract에 `UNKNOWN` 사용
- 조치: 허용하되 `needs_review.spec_unknown_contract` 기록

### QR-SPEC-003 (ERROR)
- 조건: Diff Summary에 없는 파일을 Affected Files에 기재
- 조치: 불일치 항목 제거 후 재검증

---

## 4) `UNKNOWN`/`*`/Evidence 누락 처리 정책 요약

1. `UNKNOWN`
   - 기본 허용 범위: `WARN`
   - 단, core 식별 필드(`endpoint_id`, `feature_id`, `method/path`, evidence)는 `ERROR`
2. `http='*'`
   - 기본 허용 범위: `WARN`
   - 필수 후속조치: `needs_review.http_wildcard` + 관련 근거 명시
3. evidence 누락
   - 기본 정책: `ERROR`
   - endpoint/feature/spec 항목 확정 금지

---

## 5) 권장 출력 포맷 (검증 결과)

```json
{
  "status": "warn",
  "errors": [],
  "warnings": [
    {
      "code": "QR-IR-003",
      "target": "endpoints[4]",
      "detail": "method='*' detected",
      "needs_review_code": "needs_review.http_wildcard"
    }
  ]
}
```

---

## 6) 운영 규칙

- 신규 품질 규칙 추가 시 rule code namespace를 유지한다 (`QR-IR-*`, `QR-FEAT-*` 등).
- ERROR→WARN 완화 또는 WARN→ERROR 강화 시 변경 이력(`status.md`)에 사유를 남긴다.
- 품질 규칙 위반 통계는 run_context 품질 메타 섹션에 누적한다.
