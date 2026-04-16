# CLI Command Draft

## 인터페이스 방침

LAB의 사용자 인터페이스는 **CLI 기준으로 고정**한다.
즉, 1차 범위에서는 웹 UI나 운영 서비스가 아니라, 재현 가능한 입력과 옵션을 받아 결정론적인 산출물을 생성하는 커맨드라인 도구로 설계한다.

## 설치 (프로젝트 레벨)

`lab` 명령을 셸에서 직접 사용하려면 프로젝트 루트에서 아래처럼 설치한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e . --no-build-isolation
lab --help
```

프록시/오프라인 환경에서는 `pip install -e . --no-build-isolation`을 우선 사용한다.

## 설계 원칙

- 모든 명령은 재현 가능한 입력 경로와 옵션을 받아야 한다.
- 동일 입력, 동일 옵션이면 동일 산출물과 동일 fingerprint를 만들어야 한다.
- 팩트는 정적 분석 및 DB 메타데이터로만 생성해야 한다.
- 불확실한 값은 추정하지 않고 `UNKNOWN` 또는 `needs_review`로 남겨야 한다.

## 전역 옵션 초안

- `--repo PATH`: 분석 대상 저장소 경로
- `--git-ref REF`: 분석 기준 Git ref, commit, tag
- `--db-meta PATH`: DB 메타데이터 입력 파일 경로
- `--repo-meta PATH`: 저장소 메타데이터(`repo_meta.json`) 입력 파일 경로
- `--output-dir PATH`: 산출물 출력 디렉터리
- `--include PATH_OR_GLOB`: 분석 포함 경로/패턴(복수 지정 가능)
- `--exclude PATH_OR_GLOB`: 분석 제외 경로/패턴(복수 지정 가능)
- `--format [md|json|all]`: 출력 형식 선택
- `--config PATH`: 설정 파일 경로
- `--strict`: 확인 불가능한 팩트가 있으면 실패 처리
- `--verbose`: 상세 로그 출력

## 명령어 초안

### `lab analyze`
소스 코드와 DB 메타데이터를 분석해 IR 생성을 수행한다.

예시:

```bash
lab analyze --repo . --git-ref HEAD --db-meta ./examples/db_meta.json --repo-meta ./examples/repo_meta.json --output-dir ./artifacts/run-001
```

예상 결과:
- JSON IR 생성
- `run_context.json` 생성
- `repo_meta.json` 검증/연동
- fingerprint 생성
- 분석 로그 출력

### `lab generate api`
분석 결과 또는 입력 IR을 바탕으로 `API.md`를 생성한다.

예시:

```bash
lab generate api --input ./artifacts/run-001/ir.json --output ./artifacts/run-001/API.md
```

### `lab generate spec`
변경 파일(diff)과 분석 결과를 바탕으로 `SPEC.md`를 생성한다.

예시:

```bash
lab generate spec --input ./artifacts/run-001/ir.json --output ./artifacts/run-001/SPEC.md
```

### `lab generate db-schema`
DB 메타데이터 기반으로 `db_schema.json`과 `DB_SCHEMA.md`를 생성한다.
`--input`, `--json-output`, `--output` 플래그를 함께 사용해 호출 계약을 고정한다.

예시:

```bash
lab generate db-schema \
  --input ./artifacts/run-001/db_meta.json \
  --json-output ./artifacts/run-001/db_schema.json \
  --output ./artifacts/run-001/DB_SCHEMA.md
```

### `lab diff`
두 Git 기준점 사이의 변경 파일과 영향 범위를 수집하고 `changed_files.json`을 생성한다.
실패 처리(exit code, 최소 기록 필드, 체크 이름)는 `docs/DIFF_FAILURE_CONTRACT.md`를 따른다.
필터 적용 규칙과 기본 제외 경로(`.git/`, `build/`, `target/`)는 `docs/INCLUDE_EXCLUDE_RULES.md`를 따른다.

예시:

```bash
lab diff --repo . --base main --head HEAD --output ./artifacts/run-001/changed_files.json
```

### `lab validate`
산출물의 필수 파일 존재 여부, fingerprint, quality check 결과를 검증한다.

예시:

```bash
lab validate --run-dir ./artifacts/run-001 --strict
```

## 권장 초기 사용자 흐름

1. `lab analyze`
2. `lab generate api`
3. `lab generate spec`
4. `lab generate db-schema`
5. `lab validate`

## 비범위 명시

- 웹 UI 제공
- 서버형 API 서비스 제공
- 런타임 실행 결과 수집
- LLM 기반 팩트 생성
