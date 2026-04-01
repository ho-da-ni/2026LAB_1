# LIMITS (W5 Mid Share)

## 현재 범위 한계

1. **Fixture 중심 탐지**
   - `detect-endpoints`는 현재 fixture 입력 기반 MVP 흐름이다.
   - 실제 Java 소스 파싱 전면 구현(프레임워크/버전별 완전 대응)은 후속 범위다.

2. **SPEC 생성의 보수적 채움**
   - `generate spec`은 변경 중심 구조를 생성하지만,
     Before/After/Contract/Impact 다수 항목은 근거 부족 시 `UNKNOWN`으로 기록한다.

3. **Quality Gate의 단계적 강화 필요**
   - W4 기준 핵심 규칙(`QR-IR-*`, `QR-API-*`, `QR-SPEC-*`)은 반영되었으나,
     전 문서/전 산출물의 세부 semantic 검사까지 완전하지 않다.

4. **데모 명령 최소화**
   - 중간공유에서는 3-command 데모로 제한해 안정성을 우선한다.
   - full E2E(분석/차이/문서/검증 전체)는 별도 리허설 트랙으로 운영한다.

## 발표 시 유의사항
- “자동화 완료”는 현재 문서/테스트에 고정된 범위 내 의미임을 명확히 안내
- `UNKNOWN`/`needs_review`는 실패가 아니라 **추정 금지 정책 준수 결과**임을 강조
- strict/non-strict 차이는 운영 정책 선택임을 예시와 함께 설명

