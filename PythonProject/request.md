# 기능 요청: 부산 특화 네비게이션 및 맞춤 경로 추천 + 사용자 특화 가이드

## 🎯 목표
- 부산 지역 특징(지형·관광·상권 등)을 반영한 네비게이션 및 경로 추천 기능을 구현한다.
- 사용자(시민/여행객)별 특화 가이드(동행 루트 설명, 중간 추천지, 주의사항 등)를 포함한다.
- 내부 데이터베이스(places, spatial_ref_sys)와 벡터 유사도 검색을 활용하여 개인화된 경로 추천을 제공한다.

## 🗂️ 데이터베이스 구조
```sql
-- 장소(POI) 정보 테이블
CREATE TABLE places (
  id INTEGER,
  address TEXT,
  lat DOUBLE PRECISION,
  lng DOUBLE PRECISION,
  geom USER-DEFINED,  -- PostGIS GEOMETRY 타입
  has_coords BOOLEAN,
  row JSONB,
  filename TEXT,
  embedding VECTOR -- pgvector 확장을 통한 벡터 유사도 검색 (추가 예정)
);

-- 좌표계 정보 테이블 
CREATE TABLE spatial_ref_sys (
  srid INTEGER NOT NULL PRIMARY KEY,
  auth_name CHARACTER VARYING(256),
  auth_srid INTEGER,
  srtext CHARACTER VARYING(2048),
  proj4text CHARACTER VARYING(2048)
);
```

## 상세 요구사항
1. **경로 추천**
   - 카카오 길찾기 API 연동
   - places 테이블에서 `has_coords=true`인 POI 중 유사도 검색(embedding) 기반 경유지 추천
   - 출발지·도착지 입력 시, 부산 내 주요 관광지/맛집/공공시설 등 경유 추천
   - 추천 경유지는 거리(`lat`, `lng` 좌표 활용)·관심사·계절·시간대·실시간 이벤트 등 지역 특성 고려
   - PostGIS `geom` 컬럼을 활용한 정밀한 공간 연산

2. **사용자 맞춤 가이드**
   - 대상(시민/관광객/업무/가족/우선 교통수단 등) 선택 시 최적화된 안내 제공
   - 지형, 날씨, 인파, 접근성 등 부산 지역 상황에 맞는 안내(예: "여름 해운대 주말 인파 많음, 대체 경로 제안")
   - 추천 경로와 함께, 각 중간지별 동행가이드(설명/먹거리/주변 참고/안전 및 팁) 제시
   - places 테이블의 `row` JSONB 컬럼에서 추가 메타데이터 활용

3. **응답 및 화면**
   - 한국어 안내/추천, JSON 및 Markdown 구조로 설명
   - 지도 링크 또는 좌표/주소 포함
   - 실제 DB 구조에 맞는 응답 형식:
   ```json
   {
     "route_recommendations": [
       {
         "order": 1,
         "id": 123,
         "address": "부산광역시 수영구 광안해변로 219",
         "coords": [35.1532, 129.1183],
         "has_coords": true,
         "description": "해변 명소, 여름철 인파 많음",
         "guide": {
           "tourist": "인생샷 포인트, 근처 카페 추천",
           "citizen": "조깅 코스로 적합, 주말 주차 혼잡 주의"
         }
       }
     ]
   }
   ```

## 참고 코드 및 문서
- 카카오 길찾기 API: https://developers.kakao.com/docs/latest/ko/kakaonavi/common
- 부산 관광 정보 API: https://visitbusan.net/
- src/busan/fastmcp-gemini-bridge.py의 get_route_with_recommendations 참고

## 검증 방법
1. "부산역 → 해운대" 경로 요청 시, places 테이블에서 최소 3개 경유지 + 맞춤 설명 반환
2. `has_coords=true`인 장소만 추천 결과에 포함 확인
3. 시민·관광객·가족 등 유형별 맞춤 안내 확인
4. 부적합 경로(체증 심한, 거리 먼, 접근성 떨어짐 등) 자동 제외 또는 주의 안내
5. 응답 구조/표시 정보 유효성 테스트 (id, coords, address, description 포함)
6. PostGIS 공간 쿼리 및 pgvector 유사도 검색 정상 작동 확인

## ⚠️ 주의사항 및 고려사항

### 데이터베이스 관련
- **좌표계 일관성**: spatial_ref_sys 테이블의 SRID 설정 확인 (부산 지역: EPSG:4326 또는 EPSG:5179)
- **NULL 좌표 처리**: `has_coords=false`인 레코드는 공간 쿼리에서 제외
- **JSONB 활용**: `row` 컬럼의 구조 파악 후 추가 메타데이터 추출

### 성능 최적화
- **공간 인덱스**: `geom` 컬럼에 GIST 인덱스 필수
- **벡터 인덱싱**: embedding 컬럼 추가 시 HNSW 또는 IVFFlat 인덱스 생성
- **쿼리 최적화**: `ST_DWithin` 함수로 반경 검색 성능 향상

### 부산 지역 특성
- **지형적 특성**: 산과 바다 지형으로 직선거리와 실제거리 차이 고려
- **교통 특성**: 제한적인 지하철 노선, 버스 연계 필수
- **계절별 특성**: 여름 해수욕장, 가을 단풍 등 시즌별 인파 패턴

## 비고
- 부산 데이터 특화·실시간 추천·사용자별 안내 필요. 세부 로직/모듈은 AI/시스템이 최적 판단해서 설계 및 구현
- DB 접속 정보는 환경 변수로 관리, 보안 고려
- pgvector 확장 설치 및 embedding 컬럼 추가 작업 선행 필요
