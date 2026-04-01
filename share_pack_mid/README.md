# share_pack_mid

중간공유용 패키지 구성(초안)이다. 본 디렉터리는 **발표/리허설에서 실제로 바로 열어볼 파일 목록**을 고정한다.

## 포함 자산(고정)

1. 핵심 문서
   - `README.md`
   - `RUNBOOK.md`
   - `LIMITS.md`
   - `status.md`
2. 규칙/스키마 문서
   - `docs/API.md`
   - `docs/SPEC.md`
   - `docs/QUALITY_RULES.md`
   - `docs/REPO_META_SCHEMA.md`
   - `docs/CHANGED_FILES_SCHEMA.md`
3. 데모 입력/기대값
   - `fixtures/controller_detection/endpoints.fixture.json`
   - `fixtures/controller_detection/golden_snapshots.json`
   - `fixtures/controller_detection/quality_gate_report.json`
4. 구현 코드(핵심 경로)
   - `src/lab/cli.py`
   - `src/lab/controller_detection.py`
5. 샘플 산출물
   - `artifacts/ir_merged.json`
   - `artifacts/features.json`

## 패키징 예시

```bash
tar -czf share_pack_mid.tgz \
  README.md RUNBOOK.md LIMITS.md status.md \
  docs/API.md docs/SPEC.md docs/QUALITY_RULES.md docs/REPO_META_SCHEMA.md docs/CHANGED_FILES_SCHEMA.md \
  fixtures/controller_detection/endpoints.fixture.json \
  fixtures/controller_detection/golden_snapshots.json \
  fixtures/controller_detection/quality_gate_report.json \
  src/lab/cli.py src/lab/controller_detection.py \
  artifacts/ir_merged.json artifacts/features.json \
  share_pack_mid/README.md
```

