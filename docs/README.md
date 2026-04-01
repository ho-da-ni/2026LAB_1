# Documentation Overview

이 디렉터리는 LAB의 기준 문서와 산출물 템플릿을 보관한다.

## 포함 문서

- `STRUCTURE.md`: 기본 폴더 구조와 각 디렉터리의 책임 설명
- `API.md`: API 문서 산출물의 기본 템플릿
- `SPEC.md`: 기능/변경 명세 문서의 기본 템플릿
- `DB_SCHEMA.md`: DB 메타데이터 기반 스키마 문서의 기본 템플릿
- `RUN_CONTEXT_SCHEMA.md`: `run_context.json` 스키마 초안 템플릿
- `REPO_META_SCHEMA.md`: `repo_meta.json` 스키마 초안 템플릿
- `CHANGED_FILES_SCHEMA.md`: `changed_files.json` 스키마 초안 템플릿
- `FEATURES_SCHEMA.md`: `features.json` 스키마/ID/근거(evidence) 규칙
- `PATH_NORMALIZATION.md`: 산출물 경로 정규화 규칙
- `DIFF_FAILURE_CONTRACT.md`: `lab diff` 실패 처리 계약
- `INCLUDE_EXCLUDE_RULES.md`: include/exclude 필터 정책
- `VALIDATION_TEST_SCENARIOS.md`: 검증 범위 고정용 테스트 시나리오 목록
- `QUALITY_RULES.md`: UNKNOWN/http='*'/evidence 누락 포함 품질 게이트 상세 규칙
- `REPRODUCIBILITY_VERIFICATION.md`: 2회 동일성 검정 기반 동일 입력/동일 출력 검증 절차
- `CLI.md`: CLI 인터페이스 범위와 명령어 초안
- `SPRING_BOOT_CONTROLLER_DETECTION_RULES.md`: Spring Boot Controller/Endpoint 정적 탐지 전용 규칙
- `EGOVFRAME_CONTROLLER_DETECTION_RULES.md`: 전자정부프레임워크 Controller/Endpoint 정적 탐지 전용 규칙
- `IR_MERGED_MERGE_RULES.md`: `ir_merged` 산출 시 적용할 병합 관점 요약 규칙
- `CONTROLLER_DETECTION_FIXTURE_CASES.md`: Controller/Endpoint 탐지 규칙 검증용 fixture 케이스 목록

## 문서 운영 원칙

- 팩트는 정적 분석과 DB 메타데이터로만 채운다.
- 불확실한 값은 추정하지 않고 `UNKNOWN` 또는 `needs_review`로 남긴다.
- 동일 입력에 대해 동일 문서를 재생성할 수 있어야 한다.
