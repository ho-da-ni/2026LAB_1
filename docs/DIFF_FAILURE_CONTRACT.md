# DIFF_FAILURE_CONTRACT.md

## 문서 목적
`lab diff` 실행 시 실패를 일관되게 보고/기록하기 위한 계약(Contract)을 정의한다.

## 적용 범위

- 명령: `lab diff`
- 입력: `--repo`, `--base`, `--head`, 필터 옵션(include/exclude)
- 출력: `changed_files.json`, `run_context.json.execution`, `run_context.json.quality_checks`

## 실패 분류 (v1.0.0)

### 1) 입력 오류 (`exit_code=2`)
- `--repo` 경로 누락 또는 디렉터리 아님
- `--base`/`--head` 파라미터 누락
- 지원하지 않는 옵션 조합

기록 규칙:
- `execution.exit_code=2`
- `quality_checks.checks[]`에 `diff_input_valid`를 `fail`로 기록

### 2) Git 참조 오류 (`exit_code=3`)
- `base` 또는 `head` ref 해석 실패
- `merge-base` 계산 실패 (공통 조상 없음 포함)

기록 규칙:
- 실패한 ref 이름을 `checks[].evidence`에 남긴다.
- `needs_review`에 ref 충돌 원인(오타/삭제 브랜치/권한)을 기록한다.

### 3) 산출물 생성 오류 (`exit_code=5`)
- `changed_files.json` 직렬화 실패
- 출력 디렉터리 생성/쓰기 실패

기록 규칙:
- `outputs.changed_files_path`는 요청값을 유지하고, 실제 파일 부재를 `checks[].message`에 기록한다.
- 부분 생성 파일은 원자적 쓰기 규칙에 따라 제거한다.

### 4) 무결성/재현성 오류 (`exit_code=7`)
- `summary.total_files != len(files)`
- fingerprint 생성 실패 또는 정책 불일치
- path normalization 버전 미스매치

기록 규칙:
- `quality_checks.summary.failed` 증가
- `integrity` 관련 체크 이름을 명시(`changed_files_integrity_valid` 등)

### 5) 외부 의존성 오류 (`exit_code=8`)
- Git 실행 바이너리 접근 불가
- 파일시스템 권한/락 문제

기록 규칙:
- 운영환경 이슈는 `checks[].status=warn|fail` 정책에 따라 분리하되,
  `exit_code`는 8로 고정한다.

## 우선순위 규칙

복수 실패가 동시 발생하면 아래 우선순위의 **가장 높은 심각도 코드**를 반환한다.

1. `8` 외부 의존성
2. `7` 무결성/재현성
3. `5` 산출물 생성
4. `3` Git 참조
5. `2` 입력 오류

## changed_files.json 계약

실패 시에도 가능한 경우 아래 최소 구조를 유지한다.

```json
{
  "schema_version": "1.0.0",
  "repo": {
    "base": "UNKNOWN",
    "head": "UNKNOWN"
  },
  "summary": {
    "total_files": 0
  },
  "files": [],
  "needs_review": ["diff_failed"]
}
```

완전 생성 불가 시에는 파일을 만들지 않고 `run_context`만 남긴다.

## run_context 기록 계약

- `execution.command`: 실제 실행 커맨드
- `execution.exit_code`: 위 계약 코드
- `quality_checks.checks[]`: 최소 1개 이상 실패/경고 체크
- `notes`: 운영자 액션 힌트(예: "verify git refs and rerun")

## 권장 체크 이름

- `diff_input_valid`
- `diff_ref_resolved`
- `diff_output_writable`
- `changed_files_schema_valid`
- `changed_files_integrity_valid`
- `path_normalization_applied`

## 버전 정책

- 계약 변경 시 `contract_version`을 `1.0.1` 등으로 증가한다.
- `RUN_CONTEXT_SCHEMA.md`의 `execution.exit_code_policy_version`과 함께 관리한다.
