# CHANGED_FILES_SCHEMA.md

## 문서 목적
`changed_files.json`의 구조와 필드 의미를 정의한다.

## 작성 원칙

- 변경 사실은 Git diff에서 직접 추출 가능한 값만 기록한다.
- 파일 영향도는 추정하지 않고 관측 가능한 정보만 담는다.
- 불확실한 항목은 `UNKNOWN` 또는 `needs_review`로 분리한다.
- 경로 필드(`files[].path`, `files[].old_path`)는 `docs/PATH_NORMALIZATION.md` 규칙을 따른다.

## 스키마 초안 (JSON)

```json
{
  "schema_version": "1.0.0",
  "generated_at_utc": "UNKNOWN",
  "repo": {
    "vcs": "git",
    "base": "UNKNOWN",
    "head": "UNKNOWN",
    "merge_base": "UNKNOWN"
  },
  "summary": {
    "total_files": "UNKNOWN",
    "added": "UNKNOWN",
    "modified": "UNKNOWN",
    "deleted": "UNKNOWN",
    "renamed": "UNKNOWN"
  },
  "files": [
    {
      "path": "UNKNOWN",
      "old_path": "UNKNOWN",
      "status": "A|M|D|R|C|T|UNKNOWN",
      "language": "UNKNOWN",
      "hunks": "UNKNOWN",
      "lines_added": "UNKNOWN",
      "lines_deleted": "UNKNOWN",
      "is_binary": "UNKNOWN",
      "evidence": {
        "diff_header": "UNKNOWN",
        "blob_before": "UNKNOWN",
        "blob_after": "UNKNOWN"
      }
    }
  ],
  "filters": {
    "include_paths": [],
    "exclude_paths": []
  },
  "integrity": {
    "fingerprint": "UNKNOWN",
    "fingerprint_policy_version": "1.0.0"
  },
  "needs_review": []
}
```

## 필드 설명

### repo
- `base`: diff 시작 기준 커밋/브랜치/tag.
- `head`: diff 종료 기준 커밋/브랜치/tag.
- `merge_base`: `base...head` 계산 시 사용한 merge-base.

### summary
- 전체 변경 파일 수와 상태별 집계.
- `summary.total_files`는 `files` 길이와 일치해야 한다.
- 기본 제외 경로(`.git/`, `build/`, `target/`)는 집계에서 제외한다.

### files[]
- `path`: 변경 후 기준 파일 경로.
- `old_path`: rename/move인 경우 변경 전 경로.
- `status`: Git status 코드(`A/M/D/R/C/T`).
- `hunks`: unified diff hunk 개수.
- `lines_added`, `lines_deleted`: 텍스트 diff 줄 단위 통계.
- `is_binary`: 바이너리 diff 여부.
- `evidence`: 검증 가능한 원본 단서.

## run_context 연동 가이드

- `run_context.inputs.repo.diff_base` ↔ `repo.base`
- `run_context.inputs.repo.diff_target` ↔ `repo.head`
- `run_context.analysis_scope.file_count` ↔ `summary.total_files`
- 필터 정책(`docs/INCLUDE_EXCLUDE_RULES.md`)은 양쪽에 동일하게 적용되어야 한다.

충돌 시 `run_context.needs_review`에 아래 포맷으로 기록한다.

```json
{
  "path": "analysis_scope.file_count",
  "run_context": 12,
  "changed_files": 15,
  "reason": "filter_mismatch_or_stale_artifact"
}
```
