# LAB

## 프로젝트 한 줄 정의

**LAB는 Git 기준 특정 시점의 소스와 DB 메타데이터를 분석하여, 결정론적인 팩트 기반 문서(API/SPEC/DB_SCHEMA)를 재현 가능하게 생성하는 Python CLI 도구이다.**

## 프로젝트 정의

LAB는 소스 코드와 DB 메타데이터를 기반으로 시스템 구조와 기능 변경 사항을 분석하고, 이를 문서 형태로 일관되게 생성하는 Python CLI 도구이다.

프로젝트의 핵심 원칙은 **팩트는 정적 분석/DB 메타데이터로만 생성하고, 추정하지 않으며, 실행마다 재현 가능해야 한다**는 점이다.

산출물은 JSON 기반 IR과 Markdown 문서(`API.md`, `SPEC.md`, `DB_SCHEMA.md` 등)이며, 실행 컨텍스트(`run_context.json`)와 fingerprint를 통해 동일 입력에 대해 동일 결과를 보장하는 것을 목표로 한다.

LLM은 선택적으로 사용할 수 있으나, summary 작성에만 제한되며 endpoint, DB schema, 권한, 응답, 예외 등의 팩트를 생성하거나 추정하는 데 사용하지 않는다.

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

## 완료 기준 (DoD)

- 프로젝트 한 줄 정의가 확정되어 있다.
- 프로젝트 목적/원칙/비목표가 1페이지 내로 설명 가능하다.
- 이후 범위 정의 및 정책 문서의 기준 문장으로 재사용 가능하다.

## 더 짧은 버전

> LAB는 소스 코드와 DB 메타데이터를 분석해, 팩트 기반 문서를 재현 가능하게 생성하는 Python CLI 도구이다.
