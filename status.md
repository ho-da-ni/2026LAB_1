# STATUS.md

## 현재 목표
- 문서 초안 단계를 마무리하고, 다음 세션에서 `run_context.json` 생성/검증 로직 구현을 바로 시작할 수 있는 상태를 만든다.

## 완료됨
- 프로젝트 한 줄 정의, 목표, 비목표, 핵심 원칙, 산출물 기준을 `README.md`에 정리했다.
- 기본 폴더 구조와 문서 템플릿(`API.md`, `SPEC.md`, `DB_SCHEMA.md`, `CLI.md`)을 추가했다.
- 사용자 인터페이스 범위를 CLI로 고정하고, CLI 명령어 초안을 문서화했다.
- `STATUS.md` 운영 규칙을 `README.md`에 반영했다.
- 이번 세션 종료 기준으로 `STATUS.md`를 최신 상태로 갱신했다.
- `run_context.json` 구조 정의를 위한 `docs/RUN_CONTEXT_SCHEMA.md` 초안을 추가했다.
- `RUN_CONTEXT_SCHEMA.md`에 fingerprint 포함/제외 및 정규화 규칙 초안을 반영했다.
- `RUN_CONTEXT_SCHEMA.md`에 exit code 정책(v1.0.0) 초안을 반영했다.
- `RUN_CONTEXT_SCHEMA.md`에 quality rubric(v1.0.0) 초안을 반영했다.
- `RUN_CONTEXT_SCHEMA.md`의 핵심 항목(스키마/무결성/종료코드/품질기준)이 문서 기준선으로 합의 가능한 수준까지 정리되었다.

## 진행 중
- 문서 초안은 정리되었지만, 실제 CLI 엔트리포인트와 명령 파서는 아직 구현되지 않았다.
- 예제 입력/기대 산출물/자동화 테스트는 아직 준비되지 않았다.
- `run_context.json` 스키마의 필수/선택 필드 구분과 코드 구현 연동은 아직 남아 있다.
- quality rubric 점수 계산/등급 산정을 실제 `lab validate` 결과와 연결하는 구현이 남아 있다.

## 다음 액션
1. `src/lab/`에 최소 CLI 엔트리포인트를 만들고 `lab analyze`에서 `run_context.json`을 실제 생성하도록 연결한다.  ← 다음 세션 첫 액션
2. 생성된 `run_context.json`이 `docs/RUN_CONTEXT_SCHEMA.md`의 필수 필드를 만족하는지 검증 로직을 추가한다.
3. `lab validate`에서 exit code 정책(v1.0.0)과 quality rubric(v1.0.0) 판정 로직을 구현한다.
4. 예제 입력/기대 산출물/회귀 테스트를 추가해 재현성과 fingerprint 정책을 자동 검증한다.

## 검증 명령
- `git status --short` → 성공, 변경 대상 파일 상태 확인.
- `nl -ba docs/RUN_CONTEXT_SCHEMA.md | sed -n '1,420p'` → 성공, 스키마/정책/루브릭/종료코드 규칙 최종 확인.
- `nl -ba status.md | sed -n '1,90p'` → 성공, 세션 종료 기준 상태 반영 확인.
- `git add docs/RUN_CONTEXT_SCHEMA.md status.md && git commit -m "Define quality rubric for run_context checks"` → 성공, 변경사항 커밋 완료.

## 주의사항 / 리스크
- 현재 내용은 문서 기준선이며, 실제 구현 시 필드명/출력 경로/체크 세부 규칙이 일부 조정될 수 있다.
- 다만 `No guessing`, `UNKNOWN/needs_review` 처리, 재현성 우선 원칙은 변경하지 않는다.
- fingerprint 정책 변경 시 기존 산출물과 해시 호환성이 깨질 수 있으므로 `schema_version`/정책 버전 동시 관리가 필요하다.
- quality rubric/exit code 정책은 CI와 직결되므로 임의 변경 시 버전 증가 및 마이그레이션 노트가 필요하다.

## 다음 세션 시작 프롬프트
- STATUS.md와 AGENTS.md를 먼저 읽은 뒤, `src/lab/`에 CLI 엔트리포인트를 만들고 `lab analyze`에서 `run_context.json`을 생성하도록 구현을 시작해.
- 구현 직후 샘플 실행으로 `run_context.json`을 만들고, `docs/RUN_CONTEXT_SCHEMA.md` 필수 필드 충족 여부를 먼저 검증해.
