# STATUS.md

## Source of Truth: Task Board

| ID | Task | Status | 근거/비고 |
|---|---|---|---|
| W5-T01 | 중간공유 패키지/운영 문서 정비 | ✅ Done | `share_pack_mid/README.md`, `RUNBOOK.md`, `LIMITS.md` 반영 |
| W5-T02 | 3-command 데모 시나리오 고정 | ✅ Done | `detect-endpoints -> build-w4 -> generate api` 고정 |
| W5-T03 | 리허설 체크리스트/장애대응 문서화 | ✅ Done | RUNBOOK 절차 정리 |
| W5-T04 | 재현성 리허설(동일 입력/동일 해시) | ✅ Done | `API.md` 2회 생성 해시 동일 확인 |
| W5-T05 | 세션 상태/검증 로그 관리 | 🟡 In Progress | STATUS 누적 규칙 단순화 필요 |
| W4-T01 | `build-w4` 구현 | ✅ Done | `endpoints.json` 기반 `ir_merged.json`/`features.json` 생성 |
| W4-T03 | W4 산출물 결정론 규칙 연계 | ✅ Done | dedupe/정렬/evidence/feature_id 반영 |
| W4-T05 | `generate api` 고도화 | ✅ Done | feature 연계, wildcard/UNKNOWN needs_review 반영 |
| W4-T06 | API 문서 포맷 고정 | ✅ Done | 섹션/테이블 구조 결정론 유지 |
| W4-T08 | `generate spec` 구현 | ✅ Done | Overview/Metadata/Diff Summary/Feature Changes/Validation Plan/needs_review 생성 |
| W4-T09 | `validate` 품질 규칙 반영 | ✅ Done | strict/non-strict 자동 검증 |
| W3-T01 | Controller detection MVP | ✅ Done | fixture 기반 endpoint 추출 구현 |
| W3-T02 | endpoint_id 결정론 규칙 적용 | ✅ Done | `ep_` + sha1 16자리 |
| W3-T03 | CLI 산출물 생성 연계 | ✅ Done | `detect-endpoints` 실생성 확인 |
| W3-T04 | source evidence 기록 | ✅ Done | endpoint evidence 포함 |
| W3-T07 | W3 자동화 테스트 | ✅ Done | `tests/test_w3_controller_detection.py` |
| W3-T09 | fixture/golden/quality gate 확장 | ✅ Done | 10개 케이스 기준 자동 검증 통과 |
| W2-T01 | `analyze` 산출물 생성 | ✅ Done | `repo_meta.json`, `scan_index.json` |
| W2-T02 | `diff` 기본 동작/실패코드 | ✅ Done | exit code 3/5/7 반영 |
| W2-T03 | changed_files 안정 정렬 | ✅ Done | path/status/old_path 정렬 |
| W2-T04 | W2 산출물 테스트 | ✅ Done | pytest 자동화 |
| W2-T06 | 실패 계약 테스트 | ✅ Done | 예외/실패 시나리오 검증 |
| W2-T08 | include/exclude 정규화 | ✅ Done | S07 경로 패턴 케이스 통과 |
| NEXT-01 | `generate db-schema` 구현 | ⬜ Todo | 문서 생성 경로 마지막 공백 |
| NEXT-02 | S02/S06 CI 자동 판정기 | ⬜ Todo | 임시 repo/훅 의존 제거 필요 |
| NEXT-03 | 샘플 repo fixture 실제 추가 | ⬜ Todo | `examples/repo-sample` 필요 |

---

## 현재 목표
- 검증 시나리오(S01~S08) 재현성을 유지하면서, 남은 핵심 과제를 `generate db-schema` 및 CI 자동 판정 고도화로 축소한다.

## 진행 중(핵심)
- `lab validate`의 리포트 포맷/스키마 세부 규칙 고도화(단일 CI fail-fast 기준 정교화).
- STATUS 검증 명령 기록 정책(세션 누적 방식) 단순화.

## 완료 하이라이트
- W2~W5 핵심 명령(`analyze`, `diff`, `detect-endpoints`, `build-w4`, `generate api`, `generate spec`, `validate`) 구현 및 테스트 연계 완료.
- LLM OFF E2E에서 정상 케이스/경고 케이스 모두 재현, strict/non-strict 정책 차이 검증 완료.
- W3 fixture/golden/quality gate 10케이스 자동 검증 체계 확정.

## 다음 액션(우선순위)
1. `generate db-schema` 구현 + 테스트 추가.
2. S02/S06 전용 검증을 CI 친화형 자동 판정 스크립트로 고정.
3. `examples/repo-sample` fixture 보강으로 문서/실행 환경 정합성 확보.
4. STATUS 검증 로그 누적 규칙(요약 템플릿) 확정.

## 최근 검증 요약
- `PYTHONPATH=src pytest -q` 다회 실행 기준 최종 16 passed 확인.
- W5 3-command 데모 재실행 시 `API.md` 해시 동일 확인.
- LLM OFF full E2E(run3)에서 analyze → diff → generate api → validate → validate --strict 전 단계 성공.

## 결정사항 / 리스크
- 결정: `generated_at_utc`는 payload 유지, fingerprint 계산에서는 제외.
- 결정: S06 검증용 hidden test hook 유지(운영 경로 오염 방지).
- 결정: optional artifact 누락은 strict 실패가 아닌 INFO 처리.
- 리스크: quality gate 세부 스키마/리포트 규칙은 추가 고도화 필요.
- 리스크: 일부 검증이 임시 브랜치/임시 repo 생성에 의존.
