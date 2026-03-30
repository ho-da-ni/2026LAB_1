# REPO_META_SCHEMA.md

## 문서 목적
`repo_meta.json`의 구조와 필드 의미를 정의한다.

## 작성 원칙

- 값은 저장소에서 재현 가능하게 수집 가능한 사실만 기록한다.
- 추정 정보는 쓰지 않고 `UNKNOWN` 또는 `needs_review`로 분리한다.
- `run_context.json`의 `inputs.repo`를 보강할 수 있는 최소 필드부터 시작한다.
- 경로 필드(`ownership.codeowners_path`)는 `docs/PATH_NORMALIZATION.md` 규칙을 따른다.

## 스키마 초안 (JSON)

```json
{
  "schema_version": "1.0.0",
  "repo_id": "UNKNOWN",
  "collected_at_utc": "UNKNOWN",
  "vcs": "git",
  "default_branch": "UNKNOWN",
  "remotes": [
    {
      "name": "origin",
      "url": "UNKNOWN",
      "fetch": "UNKNOWN",
      "push": "UNKNOWN"
    }
  ],
  "head": {
    "commit": "UNKNOWN",
    "branch": "UNKNOWN",
    "tag": "UNKNOWN",
    "dirty": "UNKNOWN"
  },
  "history_window": {
    "base_commit": "UNKNOWN",
    "target_commit": "UNKNOWN",
    "commit_count": "UNKNOWN"
  },
  "code_stats": {
    "file_count": "UNKNOWN",
    "language_bytes": {},
    "language_files": {}
  },
  "ownership": {
    "codeowners_path": "UNKNOWN",
    "teams": []
  },
  "constraints": {
    "license": "UNKNOWN",
    "runtime_versions": {
      "python": "UNKNOWN",
      "node": "UNKNOWN"
    }
  },
  "integrity": {
    "fingerprint": "UNKNOWN",
    "fingerprint_policy_version": "1.0.0"
  },
  "needs_review": []
}
```

## 필드 설명

### Root
- `schema_version`: `repo_meta.json` 스키마 버전.
- `repo_id`: 저장소 고유 식별자(예: `owner/name` 또는 내부 ID).
- `collected_at_utc`: 메타데이터 수집 시각(UTC, ISO-8601).
- `vcs`: 버전 관리 시스템 타입(현재 `git` 고정).

### remotes / head
- `remotes[]`: 원격 저장소 이름/URL/fetch/push URL.
- `head`: 수집 시점의 HEAD 상태.
  - `commit`: HEAD commit SHA
  - `branch`: 현재 브랜치명
  - `tag`: 태그 checkout이면 태그명
  - `dirty`: 워킹트리 변경 여부

### history_window
- 분석 기준 범위(예: diff 구간) 정의.
- `base_commit`, `target_commit`은 `run_context.inputs.repo.diff_base/diff_target`와 매핑 가능해야 한다.

### code_stats
- 저장소 스냅샷 기준 코드 통계.
- `language_bytes`: 언어별 바이트 수.
- `language_files`: 언어별 파일 수.

### ownership / constraints
- `ownership.codeowners_path`: CODEOWNERS 파일 경로.
- `ownership.teams`: 코드 소유 팀 목록.
- `constraints.license`: 프로젝트 라이선스.
- `constraints.runtime_versions`: 실행환경 버전 제약.

### integrity
- `fingerprint`: `repo_meta` 본문의 안정 정규화 해시.
- `fingerprint_policy_version`: 해시 계산 정책 버전.

## run_context 연동 가이드

`run_context.json`과 함께 사용할 때는 아래 우선순위를 따른다.

1. 실행 고정값은 `run_context.inputs.repo`를 우선한다.
2. 저장소 전역 컨텍스트(원격, 소유권, 언어 통계)는 `repo_meta`를 우선한다.
3. 충돌 시 `needs_review`에 경로 단위로 기록한다.

예시:

```json
{
  "path": "inputs.repo.branch",
  "run_context": "feature/add-validate",
  "repo_meta": "main",
  "reason": "detached_head_or_stale_meta"
}
```
