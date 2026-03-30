# VALIDATION_TEST_SCENARIOS.md

## 문서 목적
검증 범위를 세션/환경마다 흔들리지 않게 고정하기 위한 테스트 시나리오 목록을 정의한다.

## 범위 고정 원칙

- 시나리오는 **입력/기대결과/판정 기준**을 함께 가진다.
- 기본 제외 경로(`.git/`, `build/`, `target/`)는 모든 시나리오에 공통 적용한다.
- 모든 시나리오는 `run_context.json`의 `quality_checks`와 `execution.exit_code`를 검증 대상으로 포함한다.

## 공통 사전조건

- 샘플 저장소: `examples/repo-sample`
- 기준 브랜치: `main`
- 테스트 브랜치: `feature/test-diff`
- 출력 디렉터리: `artifacts/test-runs/<scenario-id>`
- path normalization: `docs/PATH_NORMALIZATION.md` v1.0.0 적용

## 시나리오 목록

### S01: 기본 diff 성공 (정상 경로)
- 목적: 가장 기본적인 성공 경로를 고정한다.
- 입력:
  - `lab diff --repo . --base main --head HEAD --output artifacts/test-runs/S01/changed_files.json`
- 기대 결과:
  - `exit_code=0`
  - `changed_files.json` 생성
  - `changed_files_schema_valid=pass`

### S02: 기본 제외 경로 강제 적용
- 목적: `.git/`, `build/`, `target/` 제외가 항상 적용되는지 확인한다.
- 입력:
  - 위 경로 내부 파일만 변경한 상태에서 `lab diff` 실행
- 기대 결과:
  - `summary.total_files=0`
  - `default_excludes_applied=pass`
  - `needs_review` 또는 `checks[].evidence`에 기본 제외 적용 흔적 존재

### S03: include/exclude 충돌 시 exclude 우선
- 목적: 동일 경로가 include/exclude 모두 매칭될 때 exclude 우선 규칙을 고정한다.
- 입력:
  - `--include src/** --exclude src/**`
- 기대 결과:
  - 대상 파일 0건
  - `exclude_precedence_enforced=pass`

### S04: 잘못된 ref 입력
- 목적: ref 해석 실패 시 종료코드/체크를 고정한다.
- 입력:
  - `--base does-not-exist --head HEAD`
- 기대 결과:
  - `exit_code=3`
  - `diff_ref_resolved=fail`
  - `checks[].evidence`에 실패 ref 포함

### S05: 출력 경로 쓰기 실패
- 목적: 산출물 생성 실패 계약을 고정한다.
- 입력:
  - 쓰기 불가 디렉터리를 `--output`으로 지정
- 기대 결과:
  - `exit_code=5`
  - `diff_output_writable=fail`
  - 부분 생성 파일 없음(원자적 쓰기)

### S06: changed_files 무결성 불일치
- 목적: `summary.total_files`와 `files` 길이 불일치 검출을 고정한다.
- 입력:
  - 생성 후 파일을 의도적으로 변조(테스트 훅)
- 기대 결과:
  - `exit_code=7`
  - `changed_files_integrity_valid=fail`

### S07: path normalization 적용 검증
- 목적: OS/입력 차이에도 동일 canonical path가 기록되는지 검증한다.
- 입력:
  - `./src//module/../module/a.py` 형태 포함 패턴
- 기대 결과:
  - 정규화된 경로로 기록
  - `path_normalization_applied=pass`

### S08: 재실행 결정론성
- 목적: 동일 입력 재실행 시 동일 산출물/해시를 보장한다.
- 입력:
  - S01 조건으로 2회 연속 실행
- 기대 결과:
  - `changed_files.json` 해시 동일
  - `quality_checks.summary` 동일

## 최소 검증 매트릭스

| 시나리오 | 성공/실패 | 필수 체크 | 기대 exit_code |
|---|---|---|---|
| S01 | 성공 | changed_files_schema_valid | 0 |
| S02 | 성공 | default_excludes_applied | 0 |
| S03 | 성공 | exclude_precedence_enforced | 0 |
| S04 | 실패 | diff_ref_resolved | 3 |
| S05 | 실패 | diff_output_writable | 5 |
| S06 | 실패 | changed_files_integrity_valid | 7 |
| S07 | 성공 | path_normalization_applied | 0 |
| S08 | 성공 | determinism_key_present | 0 |

## 운영 규칙

- CI 최소 게이트: S01, S02, S04, S06, S08
- 릴리즈 게이트: S01~S08 전체
- 실패 시 `status.md`의 "검증 명령"에 실행 커맨드와 결과를 즉시 기록

## 버전

- `scenario_set_version`: `1.0.0`
- 시나리오 추가/삭제 시 버전 증가 및 변경 이력 기록
