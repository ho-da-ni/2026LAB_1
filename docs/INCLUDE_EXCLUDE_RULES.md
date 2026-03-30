# INCLUDE_EXCLUDE_RULES.md

## 문서 목적
LAB 분석/차이 추출 시 `include_paths`/`exclude_paths` 적용 규칙을 정의한다.

## 기본 원칙

- 기본값은 **전체 포함 + 명시적 제외**이다.
- 동일 경로가 include/exclude 모두에 매칭되면 **exclude 우선**이다.
- 경로 비교 전 `docs/PATH_NORMALIZATION.md` 규칙으로 정규화한다.

## 기본 제외 경로 (필수)

아래 경로는 사용자 설정과 무관하게 기본 제외한다.

- `.git/`
- `build/`
- `target/`

목적:
- `.git/`: VCS 내부 파일/객체 제외
- `build/`, `target/`: 생성물/캐시/환경의존 산출물 제외

## 평가 순서

1. 경로 정규화
2. 기본 제외 경로 매칭 확인 (`.git/`, `build/`, `target/`)
3. 사용자 `exclude_paths` 매칭
4. 사용자 `include_paths` 매칭
5. 최종 판정

> 판정 규칙: 2~3단계에서 제외되면 include 매칭 여부와 무관하게 제외한다.

## 글롭 패턴 규칙

- `/` 기준 경로를 사용한다.
- `**`는 하위 모든 디렉터리 매칭.
- `*`는 단일 세그먼트 매칭.
- 후행 `/`가 있는 패턴은 디렉터리 전용으로 해석한다.

예시:
- `src/**` 포함
- `**/*.py` 포함
- `**/build/**` 제외
- `**/target/**` 제외
- `**/.git/**` 제외

## run_context 반영 규칙

- `analysis_scope.include_paths`에는 사용자 입력값을 보존한다.
- `analysis_scope.exclude_paths`에는 기본 제외(`.git/`, `build/`, `target/`) + 사용자 exclude를 함께 기록한다.
- 기본 제외 경로 강제 적용 사실은 `notes` 또는 `quality_checks.checks[].evidence`에 기록한다.
- `analysis_scope.file_count`는 기본 제외 적용 후 파일 수를 사용한다.

## changed_files 반영 규칙

- `filters.include_paths`, `filters.exclude_paths`에는 사용자 입력 필터를 기록한다.
- 기본 제외로 누락된 파일이 있을 경우 `needs_review`에 정책 적용 사실을 남긴다.

예시:

```json
{
  "path": "filters.exclude_paths",
  "applied_default_excludes": [".git/", "build/", "target/"],
  "reason": "default_policy_enforced"
}
```

## 권장 검증 체크

- `include_exclude_policy_loaded`
- `default_excludes_applied`
- `exclude_precedence_enforced`
- `analysis_scope_count_post_filter_valid`

## 버전

- `policy_version`: `1.0.0`
- 정책 변경 시 `RUN_CONTEXT_SCHEMA.md`의 `schema_version` 및 관련 quality check 기준과 함께 검토한다.
