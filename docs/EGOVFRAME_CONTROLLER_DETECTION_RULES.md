# 전자정부프레임워크(eGovFrame) Controller 탐지 전용 룰셋

## 문서 목적
전자정부프레임워크 기반 애플리케이션에서 Controller/Endpoint 팩트를 정적 분석으로 탐지하기 위한 전용 규칙을 정의한다.

## 적용 범위
- eGovFrame 기반 Java 웹 애플리케이션
- Spring MVC Controller(`@Controller`, `@RequestMapping`) 중심 구조
- 레거시 URL 패턴(`*.do`) 및 View 반환 패턴 포함

## 핵심 원칙
- 확인 가능한 사실만 기록한다.
- 추정이 필요한 항목은 `UNKNOWN` 또는 `needs_review`로 남긴다.
- 실행 시점 환경(프로파일/운영 설정)에 의존하는 내용은 추정하지 않는다.

## 1) Controller 후보 탐지
### 클래스 레벨
다음 중 하나를 만족하면 Controller 후보로 등록한다.
- `@Controller`
- `@RestController` (혼용 프로젝트 지원)

### eGovFrame 관례 보강
- `EgovAbstractController` 계열 상속 클래스가 존재하면 보조 증거로 기록한다.
- XML/Java Config에서 수동 등록된 컨트롤러는 정적으로 연결 가능할 때만 포함한다.

## 2) Endpoint 메서드 탐지
- 기본: `@RequestMapping`이 선언된 메서드
- 혼용 대응: `@GetMapping/@PostMapping/...`도 동일 규칙으로 수용

### HTTP Method 판정
- `method` 지정 시 해당 값 확정
- `method` 미지정 시 `Method=UNKNOWN` 또는 정책상 `ALL(미지정)`로 기록
- 임의 추론(예: 메서드명으로 GET 추정) 금지

## 3) URL Path 및 `*.do` 규칙
1. 클래스+메서드 `value/path`를 결합해 최종 path를 생성한다.
2. `*.do` 패턴은 원형을 보존한다(치환/삭제 금지).
3. 다중 path 배열은 전개한다.
4. 해석 불가 시 `Path=UNKNOWN`으로 기록한다.

### Mapping 합성 규칙(상세)
- 합성 순서: `Context Path` → 클래스 레벨 `@RequestMapping` → 메서드 레벨 `@RequestMapping`.
- eGovFrame 레거시에서 경로 접두사가 properties/XML 설정으로 주입되는 경우, 코드에서 확정 불가하면 코드 기준 path만 기록하고 `needs_review`에 `external_prefix_unresolved`를 남긴다.
- 클래스/메서드 path 배열은 카티시안 곱으로 전개하고, 결과는 사전순 정렬해 결정론성을 유지한다.
- 빈 문자열/루트(`""`, `"/"`)는 중립값으로 취급하고, 결합 후 슬래시 정규화를 1회 적용한다.
- `*.do` 확장자는 보존하되, 중복 슬래시 정리 외에는 문자열 치환을 하지 않는다.
- path 변수 템플릿(`/{userId}`)은 원문 보존한다.

### Method/조건 합성 규칙
- 클래스/메서드에 method가 모두 선언되면 교집합으로 산출한다.
- 교집합이 없으면 충돌로 판단하고 endpoint 확정을 중단한 뒤 `needs_review`에 `mapping_method_conflict`를 기록한다.
- `params`, `headers`, `consumes`, `produces` 조건은 메서드 우선, 미지정 시 클래스 조건 상속으로 처리한다.
- method 미지정이 양쪽 모두인 경우에도 메서드명을 보고 GET/POST 추정하지 않는다.

### Multi-Method 처리 규칙
- 입력 소스: 클래스/메서드 `@RequestMapping(method=...)` 배열과 축약 매핑의 고정 method를 함께 수집한다.
- 축약 매핑은 1원소 method 배열로 취급하고, eGovFrame 레거시 `@RequestMapping`은 지정 배열을 그대로 전개 대상으로 사용한다.
- method 미지정 매핑은 빈 배열 대신 `UNKNOWN_METHOD` 1원소 배열로 정규화한다.
- 최종 method는 `ClassMethods × MethodMethods` 조합에서 교집합으로 계산한다.
- 한쪽만 확정 method를 가진 경우 확정값을 그대로 계승한다.
- 양쪽 모두 `UNKNOWN_METHOD`이면 `Method=UNKNOWN`으로 기록한다.
- 결과 method 배열은 고정 순서(`GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS,TRACE,UNKNOWN`)로 정렬한다.
- 같은 `METHOD + Path(+*.do)` 조합이 중복 생성되면 dedupe하고 source evidence를 병합한다.
- 교집합이 공집합이면 `needs_review.mapping_method_conflict`를 기록하고 해당 조합을 폐기한다.

#### HTTP 배열 처리 방식(명시)
- 단일 지정(`method=RequestMethod.POST`)은 1원소 HTTP 배열로 승격한다.
- 다중 지정(`method={GET,POST}`)은 enum canonical name 기준으로 정규화한다.
- 중복 원소는 정규화 후 제거하고, 최초 선언 위치를 source evidence로 남긴다.
- 빈 배열(`method={}`) 또는 해석 실패 배열은 `UNKNOWN_METHOD` 1원소 배열로 치환한다.
- 클래스/메서드 HTTP 배열은 교집합 계산 전 고정 우선순위로 정렬한다.
- 교집합 결과가 다건이면 다중 endpoint로 전개한다.
- 비표준 method 토큰은 폐기하지 않고 `UNKNOWN_METHOD_TOKEN`으로 evidence에 남긴다.

### Class + Method 조합 정의
- 조합 기본식은 `(ClassMapping × MethodMapping)`이며, 각각의 매핑 원소를 결합해 endpoint 후보를 만든다.
- ClassMapping 원소: 클래스 레벨 `@RequestMapping`에서 추출한 path/method/조건 묶음.
- MethodMapping 원소: 메서드 레벨 `@RequestMapping`(또는 축약 매핑)에서 추출한 path/method/조건 묶음.
- 후보 생성 규칙: `compose(class_mapping, method_mapping)`을 모든 조합에 적용한다.
- eGovFrame에서는 동일 조합 key가 XML/애노테이션 혼합으로 중복될 수 있으므로 key 기준 dedupe 후 source evidence를 합친다.
- Endpoint Key는 `METHOD + NormalizedPath(+ *.do 유지) + HandlerSignature + ConditionFingerprint`로 정의한다.

### endpoint_id 생성 규칙
- `endpoint_id`는 출력 정렬/비교를 위한 결정론적 ID로 생성한다.
- canonical tuple 입력값:
  - `method_norm` (`UNKNOWN` 허용)
  - `path_norm` (`*.do` 포함 원형 의미 유지)
  - `handler_norm` (`패키지.클래스#메서드(시그니처)`)
  - `condition_fingerprint` (`params/headers/consumes/produces` 정규화 결과)
- canonical source 문자열 형식:
  - `v1|{method_norm}|{path_norm}|{handler_norm}|{condition_fingerprint}`
- `endpoint_id` 계산식:
  - `endpoint_id = "ep_" + sha1_hex(canonical_source)[:16]`
- `generated_at_utc`, 소스 파일 경로/라인, XML/애노테이션 발견 순서 같은 비본질 정보는 계산에서 제외한다.
- 동일 canonical source는 실행 시점과 무관하게 동일 `endpoint_id`를 가져야 한다.
- `UNKNOWN`이 포함된 경우에도 동일 계산식으로 ID를 생성하되, `confidence=needs_review`를 동반 기록한다.
- 동일 `endpoint_id`에 상이한 canonical source가 매핑되면 `needs_review.endpoint_id_collision`을 남기고 확정을 중단한다.

#### Class/Method 조합 예시
- Class: `/usr`, Method: `/selectUserList.do` -> `/usr/selectUserList.do`
- Class: [`/cmm`, `/sys`], Method: [`/list.do`, `/detail.do`] -> 4개 후보
- Class method: `GET,POST`, Method method: `POST` -> 교집합 `POST`
- Class method: `GET`, Method method: `POST` -> 공집합(충돌), `mapping_method_conflict`

### Multi-Path 처리 규칙
- 입력 소스: 클래스/메서드 `value`, `path` 배열을 통합 수집하고 alias 중복을 제거한다.

#### 배열 처리 방식(명시)
- 단일 문자열 매핑은 길이 1 배열로 승격해 동일 로직으로 처리한다.
- `value[]`와 `path[]`가 함께 있으면 union 병합 후 중복 제거한다.
- `null`/공백/빈문자열 원소는 `""` 중립값으로 정규화한다.
- 원소 정규화 순서: trim -> 선행 슬래시 보정 -> 중복 슬래시 축약 -> 후행 슬래시 정규화(루트 제외).
- 정규화 후 dedupe하고, 원본 배열 인덱스 정보는 source evidence에 남긴다.
- 조합 전 `ClassPaths[]`, `MethodPaths[]`는 사전순 정렬로 고정한다.
- 어느 한쪽 배열이 비면 `[""]`로 대체하여 반대쪽 path를 그대로 보존한 조합을 만든다.
- 정규화 단계: path별 trim, 빈문자열 중립값 처리, 선행 슬래시 보정, 중복 슬래시 축약을 적용한다.
- 결합 단계: `ClassPaths × MethodPaths` 전개 후 `*.do` 확장자를 포함한 원문 의미를 보존한다.
- 중복 제거: 정규화된 최종 path 기준 dedupe하고 evidence를 병합한다.
- 정렬 규칙: 결과 path를 사전순 정렬하여 결정론성을 유지한다.
- 충돌 규칙: 동일 `METHOD + Path(+*.do)`에 서로 다른 handler가 매핑되면 `needs_review.mapping_route_conflict`를 기록한다.
- 폭증 제어: 조합 수가 임계치(기본 256) 초과 시 `needs_review.multi_path_expansion_overflow`를 남기고 부분 확정 출력을 금지한다.

#### Multi-Path 예시
- Class: [`/cmm`, `/sys`], Method: [`/list.do`, `/detail.do`] -> 4개 path 후보
- Class: [`""`, `/usr`], Method: [`/selectUserList.do`] -> `/selectUserList.do`, `/usr/selectUserList.do`
- Class: [`/usr//`], Method: [`//selectUser.do`] -> `/usr/selectUser.do` (확장자/의미 보존)

## 4) View Endpoint vs API Endpoint 분류
### View Endpoint
아래 패턴이면 View Endpoint 후보로 분류한다.
- 반환형 `String`이며 논리 뷰명 반환
- `ModelMap`/`Model`에 속성 주입 후 뷰 반환

### API Endpoint
아래 패턴이면 API Endpoint 후보로 분류한다.
- `@ResponseBody` 사용
- `ResponseEntity` 반환
- JSON 직렬화 객체 반환이 명시된 경우

### 분류 불가
- 정적 증거만으로 판단 불가 시 `Endpoint Type=UNKNOWN` + `needs_review`

## 5) 입력 파라미터 탐지 (eGovFrame 관례 포함)
수집 대상:
- `@RequestParam`, `@PathVariable`, `@RequestBody`
- `ModelMap`, `Model`, `HttpServletRequest`, `HttpServletResponse`, `HttpSession`
- `Map<String, Object> commandMap` 관례 파라미터
- VO(`*VO`), `EgovMap`

기록 규칙:
- `commandMap`은 구조 미확정 입력으로 표시
- VO는 선언된 필드/애노테이션 근거만 기록
- 바인딩 추론(숨은 규칙 가정) 금지

## 6) 출력/응답 탐지
### View Endpoint
- 반환 문자열을 View Name으로 기록
- Model 속성 키/타입은 정적으로 확인 가능한 범위만 기록

### API Endpoint
- 반환 타입/`ResponseEntity<T>` 기반으로 Response Schema 기록
- 상태코드 애노테이션(`@ResponseStatus`) 있으면 반영
- 타입 해석 실패 시 `Response Schema=UNKNOWN`

## 7) 예외 처리 탐지
- 메서드 내부 `throw` 및 선언 예외를 수집
- `@ExceptionHandler`, `@ControllerAdvice` 연계 가능 시 연결
- eGovFrame 공통 예외 처리(설정 기반)는 정적 연결 가능할 때만 반영
- 연결 불가 시 `needs_review`

## 8) 레거시/혼합 설정 주의사항
- 애노테이션+XML 혼합 매핑 프로젝트를 고려한다.
- XML 매핑 해석 로직이 없는 경우, 누락 가능성을 `needs_review`로 명시한다.
- 멀티 모듈에서 URL prefix가 외부 설정으로 주입되는 경우 정적 확정이 어려우면 `UNKNOWN` 처리한다.

## 9) 산출 포맷 권장
각 endpoint에 최소 아래 항목을 기록한다.
- Endpoint Type (`view` | `api` | `UNKNOWN`)
- Method
- Path
- Handler
- Input (Path/Query/Body/Model/CommandMap)
- Output (View Name 또는 Response Schema)
- Exceptions
- Source Evidence
- Confidence (`confirmed` | `needs_review`)

## 10) FAIL_FAST 기준
아래 상황에서 실패 처리 또는 경고를 남긴다.
- Java 파싱 실패로 Controller 스캔 자체가 불가능한 경우
- XML 매핑 필수 프로젝트인데 XML 파서를 비활성화한 경우
- 같은 path/method에 상충 Handler가 다수 매핑되며 해소 규칙이 없는 경우
