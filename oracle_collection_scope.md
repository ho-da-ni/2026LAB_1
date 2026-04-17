# Oracle 수집 대상/제외 범위 정의 (W6-DB-03)

## 1) 목적
W6 단계에서 Oracle 메타데이터 수집 범위를 명확히 고정해, 수집 범위 폭주를 방지하고 실행 시간/산출물 복잡도를 제어한다.

---

## 2) W6-T02 기준 원칙
- W6-T02는 **Oracle 수집 범위 규칙 정리**를 목표로 한다.
- W6 DoD는 수집 기준이 되는 **ALL_* 뷰를 명시**하는 것이다.
- W6 범위는 스키마 구조 이해(테이블/컬럼/관계/주석)에 필요한 최소 메타데이터로 한정한다.

---

## 3) W6 포함 대상(권장)

### 3.1 오브젝트/메타데이터
- tables
- columns
- PK (Primary Key)
- FK (Foreign Key)
- table comment
- column comment

### 3.2 ALL_* 뷰 매핑 (DoD 핵심)
- 테이블 목록: `ALL_TABLES`
- 컬럼 정의: `ALL_TAB_COLUMNS`
- PK/FK 제약 기본정보: `ALL_CONSTRAINTS`
- PK/FK 제약 컬럼 매핑: `ALL_CONS_COLUMNS`
- 테이블 코멘트: `ALL_TAB_COMMENTS`
- 컬럼 코멘트: `ALL_COL_COMMENTS`

> PK 식별: `ALL_CONSTRAINTS.CONSTRAINT_TYPE = 'P'`  
> FK 식별: `ALL_CONSTRAINTS.CONSTRAINT_TYPE = 'R'`

---

## 4) W6 제외 대상(권장)

### 4.1 오브젝트
- view
- index
- sequence
- trigger
- procedure/package

### 4.2 제약/부가정보
- check constraint
- unique constraint
- 통계 정보
- 권한 정보

### 4.3 제외 대상의 대표 뷰 예시
- 뷰: `ALL_VIEWS`
- 인덱스: `ALL_INDEXES`, `ALL_IND_COLUMNS`
- 시퀀스: `ALL_SEQUENCES`
- 트리거: `ALL_TRIGGERS`
- 프로시저/패키지: `ALL_PROCEDURES`, `ALL_OBJECTS`(관련 object type)
- 체크/유니크: `ALL_CONSTRAINTS`의 `CONSTRAINT_TYPE IN ('C', 'U')`
- 통계: `ALL_TAB_STATISTICS`, `ALL_IND_STATISTICS` 등
- 권한: `ALL_TAB_PRIVS`, `ALL_COL_PRIVS`, `DBA_ROLE_PRIVS` 등

---

## 5) Owner include/exclude 규칙 (DoD 핵심)

### 5.1 include 규칙
- `--owner`가 지정되면, 지정 owner 목록만 수집한다.
- 복수 owner 지정 시 OR 조건으로 처리한다.
- owner 비교는 대문자 정규화 후 수행한다.

### 5.2 exclude 규칙
- 시스템 스키마는 기본 제외한다.
- 기본 제외 목록(최소):
  - `SYS`
  - `SYSTEM`
  - `XDB`
  - `MDSYS`
  - `CTXSYS`
  - `ORDSYS`
  - `OUTLN`
  - `DBSNMP`
  - `WMSYS`
  - `APPQOSSYS`
- `--owner`로 시스템 스키마가 명시된 경우에도 W6 기본 정책은 제외 우선으로 처리한다.

### 5.3 include/exclude 충돌 처리
- 우선순위: `exclude` > `include`
- 즉, include 목록에 있어도 시스템 스키마 제외 규칙에 걸리면 수집하지 않는다.

---

## 6) 쿼리/필터 적용 기준
- 모든 ALL_* 조회에 owner 필터를 공통 적용한다.
- PK/FK 조인 시에도 owner 경계를 유지한다.
- 결과 생성 단계에서 제외 대상 오브젝트 타입이 섞이지 않도록 최종 타입 필터를 재검증한다.

예시 조건:
- `OWNER IN (:included_owners)`
- `OWNER NOT IN (:system_owners)`
- 제약 필터: `CONSTRAINT_TYPE IN ('P', 'R')`

---

## 7) DoD
- 사용할 ALL_* 뷰가 명시되어 있다.
- 포함/제외 오브젝트가 명시되어 있다.
- owner include/exclude 규칙이 명시되어 있다.

---

## 8) 검증

### 8.1 system schema 제외 확인
- 방법: owner에 `SYS`, `SYSTEM` 등을 포함해 시도하거나 전체 수집을 수행한다.
- 기대: 결과 산출물에 시스템 스키마 객체가 포함되지 않는다.

### 8.2 범위 밖 객체 미포함 확인
- 방법: 결과에 `view/index/sequence/trigger/procedure/package/check/unique/statistics/privilege` 관련 항목 존재 여부를 검사한다.
- 기대: W6 제외 대상 객체가 결과에 포함되지 않는다.
