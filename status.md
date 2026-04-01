# STATUS.md

## 현재 목표
- `lab diff`의 검증 시나리오(S01~S08)를 문서 기준에 맞게 안정적으로 재현하고, 남은 과제는 `lab validate` 자동 판정기 구현으로 좁힌다.

## 완료됨
- W5-T01/W5-T02/W5-T03/W5-T04/W5-T05 대응: 중간공유 패키지 디렉터리(`share_pack_mid/README.md`)와 `RUNBOOK.md`, `LIMITS.md` 초안을 추가했다.
- 3-command 데모 시나리오(`detect-endpoints -> build-w4 -> generate api`)를 고정하고, 리허설 체크리스트/장애 대응 절차를 문서화했다.
- 리허설 검증: 동일 입력 고정 상태에서 `generate api` 2회 재실행 시 `API.md` 해시 동일을 확인했다.
- W4-T05/W4-T06 대응: `generate api`를 보강해 feature 연계(`--features`), wildcard/UNKNOWN `needs_review` 반영, 고정 섹션/테이블 구조를 유지하도록 개선했다.
- W4-T08 대응: `generate spec`를 구현해 변경 중심 구조(Overview/Metadata/Diff Summary/Feature Changes/Validation Plan/needs_review)를 실제 생성하도록 연결했다.
- W4-T09 대응: `validate`에 W4 품질 규칙(`QR-IR-002/003/004`, `QR-API-001/002/004`, `QR-SPEC-001`)을 반영하고 strict/non-strict 차이를 자동 검증했다.
- LLM OFF E2E(정상 케이스 + 경고 케이스) 실행을 완료해 API/SPEC/QUALITY_CHECK 생성 및 strict 정책 차이를 확인했다.
- W4-T01/W4-T03 대응: `build-w4` 명령을 추가해 `endpoints.json` 입력으로 `ir_merged.json`/`features.json`을 실제 생성하도록 구현했다.
- W4 산출물 규칙(중복 제거/정렬/evidence/feature_id 결정론)을 CLI 로직으로 연결하고 pytest(`tests/test_w4_artifacts.py`)를 추가했다.
- W3-T09(확장) 대응: fixture 부족분 4개(`M001`, `M002`, `C003`, `C004`)를 추가해 총 10개 케이스를 충족했다.
- 신규 4개 케이스에 대한 golden snapshot을 추가하고 `quality_gate_report.json`의 case 집계/평가 목록을 10개 기준으로 갱신했다.
- W3 품질 게이트 테스트를 보강해 신규 4개 케이스가 자동 검증 대상에 포함되는지 확인하도록 업데이트했다.
- W3-T09 대응: fixture 기대값 비교 + golden snapshot 비교 + quality high gate 판정 로직(`evaluate_quality_high_gate`)을 추가해 자동 검증을 고정했다.
- W3 fixture 입력 2회 실행 동일성(결정론성) 검증을 테스트로 추가했다.
- fixture 케이스 목표(10) 대비 현재(6) 부족분(4)을 quality gate 리포트에 자동 계산하도록 반영했다.
- W3-T01/W3-T02/W3-T03/W3-T04/W3-T07 대응: fixture 기반 Java endpoint MVP(`detect-endpoints`)를 추가해 `endpoints.json`을 실제 생성하도록 구현했다.
- controller detection 모듈(`src/lab/controller_detection.py`)을 추가해 fixture case 기반 endpoint 추출, source evidence 기록, `endpoint_id` 결정론(`ep_` + sha1 16자리)을 코드로 고정했다.
- W3 pytest(`tests/test_w3_controller_detection.py`)를 추가해 endpoint_id 결정론, 최소 fixture 입력 추출, CLI 산출물 생성을 자동 검증했다.
- W2-T01/W2-T02 대응: `lab analyze` 실행 시 `repo_meta.json`과 `scan_index.json`을 실제 생성하도록 구현했다.
- W2-T03 대응: `changed_files.json`의 `files` 배열을 안정 정렬(path/status/old_path)로 고정해 출력 순서 결정론성을 강화했다.
- W2-T04/W2-T06/W2-T08 대응: W2 산출물/실패 계약 검증용 pytest(`tests/test_w2_artifacts.py`)를 추가해 정상/실패/예외 시나리오를 자동화했다.
- `src/lab/`에 CLI 엔트리포인트(`python -m lab`)와 `analyze`/`diff` 기본 동작을 구현했다.
- `lab diff`가 `changed_files.json`을 생성하고, ref 해석 실패 시 `exit_code=3`, 출력 실패 시 `exit_code=5`, 무결성 불일치 시 `exit_code=7`을 반환하도록 구현했다.
- include/exclude 패턴 정규화(`_normalize_match_pattern`)를 추가해 S07 경로 패턴 케이스를 통과시켰다.
- `generated_at_utc` 변동이 fingerprint를 흔들지 않도록, fingerprint 계산 시 `generated_at_utc`를 제외했다.
- S08 재실행 결정론성 검증에서 동일 입력 2회 실행 시 산출물 해시 동일을 확인했다.
- S02 대응으로 기본 제외 경로(`.git/`, `build/`, `target/`)가 실제 적용된 경우 `needs_review`에 `default_excludes_applied` 증거를 남기도록 구현했다.
- S06 대응으로 `--test-hook-force-integrity-mismatch` 테스트 훅을 추가해 무결성 불일치 경로(`exit_code=7`)를 재현 가능하게 만들었다.
- 로컬에 `main` 브랜치 ref가 없는 환경 이슈를 보완하기 위해 세션 중 로컬 `main` ref를 생성하여 main 기준 diff 검증을 진행했다.
- Spring Boot/전자정부프레임워크 Controller 탐지 전용 룰셋 문서(`docs/SPRING_BOOT_CONTROLLER_DETECTION_RULES.md`, `docs/EGOVFRAME_CONTROLLER_DETECTION_RULES.md`)를 추가하고 문서 인덱스(`docs/README.md`)를 갱신했다.
- Spring Boot/eGovFrame 룰셋에 mapping 합성 규칙(클래스/메서드 결합, method 교집합, 외부 prefix unresolved 처리, `needs_review` 충돌 코드)을 상세화했다.
- mapping 합성 규칙에 `(ClassMapping × MethodMapping)` 조합 정의, endpoint key 규칙, 조합 예시를 추가해 구현 기준을 명시했다.
- multi-path 처리 규칙(수집/정규화/전개/정렬/dedupe/충돌/폭증 제어)과 관련 `needs_review` 코드 정의를 룰셋에 추가했다.
- multi-path 배열 처리 방식(문자열 승격, union 병합, 빈값 정규화, 인덱스 evidence, 빈 배열 대체 규칙)을 추가로 명시했다.
- multi-method 처리 규칙과 HTTP 배열 처리 방식(문자열/배열 승격, 교집합 산출, dedupe, 빈 배열 `UNKNOWN_METHOD` 치환)을 Spring Boot/eGovFrame 룰셋에 추가했다.
- endpoint_id 생성 규칙(canonical source, `ep_`+sha1 16자리, 비본질 메타데이터 제외, collision 처리)을 Spring Boot/eGovFrame 룰셋에 추가했다.
- Controller/Endpoint 탐지 fixture 케이스 목록 문서(`docs/CONTROLLER_DETECTION_FIXTURE_CASES.md`)를 추가하고 docs 인덱스에 등록했다.
- endpoint 기대값 JSON(`fixtures/controller_detection/endpoints.fixture.json`)과 golden snapshot JSON(`fixtures/controller_detection/golden_snapshots.json`)을 추가했다.
- golden fixture 품질 게이트 결과 파일(`fixtures/controller_detection/quality_gate_report.json`)을 추가하고 `quality_high=PASS` 기준을 반영했다.
- endpoint fixture JSON 포맷을 정리하고(`quality_gate_high` 포함), golden snapshot/quality gate와의 정합성을 확인했다.

- `pyproject.toml`을 추가해 `pip install -e .` 설치 경로와 console script(`lab=lab.cli:main`)를 프로젝트에 고정했다.
- README/CLI 문서에 프로젝트 레벨 설치 절차(venv + editable install)를 추가했다.

- build-system의 setuptools 버전 하한(`>=68`)을 제거해 `--no-build-isolation` 설치 시 로컬 setuptools를 재사용할 수 있게 조정했다.
- README/CLI 문서의 설치 기본 예시를 `pip install -e . --no-build-isolation`으로 변경하고 프록시 환경 대응 팁을 추가했다.
- `lab validate`를 구현해 `--run-dir`, `--strict` 옵션으로 산출물 검증 및 `quality_gate_report.json` 생성이 가능해졌다.
- quality gate를 고도화해 rule code 기반(INFO/WARN/ERROR) 결과를 출력하고 strict 판정 정책을 적용했다.
- `lab generate api --input --output`를 구현해 `ir_merged.json`에서 결정론적인 `API.md`를 생성할 수 있게 했다.
- LLM OFF full E2E(run3: analyze → diff → generate api → validate → validate --strict)를 완료하고 전 단계 성공을 확인했다.

## 진행 중
- `generate spec`, `generate db-schema`는 아직 TODO 상태다.
- S02/S06은 현재 diff 실행 + 보조 검증(임시 repo/테스트 훅) 방식으로 확인하고 있으며, CI용 일괄 자동 판정 스크립트는 미구현이다.

## 다음 액션
1. `generate spec`, `generate db-schema` 구현으로 문서 생성 경로를 완성.
2. S02/S06 전용 fixture/훅을 테스트 코드로 내장해 로컬/CI 모두에서 동일하게 재현.
3. main/feature 기준 샘플 repo fixture(`examples/repo-sample`)를 실제로 추가해 문서 사전조건과 실행환경 일치.
4. STATUS.md 검증 명령 섹션을 세션 단위로 누적 관리할 수 있게 간소화 규칙 정리.

## 검증 명령 및 결과
- `LLM_MODE=off PYTHONPATH=src python -m lab detect-endpoints --input fixtures/controller_detection/endpoints.fixture.json --case-id C001 --output /tmp/lab-mid-demo/endpoints.json` + `LLM_MODE=off PYTHONPATH=src python -m lab build-w4 --endpoints-input /tmp/lab-mid-demo/endpoints.json --output-dir /tmp/lab-mid-demo --base main --head work --merge-base UNKNOWN` + `LLM_MODE=off PYTHONPATH=src python -m lab generate api --input /tmp/lab-mid-demo/ir_merged.json --features /tmp/lab-mid-demo/features.json --output /tmp/lab-mid-demo/API.md` → 성공(W5 3-command 데모).
- `sha256sum /tmp/lab-mid-demo/API.md` + `LLM_MODE=off PYTHONPATH=src python -m lab generate api --input /tmp/lab-mid-demo/ir_merged.json --features /tmp/lab-mid-demo/features.json --output /tmp/lab-mid-demo/API.md` + `sha256sum /tmp/lab-mid-demo/API.md` → 성공(W5 리허설 재현성), 해시 동일 확인.
- `PYTHONPATH=src pytest -q` → 성공(16 passed), W4 API/SPEC/QUALITY_CHECK + 재현성 테스트 포함 전체 통과.
- `LLM_MODE=off PYTHONPATH=src python -m lab detect-endpoints --input fixtures/controller_detection/endpoints.fixture.json --case-id C001 --output /tmp/lab-w4-e2e/endpoints.json` + `LLM_MODE=off PYTHONPATH=src python -m lab build-w4 --endpoints-input /tmp/lab-w4-e2e/endpoints.json --output-dir /tmp/lab-w4-e2e --base main --head work --merge-base UNKNOWN` + `LLM_MODE=off PYTHONPATH=src python -m lab diff --repo . --base HEAD~1 --head HEAD --output /tmp/lab-w4-e2e/changed_files.json` + `LLM_MODE=off PYTHONPATH=src python -m lab generate api --input /tmp/lab-w4-e2e/ir_merged.json --features /tmp/lab-w4-e2e/features.json --output /tmp/lab-w4-e2e/API.md` + `LLM_MODE=off PYTHONPATH=src python -m lab generate spec --changed-files /tmp/lab-w4-e2e/changed_files.json --features /tmp/lab-w4-e2e/features.json --ir /tmp/lab-w4-e2e/ir_merged.json --output /tmp/lab-w4-e2e/SPEC.md` + `LLM_MODE=off PYTHONPATH=src python -m lab analyze --repo . --output-dir /tmp/lab-w4-e2e` + `LLM_MODE=off PYTHONPATH=src python -m lab validate --run-dir /tmp/lab-w4-e2e` + `LLM_MODE=off PYTHONPATH=src python -m lab validate --run-dir /tmp/lab-w4-e2e --strict` → 성공, non-strict/strict 모두 `exit_code=0` (경고 없음).
- `LLM_MODE=off PYTHONPATH=src python -m lab detect-endpoints --input fixtures/controller_detection/endpoints.fixture.json --case-id E001 --output /tmp/lab-w4-e2e-warn/endpoints.json` + `LLM_MODE=off PYTHONPATH=src python -m lab build-w4 --endpoints-input /tmp/lab-w4-e2e-warn/endpoints.json --output-dir /tmp/lab-w4-e2e-warn --base main --head work --merge-base UNKNOWN` + `LLM_MODE=off PYTHONPATH=src python -m lab diff --repo . --base HEAD~1 --head HEAD --output /tmp/lab-w4-e2e-warn/changed_files.json` + `LLM_MODE=off PYTHONPATH=src python -m lab generate api --input /tmp/lab-w4-e2e-warn/ir_merged.json --features /tmp/lab-w4-e2e-warn/features.json --output /tmp/lab-w4-e2e-warn/API.md` + `LLM_MODE=off PYTHONPATH=src python -m lab generate spec --changed-files /tmp/lab-w4-e2e-warn/changed_files.json --features /tmp/lab-w4-e2e-warn/features.json --ir /tmp/lab-w4-e2e-warn/ir_merged.json --output /tmp/lab-w4-e2e-warn/SPEC.md` + `LLM_MODE=off PYTHONPATH=src python -m lab analyze --repo . --output-dir /tmp/lab-w4-e2e-warn` + `LLM_MODE=off PYTHONPATH=src python -m lab validate --run-dir /tmp/lab-w4-e2e-warn` + `LLM_MODE=off PYTHONPATH=src python -m lab validate --run-dir /tmp/lab-w4-e2e-warn --strict` → 의도대로 차이 확인: non-strict `exit_code=0`, strict `exit_code=4` (`QR-IR-002` 경고를 strict에서 실패 처리).
- `PYTHONPATH=src pytest -q` → 성공(13 passed), W4 ir_merged/features 생성 테스트 포함 전체 통과.
- `PYTHONPATH=src pytest -q` → 성공(11 passed), 10개 fixture + golden/quality gate 자동 검증 통과.
- `PYTHONPATH=src pytest -q` → 성공(10 passed), W3-T09 fixture/golden/quality gate 자동 검증 통과.
- `PYTHONPATH=src pytest -q` → 성공(7 passed), W2/W3 자동화 테스트 통과.
- `PYTHONPATH=src pytest -q` → 성공(4 passed), W2 산출물 생성/실패 코드 검증 자동화 확인.
- `PYTHONPATH=src python -m lab --help` → 성공, CLI 진입점 확인.
- `PYTHONPATH=src python -m lab diff --repo . --base main --head HEAD --output /tmp/lab-tests/rerun/S01_changed_files.json` → 성공(S01).
- `PYTHONPATH=src python -m lab diff --repo /tmp/lab-s02-repo-rerun --base main --head feature/test-diff --output /tmp/lab-tests/rerun/S02_changed_files.json` → 성공(S02), `summary.total_files=0`, `needs_review.default_excludes_applied=pass` 확인.
- `PYTHONPATH=src python -m lab diff --repo . --base main --head HEAD --include 'src/**' --exclude 'src/**' --output /tmp/lab-tests/rerun/S03_changed_files.json` → 성공(S03), 대상 파일 0건.
- `PYTHONPATH=src python -m lab diff --repo . --base does-not-exist --head HEAD --output /tmp/lab-tests/rerun/S04_changed_files.json` → 실패 의도대로 `exit_code=3` 확인(S04).
- `PYTHONPATH=src python -m lab diff --repo . --base main --head HEAD --output /proc/1/S05_changed_files.json` → 실패 의도대로 `exit_code=5` 확인(S05).
- `PYTHONPATH=src python -m lab diff --repo . --base main --head HEAD --test-hook-force-integrity-mismatch --output /tmp/lab-tests/rerun/S06_changed_files.json` → 실패 의도대로 `exit_code=7` 확인(S06).
- `PYTHONPATH=src python -m lab diff --repo . --base main --head HEAD --include './src//lab/../lab/*.py' --output /tmp/lab-tests/rerun/S07_changed_files.json` → 성공(S07), 정규화 패턴 매칭 확인.
- `PYTHONPATH=src python -m lab diff --repo . --base main --head HEAD --output /tmp/lab-tests/rerun/S08_run1.json`
  + `PYTHONPATH=src python -m lab diff --repo . --base main --head HEAD --output /tmp/lab-tests/rerun/S08_run2.json`
  + `sha256sum /tmp/lab-tests/rerun/S08_run1.json /tmp/lab-tests/rerun/S08_run2.json` → 성공(S08), 해시 동일.

- `LLM_MODE=off PYTHONPATH=src python -m lab analyze --repo . --output-dir artifacts/e2e-llm-off/run1` + `LLM_MODE=off PYTHONPATH=src python -m lab diff --repo . --base HEAD~1 --head HEAD --output artifacts/e2e-llm-off/run1/changed_files.json` + `LLM_MODE=off PYTHONPATH=src python -m lab validate` + `LLM_MODE=off PYTHONPATH=src python -m lab generate api` → 부분 성공(E2E-LLM-OFF). analyze/diff 산출물 생성 성공, validate/generate는 현재 TODO 메시지로 미구현 확인.

- `LLM_MODE=off PYTHONPATH=src python -m lab analyze --repo . --output-dir artifacts/e2e-llm-off/run2` + `LLM_MODE=off PYTHONPATH=src python -m lab diff --repo . --base HEAD~1 --head HEAD --output artifacts/e2e-llm-off/run2/changed_files.json` + `LLM_MODE=off PYTHONPATH=src python -m lab validate --run-dir artifacts/e2e-llm-off/run2` → 성공(E2E-LLM-OFF rerun). validate `[OK]` 통과, optional artifact 2건 warning 확인.

- `LLM_MODE=off PYTHONPATH=src python -m lab analyze --repo . --output-dir artifacts/e2e-llm-off/run3` + `LLM_MODE=off PYTHONPATH=src python -m lab diff --repo . --base HEAD~1 --head HEAD --output artifacts/e2e-llm-off/run3/changed_files.json` + `LLM_MODE=off PYTHONPATH=src python -m lab generate api --input artifacts/ir_merged.json --output artifacts/e2e-llm-off/run3/API.md` + `LLM_MODE=off PYTHONPATH=src python -m lab validate --run-dir artifacts/e2e-llm-off/run3` + `LLM_MODE=off PYTHONPATH=src python -m lab validate --run-dir artifacts/e2e-llm-off/run3 --strict` → 성공(E2E-LLM-OFF full rerun). analyze/diff/generate/validate 모두 통과, optional artifact 누락은 INFO로만 기록.

## 결정사항 / 리스크
- 결정: `generated_at_utc`는 payload에 유지하되 fingerprint 계산에서는 제외한다.
- 결정: S06은 운영 경로 오염 없이 검증하기 위해 숨김 테스트 훅을 허용한다.
- 결정: optional artifact 누락은 strict 실패 대상이 아니라 INFO로 관리한다.
- 리스크: `validate`는 구현되었지만 quality gate 전 항목(예: schema 세부 규칙/리포트 포맷 고도화)은 아직 미완이라 CI 단일 판정 기준이 더 필요하다.
- 리스크: 테스트 시 임시 로컬 브랜치/임시 repo 생성이 필요해 환경 의존성이 남아 있다.

## 다음 세션 시작 프롬프트
- STATUS.md와 AGENTS.md를 먼저 확인한 뒤 `generate spec`/`generate db-schema` 구현을 이어서 문서 생성 파이프라인을 완성해.
- fixture case(`C/M/I/E/X`)별 expected/golden 비교를 테스트 코드로 고정하고, 품질 게이트(`quality_high`)를 CI에서 fail-fast로 평가해.
