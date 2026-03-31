# Controller/Endpoint 탐지 Fixture 케이스 목록 (초안)

## 목적
- Spring Boot/eGovFrame Controller 탐지 규칙 문서의 구현 검증을 위해, 재현 가능한 fixture 케이스 집합을 정의한다.
- 케이스별 기대 결과를 고정해 파서/정규화/합성 로직 회귀를 빠르게 감지한다.

## 범위
- 대상 엔진: Spring Boot 전용 룰셋, eGovFrame 전용 룰셋
- 검증 축: path/method 합성, multi-path/multi-method 전개, `endpoint_id` 결정론, 충돌/`needs_review` 코드
- 제외: 런타임 의존 동작(실제 DispatcherServlet 실행 결과), 네트워크/DB 연동

## 공통 규칙
- 각 fixture는 `case_id`, `framework`, `input_sources`, `expected_endpoints`, `expected_needs_review`를 가진다.
- 기대값은 "확정 가능한 사실만" 기록한다.
- 정렬 기준(method/path/endpoint_id)은 규칙 문서의 canonical 순서를 따른다.
- `UNKNOWN`이 기대되는 케이스는 반드시 이유 코드를 포함한다.

---

## A. Core Mapping 합성 케이스

### C001: 단일 class + 단일 method path
- 목적: 기본 결합(`/api` + `/users`) 검증
- 기대: endpoint 1건, `GET /api/users`

### C002: class path 배열 × method path 배열
- 목적: 카티시안 전개와 정렬 검증
- 기대: 4건 전개, 사전순 path 출력

### C003: 루트/빈문자열 중립값 결합
- 목적: `""`, `/` 처리 일관성 검증
- 기대: prefix 생략 규칙 적용

### C004: 중복 슬래시 정규화
- 목적: `/api//` + `//users` 정규화 검증
- 기대: `/api/users` 1건

---

## B. Multi-Method/HTTP 배열 케이스

### M001: 축약 매핑 단일 method
- 목적: `@GetMapping` -> 길이 1 배열 승격 검증
- 기대: `GET` 확정

### M002: `RequestMethod[]` 다중 지정
- 목적: `{GET,POST}` 정규화 + 다건 전개 검증
- 기대: method 2건 endpoint 생성

### M003: class-method 교집합
- 목적: class `{GET,POST}` + method `{POST,PUT}` 교집합 검증
- 기대: `POST`만 유지

### M004: method 충돌(공집합)
- 목적: class `GET` + method `POST` 충돌 처리
- 기대: endpoint 미확정, `needs_review.mapping_method_conflict`

### M005: 빈 method 배열
- 목적: `method={}` -> `UNKNOWN_METHOD` 치환 검증
- 기대: `Method=UNKNOWN`, `confidence=needs_review`

---

## C. endpoint_id 결정론 케이스

### I001: 동일 canonical source 재실행
- 목적: 실행 시각/파일 위치 무관 동일 ID 검증
- 기대: 동일 `endpoint_id`

### I002: method만 다른 경우
- 목적: canonical tuple 변화 반영 검증
- 기대: 서로 다른 `endpoint_id`

### I003: path만 다른 경우
- 목적: ID 분리 검증
- 기대: 서로 다른 `endpoint_id`

### I004: `UNKNOWN` 포함 tuple
- 목적: placeholder 포함 ID 생성 검증
- 기대: `endpoint_id` 생성됨 + `confidence=needs_review`

### I005: 인위적 충돌 주입
- 목적: collision 감지 경로 검증
- 기대: `needs_review.endpoint_id_collision`

---

## D. eGovFrame 특화 케이스

### E001: `*.do` 기본 보존
- 목적: `/usr/selectUserList.do` 원형 유지 검증
- 기대: path 치환 없이 유지

### E002: View endpoint (`String` + `ModelMap`)
- 목적: view/api 분류 검증
- 기대: `Endpoint Type=view`

### E003: API endpoint (`@ResponseBody`)
- 목적: view/api 분류 검증
- 기대: `Endpoint Type=api`

### E004: `commandMap` 파라미터
- 목적: 관례 입력 처리 검증
- 기대: 구조 미확정 입력으로 기록

### E005: XML+Annotation 중복 매핑
- 목적: dedupe + evidence 병합 검증
- 기대: endpoint 1건, evidence 2소스

---

## E. 오류/경계 케이스

### X001: 파싱 실패 파일 포함
- 목적: fail-fast/경고 정책 검증
- 기대: 오류 리포트 + 분석 중단/격리

### X002: multi-path 폭증
- 목적: 임계치(기본 256) 초과 처리 검증
- 기대: `needs_review.multi_path_expansion_overflow`

### X003: 동일 METHOD+PATH에 상이 handler
- 목적: 라우트 충돌 검증
- 기대: `needs_review.mapping_route_conflict`

### X004: 외부 prefix만 존재
- 목적: 코드에서 확정 불가 path 처리
- 기대: 코드 기준 path + `needs_review.external_prefix_unresolved`

---

## 우선순위(Phase 제안)
1. **Phase 1 (필수, 12건)**: C001~C004, M001~M004, I001~I002
2. **Phase 2 (확장, 8건)**: M005, I003~I005, E001~E003
3. **Phase 3 (레거시/오류, 6건)**: E004~E005, X001~X004

## 네이밍 규칙 제안
- fixture 폴더: `tests/fixtures/controller_detection/<framework>/<case_id>/`
- 파일 기본 세트:
  - `input/` (컨트롤러 소스)
  - `expected/endpoints.json`
  - `expected/needs_review.json`
  - `README.md` (케이스 의도/근거)

## JSON 산출물(현재 저장소 반영)
- `fixtures/controller_detection/endpoints.fixture.json`
  - fixture별 endpoint 기대 결과를 통합 관리한다.
- `fixtures/controller_detection/golden_snapshots.json`
  - `endpoint_id` 포함 golden snapshot을 고정해 회귀 비교 기준으로 사용한다.
- `fixtures/controller_detection/quality_gate_report.json`
  - fixture/golden 검증 결과의 품질 게이트(`quality_high`) 판정을 기록한다.
- golden 비교 시에는 `endpoint_id`, `method`, `path`, `handler`, `condition_fingerprint`, `confidence`를 최소 비교 키로 사용한다.

## 완료 기준(DoD)
- 각 case_id에 대해 expected 산출물이 고정되어 재실행 해시가 동일해야 한다.
- 규칙 변경 시 영향받는 case 목록과 snapshot diff를 함께 남긴다.
- 신규 `needs_review` 코드 추가 시 최소 1개 fixture를 반드시 동반한다.
