# RUNBOOK (W5 Mid Share)

## 목적
- 2~3개 명령으로 핵심 흐름을 시연한다.
- 문서(`API.md`, `SPEC.md`, `QUALITY_RULES.md`)와 실제 CLI 결과가 어긋나지 않음을 확인한다.

## 데모 시나리오 (3 Commands)

아래 3개 명령을 순서대로 실행한다.

```bash
LLM_MODE=off PYTHONPATH=src python -m lab detect-endpoints \
  --input fixtures/controller_detection/endpoints.fixture.json \
  --case-id C001 \
  --output /tmp/lab-mid-demo/endpoints.json
```

```bash
LLM_MODE=off PYTHONPATH=src python -m lab build-w4 \
  --endpoints-input /tmp/lab-mid-demo/endpoints.json \
  --output-dir /tmp/lab-mid-demo \
  --base main --head work --merge-base UNKNOWN
```

```bash
LLM_MODE=off PYTHONPATH=src python -m lab generate api \
  --input /tmp/lab-mid-demo/ir_merged.json \
  --features /tmp/lab-mid-demo/features.json \
  --output /tmp/lab-mid-demo/API.md
```

## 기대 결과
- `/tmp/lab-mid-demo/endpoints.json` 생성
- `/tmp/lab-mid-demo/ir_merged.json`, `/tmp/lab-mid-demo/features.json` 생성
- `/tmp/lab-mid-demo/API.md` 생성
- 산출물은 JSON key 정렬/고정 순서 기반으로 재실행 diff가 최소화된다.

## 리허설 절차 (2회 반복)

### Rehearsal #1
1. 위 3개 명령 실행
2. 출력 파일 존재 확인
3. `API.md`에 `# API Overview`, `## Endpoint Index`, `## Endpoints` 섹션 존재 확인

### Rehearsal #2
1. 1~2번 명령은 1회만 수행해 입력(`ir_merged.json`, `features.json`)을 고정한다.
2. 3번 명령(`generate api`)만 2회 연속 재실행한다.
3. `sha256sum /tmp/lab-mid-demo/API.md` 값이 동일한지 확인한다.

## 장애 대응
- `git ref` 관련 실패 시: `--base/--head`를 현재 repo에 존재하는 ref로 교체
- 권한 실패 시: `/tmp/lab-mid-demo` 경로를 사용자 쓰기 가능한 경로로 변경
- 입력 JSON 오류 시: fixture JSON 유효성부터 재검증
