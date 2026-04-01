# IR 병합(`ir_merged`) 규칙 정리

본 문서는 다음 규칙 문서를 기준으로 **IR 레벨 병합 관점**만 추려 정리한 요약본이다.

- `docs/SPRING_BOOT_CONTROLLER_DETECTION_RULES.md`
- `docs/EGOVFRAME_CONTROLLER_DETECTION_RULES.md`

---

## 1) 병합 대상/단위

- 병합 기본 단위는 Endpoint 후보이다.
- 후보 생성은 클래스 매핑 × 메서드 매핑의 Cartesian product 조합으로 본다.
- 동일 endpoint key(실질적으로 `METHOD + normalized_path` 축)로 수렴되는 항목은 1건으로 통합한다.

## 2) Path 병합 규칙

- `value`, `path`가 문자열/배열로 혼재하면 배열로 승격 후 처리한다.
- `value[]`와 `path[]`가 동시에 존재하면 union 병합 후 dedupe한다.
- 경로 정규화 후(슬래시/빈값 정리) 동일 path는 1건으로 dedupe한다.
- 최종 path 목록은 사전순 정렬을 적용해 결정론성을 유지한다.

## 3) HTTP Method 병합 규칙

- `method`가 문자열/배열 혼재 시 배열로 승격한다.
- 클래스/메서드 레벨 method 조건이 모두 존재하면 교집합을 적용한다.
- 교집합이 공집합이면 endpoint 확정 대신 `needs_review`로 분기한다.
- 최종 method 목록은 dedupe/정렬로 고정한다.

## 4) Evidence 병합 규칙

- 동일 endpoint key로 중복 생성된 후보는 source evidence를 합쳐 1건으로 통합한다.
- 통합 시 파일/심볼/annotation 근거는 잃지 않고 누적 기록한다.
- 배열 필드는 순서 안정성을 유지하도록 정렬/중복제거 후 저장한다.

## 5) 충돌/불확실성 처리

다음은 병합 완료 대신 `needs_review`를 남겨 수동 확인 대상으로 전환한다.

- 동일 `METHOD + Path`에 서로 다른 HandlerSignature가 매핑되는 경우
  - `needs_review.mapping_route_conflict`
- class/method 매핑 조합 폭증으로 안전 임계치를 넘는 경우
  - `needs_review.multi_path_expansion_overflow`
- method 교집합이 비거나 메타데이터가 상충해 endpoint 확정이 불가능한 경우
  - 규칙 문서에 정의된 충돌 코드를 유지

## 6) endpoint_id 병합 규칙

- endpoint_id는 canonical source(주요 식별 필드) 기반으로 생성한다.
- 비본질 메타데이터(표시용 설명/일시적 필드)는 ID 계산에서 제외한다.
- 동일 canonical 입력은 항상 동일 ID를 내야 하며, 충돌 시 deterministic suffix 규칙을 둔다.

## 7) `ir_merged` 출력 권장 형태

- endpoint 리스트는 `(method, path, endpoint_id)` 기준으로 안정 정렬한다.
- 중복 제거 이후에도 원본 근거 추적이 가능하도록 evidence 목록을 유지한다.
- 자동 해소 불가 항목은 반드시 `needs_review[]`에 남긴다.

---


## 8) 중복 제거(dedupe) 기준 (명시)

`ir_merged` 단계에서는 아래 키 기준으로 **중복 여부를 먼저 판정**한다.

1. Endpoint 후보 dedupe key
   - `normalized_method` (대문자 정규화, 예: `GET`)
   - `normalized_path` (슬래시/빈값 정규화 반영)
   - 필요 시 확장 키: `produces`, `consumes`, `params`, `headers` (정렬된 canonical 문자열)
2. 완전 동일 key가 2건 이상이면
   - endpoint 본문은 1건만 유지
   - `source_evidence[]`는 union 병합
   - `needs_review[]`는 코드 기준 dedupe 후 합집합
3. key는 동일하지만 handler 식별자(예: `HandlerSignature`)가 다르면
   - 자동 병합하지 않고 `needs_review.mapping_route_conflict`로 격리

## 9) 정렬(sort) 기준 (명시)

결과 재현성을 위해 정렬 우선순위를 아래처럼 고정한다.

1. Endpoint 리스트 정렬 키 (오름차순)
   1) `normalized_path`
   2) `normalized_method`
   3) `endpoint_id`
2. Endpoint 내부 배열 정렬
   - `methods[]`: ASCII 오름차순 (`DELETE`, `GET`, `PATCH`, `POST`, `PUT` ...)
   - `paths[]`: ASCII 오름차순
   - `source_evidence[]`: `(file_path, symbol, line_start, line_end)` 순 비교
   - `needs_review[]`: `(code, path, method, handler)` 순 비교
3. 비교 전 공통 정규화
   - 문자열 trim
   - method 대문자화
   - path 선행 `/` 보장 및 중복 `/` 축약
   - 없는 값은 빈 문자열 `""`로 치환해 comparator 입력 안정화

## 체크리스트 (구현/리뷰용)

- [ ] 문자열/배열 혼용 입력을 모두 배열로 승격했는가?
- [ ] `value[]` + `path[]` union/dedupe를 적용했는가?
- [ ] class/method method 조건 교집합을 계산했는가?
- [ ] endpoint key 중복 시 evidence merge + 단일화가 되었는가?
- [ ] 충돌 케이스를 임의 해소하지 않고 `needs_review`로 격리했는가?
- [ ] endpoint_id가 결정론적으로 재현되는가?
- [ ] dedupe key(`method+path` 및 확장 조건)를 코드로 고정했는가?
- [ ] endpoint/내부 배열 정렬 comparator가 문서 기준과 일치하는가?
- [ ] 결과 정렬이 고정되어 재실행 diff가 최소화되는가?

## 참고

본 문서는 “신규 규칙 정의”가 아니라 기존 Spring Boot/eGovFrame 규칙의 병합 관점 요약이다.
