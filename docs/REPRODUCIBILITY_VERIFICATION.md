# 재현성 검증 절차 (2회 동일성 검정)

목적: **동일 입력 → 동일 출력**을 운영 레벨에서 검증하기 위한 표준 절차를 정의한다.

검증 대상 산출물(예시):

- `artifacts/ir_merged.json`
- `artifacts/features.json`
- `API.md` (생성본)
- `SPEC.md` (생성본)

---

## 1) 검증 정의

### 1.1 동일 입력

다음 조건이 모두 동일해야 한다.

- `base/head/merge_base`
- include/exclude 필터
- 실행 옵션/플래그
- 분석 대상 저장소 상태(working tree clean)
- 도구 버전(Python, 의존성, CLI 버전)

### 1.2 동일 출력

다음 조건을 만족해야 한다.

- JSON 산출물: 정규화 후 바이트 동일
- Markdown 산출물: trailing 공백/개행 정규화 후 바이트 동일
- 파일 목록/정렬 순서 동일

---

## 2) 사전 준비

1. 실행 환경 고정
   - Python 버전 고정
   - 의존성 lockfile 기준 설치
2. 저장소 상태 고정
   - `git status --porcelain` 결과가 비어 있어야 함
3. 실행 인자 고정
   - `base/head/include/exclude`를 run config로 고정
4. 시간 비결정성 제거
   - 가능하면 `generated_at`을 고정 또는 비교 제외 필드로 처리

---

## 3) 2회 동일성 검정 절차

## Step A) 1차 실행

- 동일 입력 조건으로 산출물 생성
- 결과를 `runA/` 디렉터리에 보관

예시 명령:

```bash
mkdir -p /tmp/repro/runA /tmp/repro/runB
# (예) 산출물 생성 후 복사
cp artifacts/ir_merged.json /tmp/repro/runA/ir_merged.json
cp artifacts/features.json /tmp/repro/runA/features.json
cp docs/API.md /tmp/repro/runA/API.md
cp docs/SPEC.md /tmp/repro/runA/SPEC.md
```

## Step B) 2차 실행

- 입력/옵션 변경 없이 동일 명령 재실행
- 결과를 `runB/` 디렉터리에 보관

```bash
cp artifacts/ir_merged.json /tmp/repro/runB/ir_merged.json
cp artifacts/features.json /tmp/repro/runB/features.json
cp docs/API.md /tmp/repro/runB/API.md
cp docs/SPEC.md /tmp/repro/runB/SPEC.md
```

## Step C) 정규화

비교 전 비결정 필드/표현 차이를 정규화한다.

- JSON: key 정렬, pretty format 통일
- Markdown: trailing 공백 제거, 파일 끝 newline 통일
- 시간 필드: 정책에 따라 고정 또는 제거

예시(JSON 정규화):

```bash
python -m json.tool /tmp/repro/runA/ir_merged.json > /tmp/repro/runA/ir_merged.norm.json
python -m json.tool /tmp/repro/runB/ir_merged.json > /tmp/repro/runB/ir_merged.norm.json
python -m json.tool /tmp/repro/runA/features.json > /tmp/repro/runA/features.norm.json
python -m json.tool /tmp/repro/runB/features.json > /tmp/repro/runB/features.norm.json
```

## Step D) 동일성 비교

### D-1 해시 비교

```bash
sha256sum /tmp/repro/runA/ir_merged.norm.json /tmp/repro/runB/ir_merged.norm.json
sha256sum /tmp/repro/runA/features.norm.json /tmp/repro/runB/features.norm.json
sha256sum /tmp/repro/runA/API.md /tmp/repro/runB/API.md
sha256sum /tmp/repro/runA/SPEC.md /tmp/repro/runB/SPEC.md
```

### D-2 diff 비교(보조)

```bash
diff -u /tmp/repro/runA/ir_merged.norm.json /tmp/repro/runB/ir_merged.norm.json
diff -u /tmp/repro/runA/features.norm.json /tmp/repro/runB/features.norm.json
diff -u /tmp/repro/runA/API.md /tmp/repro/runB/API.md
diff -u /tmp/repro/runA/SPEC.md /tmp/repro/runB/SPEC.md
```

판정:

- 해시 동일 + diff 없음 → PASS
- 하나라도 불일치 → FAIL

---

## 4) 불일치 발생 시 원인 분류

1. 시간 필드 변동 (`generated_at`)
2. 정렬/중복제거 불안정
3. 비결정 자료구조 순회(set/dict iteration)
4. 경로 정규화 미적용
5. 외부 의존성 버전 차이

조치 원칙:

- 원인을 `needs_review.reproducibility_mismatch`로 기록
- 해당 규칙 문서(`QUALITY_RULES.md`, 스키마 문서)와 구현을 함께 보정

---

## 5) CI 게이트 권장안

- PR마다 2회 실행 job을 추가한다.
- job은 `runA/runB` 산출물 해시와 diff 결과를 아티팩트로 남긴다.
- 실패 시 merge block.

권장 exit code:

- `0`: 재현성 검증 성공
- `20`: 입력 불일치로 검증 무효
- `21`: 출력 불일치(재현성 실패)

---

## 6) 기록 포맷 (run_context 연계)

재현성 검증 결과는 `run_context` 또는 별도 검증 로그에 다음 필드를 남긴다.

```json
{
  "reproducibility": {
    "mode": "two_run_identity",
    "input_fingerprint": "sha256:...",
    "runA_output_fingerprint": "sha256:...",
    "runB_output_fingerprint": "sha256:...",
    "result": "pass",
    "mismatch_targets": []
  }
}
```

---

## 7) 체크리스트

- [ ] 동일 입력 조건(base/head/options/environment) 고정
- [ ] 2회 실행 산출물 분리 보관
- [ ] JSON/Markdown 정규화 후 비교
- [ ] 해시 + diff 이중 검증
- [ ] 실패 시 원인 코드와 함께 기록
