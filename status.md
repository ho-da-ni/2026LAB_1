# STATUS.md

## 현재 목표
- 초기 문서/구조 정리를 마무리하고, 다음 세션에서 바로 CLI 구현을 시작할 수 있는 상태를 만든다.

## 완료됨
- 프로젝트 한 줄 정의, 목표, 비목표, 핵심 원칙, 산출물 기준을 `README.md`에 정리했다.
- 기본 폴더 구조와 문서 템플릿(`API.md`, `SPEC.md`, `DB_SCHEMA.md`, `CLI.md`)을 추가했다.
- 사용자 인터페이스 범위를 CLI로 고정하고, CLI 명령어 초안을 문서화했다.
- `STATUS.md` 운영 규칙을 `README.md`에 반영했다.
- 이번 세션 종료 기준으로 `STATUS.md`를 최신 상태로 갱신했다.

## 진행 중
- 문서 초안은 정리되었지만, 실제 CLI 엔트리포인트와 명령 파서는 아직 구현되지 않았다.
- 예제 입력/기대 산출물/자동화 테스트는 아직 준비되지 않았다.

## 다음 액션
1. `src/lab/`에 CLI 엔트리포인트(`main.py` 또는 `cli.py`)와 명령 파서를 추가한다.
2. `lab analyze`, `lab generate`, `lab diff`, `lab validate`의 실제 입출력 계약을 코드와 예제로 구체화한다.
3. 예제 입력과 기대 산출물을 만들고 테스트를 추가한다.

## 검증 명령
- `nl -ba README.md` → 성공, README의 CLI 범위/명령 초안/STATUS 운영 규칙 반영 확인.
- `nl -ba docs/CLI.md` → 성공, CLI 전용 방침과 명령어 초안 문서 확인.
- `nl -ba docs/README.md` → 성공, 문서 인덱스에 `CLI.md` 포함 확인.
- `nl -ba status.md` → 성공, 세션 종료 상태 반영 확인.
- `git diff -- README.md docs/CLI.md docs/README.md status.md` → 성공, 최종 문서 변경 내용 검토 완료.
- `python - <<'PY' ...` → 성공, 주요 Markdown 파일 line count 출력 확인.

## 주의사항 / 리스크
- 현재 CLI 명령과 옵션은 문서 초안 단계이며, 구현 과정에서 세부 이름이나 출력 경로 규칙이 조정될 수 있다.
- 다만 CLI 기준 고정, 정적 분석/DB 메타데이터 기반 팩트 생성, `UNKNOWN`/`needs_review` 처리 원칙은 유지해야 한다.
- 이후 구현 시에도 웹 UI/운영 서비스 범위로 확장하지 않도록 주의해야 한다.

## 다음 세션 시작 프롬프트
- STATUS.md와 AGENTS.md를 먼저 읽고, 남은 작업 중 1번인 CLI 엔트리포인트 추가부터 시작해.
- `src/lab/`에 최소 실행 가능한 CLI 골격을 만들고, `lab analyze`부터 연결해.
