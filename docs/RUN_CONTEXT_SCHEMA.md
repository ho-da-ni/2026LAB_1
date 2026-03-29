# RUN_CONTEXT_SCHEMA.md Template

## 문서 목적
`run_context.json`의 구조와 필드 의미를 정의한다.

## 작성 원칙

- 값은 실행 시점에 수집 가능한 사실만 기록한다.
- 재현 가능성 검증에 필요한 최소 필드를 우선 포함한다.
- 불확실하거나 수집되지 않은 값은 `UNKNOWN` 또는 `needs_review`로 표기한다.

## 스키마 초안 (JSON)

```json
{
  "schema_version": "1.0.0",
  "run_id": "UNKNOWN",
  "created_at_utc": "UNKNOWN",
  "tool": {
    "name": "lab",
    "version": "UNKNOWN"
  },
  "workspace": {
    "root_path": "UNKNOWN",
    "os": "UNKNOWN",
    "python_version": "UNKNOWN"
  },
  "inputs": {
    "repo": {
      "vcs": "git",
      "commit": "UNKNOWN",
      "branch": "UNKNOWN",
      "dirty": "UNKNOWN",
      "diff_base": "UNKNOWN",
      "diff_target": "UNKNOWN"
    },
    "db_metadata": {
      "source_type": "UNKNOWN",
      "source_path": "UNKNOWN",
      "snapshot_id": "UNKNOWN",
      "collected_at_utc": "UNKNOWN"
    },
    "config": {
      "path": "UNKNOWN",
      "hash_sha256": "UNKNOWN",
      "profile": "UNKNOWN"
    }
  },
  "execution": {
    "command": "UNKNOWN",
    "argv": [],
    "start_time_utc": "UNKNOWN",
    "end_time_utc": "UNKNOWN",
    "duration_ms": "UNKNOWN",
    "timezone": "UTC",
    "exit_code": "UNKNOWN",
    "exit_code_policy_version": "1.0.0"
  },
  "analysis_scope": {
    "include_paths": [],
    "exclude_paths": [],
    "file_count": "UNKNOWN",
    "language_set": [],
    "module_count": "UNKNOWN"
  },
  "outputs": {
    "ir_path": "UNKNOWN",
    "api_md_path": "UNKNOWN",
    "spec_md_path": "UNKNOWN",
    "db_schema_md_path": "UNKNOWN",
    "fingerprint": "UNKNOWN",
    "artifact_dir": "UNKNOWN"
  },
  "quality_checks": {
    "checks": [],
    "summary": {
      "passed": "UNKNOWN",
      "failed": "UNKNOWN",
      "warnings": "UNKNOWN"
    },
    "rubric_version": "1.0.0"
  },
  "integrity": {
    "input_fingerprint": "UNKNOWN",
    "output_fingerprint": "UNKNOWN",
    "determinism_key": "UNKNOWN",
    "fingerprint_policy": {
      "algorithm": "sha256",
      "normalization": "stable_json_canonicalization",
      "include": [],
      "exclude": []
    }
  },
  "notes": [
    "UNKNOWN"
  ],
  "needs_review": []
}
```

## 필드 설명

### Root
- `schema_version`: run_context 스키마 버전.
- `run_id`: 실행 식별자(UUID 권장).
- `created_at_utc`: run_context 생성 시각(UTC, ISO-8601).

### tool / workspace
- `tool.name`, `tool.version`: 실행한 도구 이름/버전.
- `workspace.root_path`: 분석 루트.
- `workspace.os`, `workspace.python_version`: 실행 환경 메타데이터.

### inputs
- `inputs.repo`: Git 기준 입력 상태.
- `inputs.db_metadata`: DB 메타데이터 수집 소스 정보.
- `inputs.config`: 설정 파일 경로/해시/프로파일.

### execution
- 실행 명령, 시작/종료 시각, 소요 시간, 종료코드.
- `execution.exit_code_policy_version`: 종료코드 해석 기준 버전.

### analysis_scope
- 포함/제외 경로, 분석 파일 수, 언어 집합, 모듈 수.

### outputs
- IR/문서 산출물 경로, fingerprint, artifact 디렉터리.

### quality_checks
- 개별 체크 결과 배열(`checks`)과 집계(`summary`).
- `quality_checks.rubric_version`: quality rubric 해석 기준 버전.

### integrity
- 입력/출력 fingerprint 및 결정론성 비교 키.
- `integrity.fingerprint_policy`: fingerprint 계산 기준(알고리즘/정규화/포함/제외 규칙).

### notes / needs_review
- 실행 중 특이사항과 후속 검토 항목.

## `quality_checks.checks` 권장 원소 포맷

```json
{
  "name": "UNKNOWN",
  "status": "pass|fail|warn|UNKNOWN",
  "message": "UNKNOWN",
  "evidence": "UNKNOWN"
}
```

## quality rubric (초안 v1.0.0)

### 평가 축
- `determinism`: 동일 입력 재실행 시 동일 산출물/해시 보장 수준
- `evidence_completeness`: 문서 팩트 항목의 source evidence 충족 수준
- `schema_validity`: IR/문서/run_context가 정의 스키마를 만족하는 수준
- `traceability`: 입력(commit, snapshot, config)↔출력(api/spec/db_schema) 추적 가능성
- `integrity_consistency`: input/output fingerprint와 determinism key의 일관성

### 등급 체계
- `A` (Excellent): 필수 체크 100% pass, 경고 0, 재현성 검증 pass
- `B` (Good): 필수 체크 100% pass, 경고 허용(<=2), 재현성 검증 pass
- `C` (Acceptable): 필수 체크 100% pass, 경고 다수(>2) 또는 비핵심 체크 fail 존재
- `D` (Poor): 필수 체크 fail 1개 이상
- `F` (Critical): 무결성/재현성 핵심 체크 fail 또는 run_context 자체 스키마 불일치

### 체크 심각도
- `critical`: 실패 시 즉시 전체 실패 (`exit_code=7` 또는 `6` 상황 유발)
- `major`: 품질 게이트 실패 조건(정책에 따라 fail 처리)
- `minor`: 경고 누적 대상, 단독으로는 실패 아님
- `info`: 참고용 메트릭, 판정 미반영

### 필수 체크(권장)
- `run_context_schema_valid` (critical)
- `input_fingerprint_present` (critical)
- `output_fingerprint_present` (critical)
- `determinism_key_present` (major)
- `api_md_generated` (major)
- `spec_md_generated` (major)
- `db_schema_md_generated` (major)
- `source_evidence_minimum_coverage` (major)

### 점수 계산(권장)
- 시작 점수 100점에서 감점:
  - critical fail: 즉시 등급 `F`
  - major fail: -20점/건
  - minor fail: -5점/건
  - warning: -2점/건
- 최종 점수 밴드:
  - 95~100: `A`
  - 85~94: `B`
  - 70~84: `C`
  - 50~69: `D`
  - <50: `F`

### run_context 반영 규칙
- `quality_checks.summary`는 최소 `passed/failed/warnings`를 포함한다.
- 가능하면 `quality_checks`에 `grade`, `score`, `failed_critical_count`를 확장 필드로 기록한다.
- `rubric_version`이 바뀌면 점수/등급의 직접 비교는 금지하고 버전 기준으로만 비교한다.

## fingerprint 포함/제외 규칙 (초안)

### 포함(`include`) 원칙
- 실행 재현성에 직접 영향을 주는 입력만 포함한다.
- 권장 포함 대상:
  - Git 기준점: `inputs.repo.commit`, `inputs.repo.diff_base`, `inputs.repo.diff_target`
  - DB 메타데이터 식별자: `inputs.db_metadata.snapshot_id`
  - 설정 식별자: `inputs.config.hash_sha256`, `inputs.config.profile`
  - 분석 범위: `analysis_scope.include_paths`, `analysis_scope.exclude_paths`
  - 도구 버전: `tool.name`, `tool.version`

### 제외(`exclude`) 원칙
- 실행마다 변하거나 환경 의존적인 값은 제외한다.
- 권장 제외 대상:
  - 시각/시간값: `created_at_utc`, `execution.start_time_utc`, `execution.end_time_utc`, `execution.duration_ms`
  - 경로/환경값: `workspace.root_path`, `workspace.os`, `workspace.python_version`
  - 결과 위치값: `outputs.ir_path`, `outputs.api_md_path`, `outputs.spec_md_path`, `outputs.db_schema_md_path`, `outputs.artifact_dir`
  - 일회성 실행값: `run_id`, `execution.command`, `execution.argv`
  - 운영 메모: `notes`, `needs_review`

### 정규화 규칙
- JSON 직렬화 시 key 정렬을 고정한다.
- 리스트는 의미가 "집합"인 경우 정렬 후 해시한다(예: `language_set`, include/exclude path 목록).
- 경로 구분자와 대소문자는 OS 차이를 고려해 canonical form으로 정규화한다.
- `UNKNOWN` 값은 그대로 문자열로 유지해 해시 입력에 포함한다(누락과 구분).

### 계산 대상 권장 분리
- `integrity.input_fingerprint`: 입력/설정/분석범위 기반 해시.
- `integrity.output_fingerprint`: 산출물 내용(파일 콘텐츠 해시) 기반 해시.
- `integrity.determinism_key`: `input_fingerprint + tool.version + schema_version` 조합 기반 키.

## exit code 정책 (초안 v1.0.0)

### 목표
- CLI 자동화/CI 환경에서 실패 원인을 기계적으로 분류 가능하게 한다.
- 동일 실패 유형에 대해 항상 동일한 종료코드를 반환한다.

### 코드 체계
- `0`: 성공 (요청된 작업이 정상 완료)
- `1`: 일반 실패 (분류 불가 내부 오류, unexpected exception)
- `2`: CLI 사용 오류 (잘못된 인자, 필수 인자 누락, 잘못된 옵션 조합)
- `3`: 입력 검증 실패 (경로 없음, 지원하지 않는 입력 형식, 스키마 불일치)
- `4`: 분석 실패 (소스/메타데이터 파싱 실패, 필수 evidence 수집 실패)
- `5`: 생성 실패 (문서/IR 렌더링 실패, 출력 직렬화 실패)
- `6`: 품질 검증 실패 (`lab validate`에서 fail 기준 미충족)
- `7`: 재현성/무결성 실패 (fingerprint 불일치, determinism key 검증 실패)
- `8`: 외부 의존성 실패 (VCS/DB/파일시스템/권한/네트워크 접근 실패)
- `9`: 인터럽트/취소 (`SIGINT`, 사용자 취소, 타임아웃 정책에 의한 중단)

### 적용 규칙
- 하나의 실행에서 복수 오류가 발생하면 **가장 먼저 발생한 치명 오류 코드**를 반환한다.
- `warnings`만 존재하고 fail 조건이 없으면 종료코드는 `0`으로 유지한다.
- `lab validate`는 경고만 있을 때 `0`, fail이 1개 이상이면 `6`을 반환한다.
- `needs_review` 항목 존재만으로는 실패 처리하지 않는다(정책적으로 허용).

### run_context 기록 규칙
- `execution.exit_code`에는 실제 프로세스 종료코드를 기록한다.
- `quality_checks.summary`와 종료코드 해석이 충돌하지 않도록 함께 기록한다.
- 정책 변경 시 `execution.exit_code_policy_version`을 증가시킨다.
