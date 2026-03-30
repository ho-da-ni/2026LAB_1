# PATH_NORMALIZATION.md

## 문서 목적
LAB 산출물(`run_context.json`, `repo_meta.json`, `changed_files.json`)에서 경로를 일관되게 기록하기 위한 정규화 규칙을 정의한다.

## 기본 원칙

- 경로는 **결정론적 비교 가능성**을 우선한다.
- OS별 표현 차이(구분자, 대소문자, 드라이브 표기)를 흡수한다.
- 사람이 읽는 경로와 해시 입력 경로가 동일 규칙을 따라야 한다.

## 정규화 절차 (v1.0.0)

입력 경로 `raw_path`에 대해 아래 순서로 처리한다.

1. **공백 정리**: 앞뒤 공백 제거.
2. **구분자 통일**: `\\`를 `/`로 변환.
3. **절대/상대 기준 고정**:
   - 워크스페이스 내부 경로는 `workspace.root_path` 기준 상대경로로 저장.
   - 워크스페이스 외부 경로는 절대경로 유지.
4. **중복 구분자 제거**: `//` 연속 구분자를 `/`로 축약.
5. **dot segment 정리**: `.` 제거, `..`는 가능한 범위에서 해소.
6. **심볼릭 링크 처리**:
   - 표시 경로는 링크를 해소하지 않은 논리 경로 사용.
   - fingerprint 입력값은 링크 해소(realpath) 결과를 별도 사용 가능(정책에 명시 필요).
7. **트레일링 슬래시 규칙**:
   - 파일 경로는 trailing `/` 제거.
   - 디렉터리는 저장 시 trailing `/` 제거(타입 필드로 구분).
8. **Windows 드라이브 정규화**:
   - `C:\repo\a.py` → `c:/repo/a.py` (드라이브 소문자).
9. **루트 상대 표기 금지**:
   - `./a/b.py` → `a/b.py`.
10. **빈 경로 방지**:
   - 정규화 결과가 비면 `UNKNOWN` + `needs_review` 기록.

## 비교/저장 규칙

- JSON에 저장되는 경로는 UTF-8 문자열, slash(`/`) 기준이다.
- 경로 비교는 기본적으로 **대소문자 구분(case-sensitive)** 으로 수행한다.
- 단, Windows 수집 환경에서는 `integrity.fingerprint_policy`에 `case_fold_windows=true`를 명시한 경우에만 소문자 비교를 허용한다.

## 금지 규칙

- 홈 축약 표기(`~`) 저장 금지.
- 환경변수 형태(`$HOME`, `%USERPROFILE%`) 저장 금지.
- URL(`file://`, `s3://`)을 로컬 path 필드에 혼용 금지.

## needs_review 기록 예시

```json
{
  "path": "outputs.ir_path",
  "raw": "./artifacts//run-001/../run-001/ir.json",
  "normalized": "artifacts/run-001/ir.json",
  "reason": "non_canonical_input_path"
}
```

## 적용 대상 필드

- `run_context.json`
  - `workspace.root_path`
  - `analysis_scope.include_paths[]`, `analysis_scope.exclude_paths[]`
  - `outputs.*_path`, `outputs.artifact_dir`
- `repo_meta.json`
  - `ownership.codeowners_path`
- `changed_files.json`
  - `files[].path`, `files[].old_path`
  - `filters.include_paths[]`, `filters.exclude_paths[]`

## 버전 관리 규칙

- 본 문서의 규칙 변경 시 `path_normalization_version`을 증가시킨다.
- fingerprint 계산에 경로가 포함된다면, 규칙 변경 시 `fingerprint_policy_version`도 함께 증가시킨다.
