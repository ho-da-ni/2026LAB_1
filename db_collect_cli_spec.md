# DB 수집용 CLI 인자 규격 (W6-DB-01)

## 1) 목적
명령어 기반 DB 메타데이터 수집 시작점을 고정하기 위해, W6 범위에서 사용할 CLI 인자 계약(Contract)을 정의한다.

역할 분리 원칙:
- `lab collect db`: 수집 단계(접속 인자 검증 + 수집 JSON 생성)
- `lab generate db-schema`: 렌더링 단계(`db_collection.json` -> `db_schema.json`/`DB_SCHEMA.md`)

---

## 2) 명령 형태

```bash
lab collect db [OPTIONS]
```

---

## 3) 인자 규격

| 인자 | 타입 | 필수 여부 | 기본값 | 설명 |
|---|---|---|---|---|
| `--host` | string | 필수 | 없음 | DB 서버 호스트명 또는 IP |
| `--port` | int | 선택 | `1521` | DB 리스너 포트 |
| `--service-name` | string | 조건부 필수 | 없음 | Oracle 서비스명. `--sid`와 상호배타 |
| `--sid` | string | 조건부 필수 | 없음 | Oracle SID. `--service-name`와 상호배타 |
| `--username` | string | 필수 | 없음 | DB 로그인 사용자 |
| `--password` | string | 선택* | 없음 | 비밀번호 직접 입력(평문 전달). 보안상 비권장 |
| `--password-stdin` | flag | 선택* | `false` | stdin으로 비밀번호 입력 |
| `--password-env` | string | 선택* | 없음 | 지정한 환경변수에서 비밀번호 읽기 (예: `DB_PASSWORD`) |
| `--owner` | string (반복 가능) | 선택 | 없음 | owner/schema 필터(복수 지정 가능) |
| `--output-dir` | path | 필수 | 없음 | 수집 산출물 저장 디렉터리 |
| `--timeout` | int(초) | 선택 | `30` | DB 연결/조회 타임아웃(초), 1 이상 |
| `--include-comments` | flag | 선택 | `false` | 컬럼/테이블 코멘트 수집 여부 |
| `--format` | enum | 선택 | `json` | 출력 포맷. W6에서는 `json`만 허용 |

> `*` 비밀번호 입력 옵션(`--password`, `--password-stdin`, `--password-env`) 중 **정확히 1개 필수**.

---

## 4) 필수/선택 인자 정리

### 필수
- `--host`
- `--username`
- `--output-dir`
- 접속 식별자 1개: `--service-name` **또는** `--sid`
- 비밀번호 입력 방식 1개: `--password` **또는** `--password-stdin` **또는** `--password-env`

### 선택
- `--port` (기본 `1521`)
- `--owner` (0개 이상)
- `--timeout` (기본 `30`)
- `--include-comments` (기본 `false`)
- `--format` (기본/허용 `json`)

---

## 5) 잘못된 조합 처리 규칙

1. `--service-name`와 `--sid`를 동시에 지정하면 실패.
2. `--service-name`, `--sid`를 모두 생략하면 실패.
3. 비밀번호 옵션 3종(`--password`, `--password-stdin`, `--password-env`)을 2개 이상 지정하면 실패.
4. 비밀번호 옵션 3종을 모두 생략하면 실패.
5. `--format`이 `json`이 아니면 실패 (W6 범위 제한).
6. `--timeout < 1`이면 실패.
7. `--port`가 1~65535 범위를 벗어나면 실패.
8. `--owner`가 빈 문자열이면 실패.

권장 오류 코드:
- 인자 검증 실패: `exit 2`
- 연결/실행 실패: `exit 1`

오류 메시지 규칙:
- 어떤 인자가 충돌/누락인지 명시한다.
- 수정 방법(예: "`--service-name` 또는 `--sid` 중 하나만 지정")을 함께 제시한다.

---

## 6) 명령 예시

### 예시 A: service_name + 환경변수 비밀번호

```bash
export DB_PASSWORD='***'
lab collect db \
  --host 10.10.20.15 \
  --port 1521 \
  --service-name ORCLPDB1 \
  --username app_reader \
  --password-env DB_PASSWORD \
  --owner APP --owner COMMON \
  --output-dir ./artifacts/db/run-001 \
  --timeout 60 \
  --include-comments \
  --format json
```

### 예시 B: sid + stdin 비밀번호

```bash
printf '%s' '***' | lab collect db \
  --host db.internal.local \
  --sid ORCL \
  --username system \
  --password-stdin \
  --output-dir ./artifacts/db/run-002 \
  --format json
```

---

## 7) 검증 시나리오 (DoD)

### 7.1 정상 인자 조합 테스트
- 조건: 필수 인자 모두 충족, 상호배타 규칙 위반 없음.
- 기대: 인자 검증 통과 후 수집 로직 시작.

### 7.2 필수 인자 누락 테스트
- 케이스: `--host` 누락, 또는 `--username` 누락, 또는 `--output-dir` 누락.
- 기대: 즉시 실패(`exit 2`) + 누락 인자명 출력.

### 7.3 service_name / sid 충돌 테스트
- 케이스: `--service-name`와 `--sid` 동시 지정.
- 기대: 즉시 실패(`exit 2`) + 충돌 안내 메시지 출력.

### 7.4 비밀번호 미입력 처리 테스트
- 케이스: `--password`, `--password-stdin`, `--password-env` 모두 미지정.
- 기대: 즉시 실패(`exit 2`) + 비밀번호 입력 방식 1개 필수 안내.
