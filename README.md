# LAB

## 프로젝트 한 줄 정의

**LAB는 Git 기준 특정 시점의 소스와 DB 메타데이터를 분석하여, 결정론적인 팩트 기반 문서(API/SPEC/DB_SCHEMA)를 재현 가능하게 생성하는 Python CLI 도구이다.**

## 프로젝트 정의

LAB는 소스 코드와 DB 메타데이터를 기반으로 시스템 구조와 기능 변경 사항을 분석하고, 이를 문서 형태로 일관되게 생성하는 Python CLI 도구이다.

프로젝트의 핵심 원칙은 **팩트는 정적 분석/DB 메타데이터로만 생성하고, 추정하지 않으며, 실행마다 재현 가능해야 한다**는 점이다.

산출물은 JSON 기반 IR과 Markdown 문서(`API.md`, `SPEC.md`, `DB_SCHEMA.md` 등)이며, 실행 컨텍스트(`run_context.json`)와 fingerprint를 통해 동일 입력에 대해 동일 결과를 보장하는 것을 목표로 한다.

LLM은 선택적으로 사용할 수 있으나, summary 작성에만 제한되며 endpoint, DB schema, 권한, 응답, 예외 등의 팩트를 생성하거나 추정하는 데 사용하지 않는다.

## 기본 폴더 구조

```text
LAB/
├─ README.md
├─ docs/
│  ├─ README.md
│  ├─ STRUCTURE.md
│  ├─ API.md
│  ├─ SPEC.md
│  ├─ DB_SCHEMA.md
│  └─ CLI.md
├─ src/
│  └─ lab/
│     └─ __init__.py
├─ tests/
├─ examples/
└─ artifacts/
```

## 왜 이런 구조로 시작해야 하는가

- `docs/`는 사람이 읽는 기준 문서를 한곳에 모아 프로젝트 정의와 산출물 기준을 흔들리지 않게 유지한다.
- `src/lab/`는 Python CLI 구현을 담는 영역으로, 문서와 실행 코드를 분리해 책임을 명확하게 만든다.
- `tests/`는 결정론성과 재현 가능성을 검증하는 자동화 테스트를 두는 위치다.
- `examples/`는 입력 예시, 샘플 diff, 샘플 메타데이터처럼 재현 가능한 데모 자산을 관리하기 좋다.
- `artifacts/`는 실행 결과 예시나 템플릿 산출물처럼 생성물을 보관할 때 유용하며, 소스와 결과를 분리해 비교와 검증을 쉽게 한다.

자세한 설명은 `docs/STRUCTURE.md`에 정리했다.

## 사용자 인터페이스 범위

- 사용자 인터페이스는 **CLI 기준으로 고정**한다.
- 초기 범위에서는 웹 UI나 운영 배포용 서비스 대신, 재현 가능한 커맨드라인 실행 흐름에 집중한다.
- CLI 명령어 초안은 `docs/CLI.md`에 정리한다.

## CLI 명령어 초안

- `lab analyze`: 소스 코드와 DB 메타데이터를 분석해 IR, `run_context.json`, fingerprint를 생성한다.
- `lab generate api`: `API.md`를 생성한다.
- `lab generate spec`: `SPEC.md`를 생성한다.
- `lab generate db-schema`: `DB_SCHEMA.md`를 생성한다.
- `lab diff`: 두 Git 기준점 사이의 변경 파일과 영향 범위를 수집한다.
- `lab validate`: 산출물과 quality check 결과를 검증한다.

자세한 옵션과 예시는 `docs/CLI.md`를 따른다.

## 프로젝트 목표

- 소스/DB 구조를 바탕으로 문서화를 자동화한다.
- 변경 파일(diff) 기준으로 영향 범위와 기능 단위를 정리할 수 있게 한다.
- 실행 결과를 재현 가능하게 남겨 디버깅과 검증을 쉽게 한다.
- 문서 생성 과정에서 추정 대신 `UNKNOWN + needs_review` 방식으로 불확실성을 격리한다.

## 프로젝트 비목표

- LLM이 팩트를 추정하거나 생성하는 기능
- 런타임 실행 결과 기반 분석
- 자동 코드 수정/패치
- 운영 배포용 서비스/웹 UI
- 실데이터 기반 분석

## 핵심 원칙

- Facts are deterministic
- Narrative is probabilistic (summary-only)
- No guessing
- FAIL_FAST
- Reproducibility first

## 산출물 기준

- JSON IR
- Markdown 문서
- `run_context.json`
- fingerprint
- quality check 결과

기본 문서 템플릿은 `docs/API.md`, `docs/SPEC.md`, `docs/DB_SCHEMA.md`에 준비했다.

## 완료 기준 (DoD)

- 프로젝트 한 줄 정의가 확정되어 있다.
- 프로젝트 목적/원칙/비목표가 1페이지 내로 설명 가능하다.
- 이후 범위 정의 및 정책 문서의 기준 문장으로 재사용 가능하다.

## STATUS.md 운영 규칙
- 작업 시작 전 `STATUS.md`를 읽고 현재 목표, 진행 중 항목, 다음 액션을 확인한다.
- 계획이 확정되면 `STATUS.md`의 현재 목표와 작업 계획을 먼저 갱신한다.
- 각 마일스톤 완료 후 `STATUS.md`를 업데이트한다.
- 업데이트 시 아래 항목을 유지한다:
  - 현재 목표
  - 완료됨
  - 진행 중
  - 다음 액션
  - 검증 명령 및 결과
  - 결정사항 / 리스크
- 검증 실패, 범위 변경, 중요한 설계 결정이 생기면 즉시 `STATUS.md`에 반영한다.
- 세션 종료 전 반드시 `STATUS.md`를 최신 상태로 정리하고, 다음 세션 시작 프롬프트를 1~3줄로 남긴다.
