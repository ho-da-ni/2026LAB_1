# Spring Boot Controller 탐지 전용 룰셋

## 문서 목적
Spring Boot(Annotation 기반 Spring MVC) 코드에서 API Endpoint 팩트를 정적 분석으로 탐지하기 위한 전용 규칙을 정의한다.

## 적용 범위
- Java/Kotlin 기반 Spring Boot 애플리케이션
- `@RestController`/`@Controller` + Mapping 애노테이션 기반 라우팅
- 정적 분석으로 확인 가능한 정보만 산출

## 핵심 원칙
- 추정 금지: 코드/메타데이터로 확인된 사실만 기록한다.
- 불확실성 격리: 확인 불가 값은 `UNKNOWN` 또는 `needs_review`로 기록한다.
- 재현 가능성: 동일 입력에서 동일 출력이 나오도록 결정론적으로 처리한다.

## 1) Controller 후보 탐지
### 클래스 레벨
다음 중 하나를 만족하면 Controller 후보로 등록한다.
- `@RestController`
- `@Controller`

### 제외
- 테스트 소스(`src/test/**`)
- generated 코드, 외부 라이브러리 바이너리

## 2) Endpoint 메서드 탐지
메서드에 아래 애노테이션이 있으면 endpoint 후보로 등록한다.
- `@RequestMapping`
- `@GetMapping`
- `@PostMapping`
- `@PutMapping`
- `@DeleteMapping`
- `@PatchMapping`

### 우선순위
- 축약 매핑(`@GetMapping` 등)이 있으면 해당 HTTP Method를 확정값으로 사용한다.
- `@RequestMapping(method=...)`은 지정된 method 배열을 전개한다.
- method 미지정 시 `Method=UNKNOWN`으로 기록한다(추정 금지).

## 3) Path 결정
1. 클래스 레벨 path(`@RequestMapping`)와 메서드 레벨 path를 결합한다.
2. 슬래시 중복/누락을 정규화한다(예: `/api` + `/users` → `/api/users`).
3. 클래스/메서드 양쪽에 path 배열이 있으면 카티시안 곱으로 전개한다.
4. path 값을 해석할 수 없으면 `Path=UNKNOWN`으로 기록한다.

### Mapping 합성 규칙(상세)
- 합성 순서: `Servlet Context Path` → (선택) `Class-level @RequestMapping` → `Method-level Mapping`.
- prefix가 외부 설정(`server.servlet.context-path`, 프록시 rewrite 등)으로만 주어져 코드에서 확정 불가하면 endpoint path는 코드 기준으로 기록하고 `needs_review`를 추가한다.
- 클래스 레벨에 `path`와 `value`가 동시에 선언된 경우, Spring 별칭 규칙을 따라 동일 의미로 취급하고 중복 제거 후 합성한다.
- 메서드 레벨에서 절대 경로처럼 보여도(예: `"/v1/users"`) 클래스 레벨 prefix를 무시하지 않는다. 항상 클래스+메서드 결합을 기본값으로 한다.
- 빈 문자열/루트(`""`, `"/"`)는 결합 시 중립값으로 처리한다.
- 경로 변수(`/{id}`)는 원문 보존을 기본으로 하며 이름 치환/정규식 해석 추론은 하지 않는다.
- path 후보가 여러 개인 경우 정렬 기준(사전순)을 고정해 출력 순서를 결정론적으로 유지한다.

### HTTP Method/조건 합성 규칙
- 클래스 레벨 `@RequestMapping(method=...)`와 메서드 레벨 method가 모두 있으면 교집합으로 계산한다.
- 교집합이 공집합이면 유효 endpoint로 확정하지 않고 `needs_review`에 `mapping_method_conflict`를 남긴다.
- `params`, `headers`, `consumes`, `produces` 조건은 메서드 우선, 없으면 클래스 레벨 상속으로 합성한다.
- `name` 속성은 라우팅 식별 근거로만 보조 기록하고 endpoint key 생성에는 사용하지 않는다.

### Multi-Method 처리 규칙
- 입력 소스: 클래스/메서드의 `RequestMethod[]`(또는 축약 매핑의 고정 method)를 모두 수집한다.
- 축약 매핑(`@GetMapping`, `@PostMapping` 등)은 길이 1 method 배열로 취급한다.
- method 미지정 `@RequestMapping`은 빈 배열이 아니라 `UNKNOWN_METHOD` 1원소 배열로 정규화한다.
- 최종 method 후보는 `ClassMethods × MethodMethods` 조합에서 교집합으로 산출한다.
- 클래스/메서드 중 한쪽만 method가 확정된 경우, 확정된 쪽 값을 그대로 사용한다.
- 양쪽 모두 `UNKNOWN_METHOD`인 경우 endpoint method는 `UNKNOWN`으로 확정한다(추정 금지).
- 산출 method 목록은 `GET < POST < PUT < PATCH < DELETE < HEAD < OPTIONS < TRACE < UNKNOWN` 고정 순서로 정렬한다.
- 동일 `Path + Method` 결과가 중복 생성되면 source evidence를 병합하고 1건으로 dedupe한다.
- 교집합 공집합 충돌은 `needs_review.mapping_method_conflict`로 기록하고 endpoint 확정을 중단한다.

#### HTTP 배열 처리 방식(명시)
- `method=RequestMethod.GET` 같은 단일 지정은 길이 1 HTTP 배열로 승격한다.
- `method={GET, POST}` 같은 다중 지정은 선언 순서를 버리고 enum canonical name 기준으로 정규화한다.
- 배열 원소는 대문자 표준값(`GET`, `POST` 등)으로 정규화하고 비표준 토큰은 `UNKNOWN_METHOD_TOKEN`으로 기록한다.
- 중복 method(`{GET, GET}`)는 정규화 후 dedupe하며 최초 선언 인덱스를 evidence로 보존한다.
- 빈 HTTP 배열(`method={}`)은 명시적 미지정으로 간주해 `UNKNOWN_METHOD` 1원소 배열로 치환한다.
- 클래스/메서드 각 HTTP 배열은 교집합 계산 전에 사전순이 아니라 고정 우선순위(`GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS,TRACE`)로 정렬한다.
- 교집합 결과가 다건이면 해당 배열을 그대로 endpoint 전개에 사용하고, 각 원소별로 endpoint key를 생성한다.

### Class + Method 조합 정의
- 조합 단위는 `(ClassMapping × MethodMapping)`의 데카르트 곱이다.
- ClassMapping은 클래스 레벨 `@RequestMapping`의 각 path/method/조건 조합 원소를 의미한다.
- MethodMapping은 메서드 레벨 매핑(`@RequestMapping` 또는 축약 매핑)의 각 path/method/조건 조합 원소를 의미한다.
- Endpoint 후보는 `for c in ClassMapping: for m in MethodMapping: compose(c, m)` 규칙으로 생성한다.
- 최종 Endpoint Key는 `METHOD + NormalizedPath + HandlerSignature + ConditionFingerprint`로 정의한다.
- 동일 Endpoint Key가 중복 생성되면 source evidence를 병합하고 1건으로 dedupe한다.

### endpoint_id 생성 규칙
- `endpoint_id`는 사람이 읽을 수 있는 stable key가 아니라, 결정론적 식별자 문자열로 생성한다.
- 원본 재료는 아래 canonical tuple을 사용한다.
  - `method_norm` (`UNKNOWN` 허용)
  - `path_norm`
  - `handler_norm` (`패키지.클래스#메서드(시그니처)`)
  - `condition_fingerprint` (`params/headers/consumes/produces` 정규화 결과)
- canonical source 문자열 형식:
  - `v1|{method_norm}|{path_norm}|{handler_norm}|{condition_fingerprint}`
- `endpoint_id` 계산식:
  - `endpoint_id = "ep_" + sha1_hex(canonical_source)[:16]`
- 같은 canonical source면 실행/환경이 달라도 동일 `endpoint_id`를 보장해야 한다.
- `generated_at_utc`, 파일 경로, 라인번호, 배열 원본 순서 같은 비본질 메타데이터는 `endpoint_id` 입력에서 제외한다.
- 경로/메서드가 `UNKNOWN`이어도 placeholder를 포함해 ID를 생성하고, 별도로 `confidence=needs_review`를 기록한다.
- hash 충돌(동일 `endpoint_id`에 서로 다른 canonical source)이 감지되면 분석을 중단하고 `needs_review.endpoint_id_collision`을 기록한다.

#### Class/Method 조합 예시
- Class: `/api`, Method: `/users` -> `/api/users`
- Class: [`/api`, `/admin`], Method: [`/users`, `/{id}`] -> 4개 endpoint 후보 생성
- Class method: `GET,POST`, Method method: `POST` -> 교집합 `POST`
- Class method: `GET`, Method method: `POST` -> 공집합(충돌), `mapping_method_conflict`

### Multi-Path 처리 규칙
- 입력 소스: `value`, `path` 속성의 문자열/배열 값을 모두 수집하고, alias 중복을 제거한다.

#### 배열 처리 방식(명시)
- 단일 문자열은 길이 1 배열로 승격해 동일 파이프라인으로 처리한다.
- `value[]`, `path[]`가 동시에 존재하면 두 배열을 합집합(union)으로 병합한다(중복 문자열 제거).
- 배열 원소가 `null`/공백/빈문자열이면 `""`(루트 중립값)로 정규화한다.
- 배열 원소 정규화 순서: trim -> 선행 슬래시 보정 -> 중복 슬래시 축약 -> 후행 슬래시 정규화(루트 제외).
- 배열 dedupe는 정규화 이후 수행하며, 최초 등장 인덱스를 evidence로 보존한다.
- 최종 전개 전 `ClassPaths[]`, `MethodPaths[]`는 사전순 정렬하여 조합 순서를 고정한다.
- 빈 배열이면 암묵적으로 `[""]` 1개로 간주해 반대쪽 배열과 조합 가능하게 한다.
- 정규화 단계: 각 path 토큰에 대해 trim -> 빈값 처리(`""`는 루트 중립값) -> 선행 슬래시 보정 -> 중복 슬래시 축약 순으로 처리한다.
- 결합 단계: `ClassPaths × MethodPaths` 데카르트 곱으로 합성하되, 루트 중립값은 결합 시 생략 가능한 prefix/suffix로 처리한다.
- 중복 제거: 정규화 후 동일 문자열 path는 1건으로 dedupe하고 source evidence 목록만 병합한다.
- 정렬 규칙: 최종 path 목록은 사전순(ASCII) 정렬로 출력해 실행마다 동일 순서를 보장한다.
- 충돌 규칙: 동일 `METHOD + Path`에 서로 다른 HandlerSignature가 매핑되면 endpoint 확정을 중단하고 `needs_review.mapping_route_conflict`를 남긴다.
- 제한 규칙: path 개수 폭증 방지를 위해 `len(ClassPaths) * len(MethodPaths)`가 임계치(기본 256)를 초과하면 `needs_review.multi_path_expansion_overflow`를 기록한다.

#### Multi-Path 예시
- Class: [`/api`, `/admin`], Method: [`/users`, `/users/{id}`] -> 4개 path 생성 후 정렬
- Class: [`""`, `/api`], Method: [`/health`] -> `/health`, `/api/health`
- Class: [`/api//`], Method: [`//users`] -> 정규화 결과 `/api/users`

## 4) Handler 식별자
- 기본 형식: `패키지.클래스명#메서드명`
- 오버로드 메서드는 파라미터 타입 시그니처를 함께 기록한다.
- 프록시/바이트코드 생성 클래스 이름은 원본 소스 기준 이름으로 정규화한다.

## 5) 입력(Request) 탐지
메서드 파라미터를 기준으로 다음을 수집한다.
- `@RequestBody`: Request Body 스키마 후보
- `@PathVariable`: Path 파라미터
- `@RequestParam`: Query/Form 파라미터
- `@RequestHeader`, `@CookieValue`: Header/Cookie 파라미터
- `@ModelAttribute`: 바인딩 객체

### 보조 메타데이터
- Bean Validation(`@Valid`, `@NotNull` 등)은 정적으로 확인 가능한 범위만 기록
- Jackson(`@JsonProperty`) 등 직렬화 메타데이터는 확인 가능할 때만 반영
- 제네릭/복합 타입 해석 실패 시 `UNKNOWN + needs_review`

## 6) 출력(Response) 탐지
- `ResponseEntity<T>`는 `T`를 응답 스키마 후보로 기록
- 메서드 반환 타입(`T`)을 응답 스키마 후보로 기록
- `@ResponseStatus`가 있으면 status 코드 기록
- `void`/`Mono<Void>`/`Flux<Void>`는 본문 없음으로 기록
- 타입 추적 불가 시 `Response Schema=UNKNOWN`

## 7) 예외(Exception) 탐지
- 메서드/클래스 내부에서 정적으로 확인 가능한 `throw` 예외를 기록
- `@ExceptionHandler`, `@ControllerAdvice` 매핑을 연결할 수 있으면 연결
- 전역 예외 매핑 연결 불가 시 `needs_review`로 격리

## 8) Media Type/부가 속성
- `consumes`, `produces`는 메서드 우선, 없으면 클래스 레벨 상속
- CORS, 인증 애노테이션 등은 존재 사실만 기록하고 의미 추론은 하지 않는다

## 9) 산출 포맷 권장
각 endpoint에 최소 아래 항목을 기록한다.
- Method
- Path
- Handler
- Request Schema
- Response Schema
- Exceptions
- Source Evidence
- Confidence (`confirmed` | `needs_review`)

## 10) FAIL_FAST 기준
아래 상황에서 분석 단계를 실패 처리하거나 경고를 반드시 남긴다.
- 소스 인코딩/파싱 실패로 Controller 탐지가 불가능한 경우
- 동일 Handler에 상충되는 Method/Path가 다수 존재하는데 해소 규칙이 없는 경우
- 증거(source evidence) 경로를 남길 수 없는 경우
