# 접속 정보 전달/마스킹 정책 (W6-DB-02)

## 1) 목적
DB 수집 CLI 실행 시 접속 정보 전달 방식과 민감정보 처리 경계를 고정하여, 실행 안정성과 보안 요구를 동시에 만족한다.

---

## 2) 범위
- 대상 명령: `lab collect db`
- 대상 정보: `host`, `port`, `service_name/sid`, `username`, `password` 및 실행/오류 로그, `run_context`

---

## 3) 접속 정보 전달 정책

### 3.1 CLI 직접 입력 허용 범위
- **허용(직접 입력 가능)**
  - `--host`
  - `--port`
  - `--service-name` 또는 `--sid`
  - `--username`
  - `--owner`
  - `--timeout`
  - `--include-comments`
  - `--output-dir`
  - `--format`(W6: `json`)
- **제한(직접 입력 비권장/예외 허용)**
  - `--password <value>`는 디버깅/로컬 단발성 실행에 한해 허용하되, 운영/CI에서는 금지 권고.

### 3.2 환경변수 사용 여부
- 기본 권장 방식: `--password-env <ENV_NAME>`
- CI/CD, 배치, 자동화 환경에서는 **환경변수 방식 사용을 원칙**으로 한다.
- `ENV_NAME` 자체는 로그/`run_context`에 남길 수 있으나, 환경변수 **값(실제 비밀번호)은 절대 기록하지 않는다**.
- 대안으로 `--password-stdin` 허용(사용자 인터랙티브/파이프 입력).

### 3.3 비밀번호 입력 채널 우선순위(권장)
1. `--password-env`
2. `--password-stdin`
3. `--password` (최후 수단)

---

## 4) 로그 마스킹 정책

### 4.1 금지 규칙
- 로그(콘솔/stdout/stderr/파일 로그)에 아래 항목을 평문 출력하면 안 된다.
  - 실제 비밀번호 문자열
  - DB 연결 문자열 내 인증정보(`user/password@...` 형태의 password 부분)
  - 인증 토큰/시크릿 키 등 추가 민감정보

### 4.2 허용 규칙
- 접속 시도 사실, 호스트/포트, DB 식별자(service_name/sid), 타임아웃, 재시도 횟수 등은 출력 가능.
- 비밀번호 관련 로그는 아래처럼 마스킹된 형태만 허용.
  - `password=***`
  - `password_source=env(DB_PASSWORD)`

### 4.3 마스킹 표준
- 민감값 전체를 `***`로 치환(부분 노출 금지).
- 길이/해시/접두어·접미어 노출 금지.

---

## 5) run_context 기록 정책

### 5.1 run_context에 **남길 정보**
- `host`
- `port`
- `service_name` 또는 `sid` 중 사용된 식별자 이름/값
- `username` (선택: 조직 정책상 마스킹 필요 시 `u***` 규칙 적용 가능)
- `owner`/`schema` 필터
- `output_dir`
- `timeout`
- `include_comments`
- `format`
- `password_input_mode` (`env` | `stdin` | `cli`)
- `password_env_name` (mode가 `env`일 때만)

### 5.2 run_context에 **남기지 않을 정보**
- 실제 비밀번호 값
- stdin으로 입력된 원문
- 환경변수 조회 결과(비밀번호 값)
- 완전한 DSN/connection string 원문(인증정보 포함 가능성이 있으면 금지)

---

## 6) 접속 실패 시 에러 메시지 규칙

### 6.1 원칙
- 사용자 행동 가능한 원인/해결책을 제시한다.
- 민감정보(비밀번호, 시크릿, 인증원문)는 포함하지 않는다.
- 에러 메시지에 포함 가능한 정보는 host/port/service_name|sid/username 수준으로 제한한다.

### 6.2 실패 메시지 템플릿

#### 템플릿 A: 인증 실패
`[DB_CONN_AUTH_FAILED] Authentication failed for user '{username}' at {host}:{port} ({db_id_type}={db_id}). Verify credentials input mode and secret value.`

#### 템플릿 B: 네트워크/타임아웃 실패
`[DB_CONN_TIMEOUT] Connection timed out after {timeout}s to {host}:{port} ({db_id_type}={db_id}). Check network, listener status, and timeout setting.`

#### 템플릿 C: 식별자/서비스 불일치
`[DB_CONN_TARGET_INVALID] Target database identifier is not reachable: {db_id_type}={db_id} at {host}:{port}. Verify service_name/sid and listener registration.`

#### 템플릿 D: 환경변수 누락
`[DB_CONN_SECRET_MISSING] Password environment variable '{env_name}' is not set. Provide --password-env with a valid variable or use --password-stdin.`

---

## 7) DoD
- 비밀번호/민감정보 로그 노출 금지 규칙이 명시되어 있다.
- `run_context` 기록 범위(남길/남기지 않을 정보)가 정의되어 있다.
- 접속 실패 메시지 템플릿이 정의되어 있다.

---

## 8) 검증 항목

### 8.1 실행 로그 비밀번호 미노출 검증
- 방법: 샘플 실행 후 로그에서 실제 비밀번호 문자열 및 `password=` 원문 노출 여부 검색.
- 기대: 실제 비밀번호 문자열 미검출, `password=***` 같은 마스킹 문자열만 존재.

### 8.2 에러 출력 민감정보 비혼입 검증
- 방법: 인증 실패를 유도한 뒤 stderr/로그를 검사.
- 기대: 에러 메시지에 비밀번호/시크릿/원문 DSN 미포함, 템플릿 규칙 준수.
