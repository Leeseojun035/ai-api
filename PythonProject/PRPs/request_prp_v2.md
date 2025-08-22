# Product Requirements Prompt (PRP)
## 1. Overview
- **Feature Name:** Route Recommendation Enhancement with Spatial Data and Kakao Navi Integration

- **Objective:** Enhance the existing route recommendation system by incorporating spatial data (PostGIS geometries, pgvector embeddings) and integrating with external APIs (Kakao Navi, Visit Busan) to provide more accurate and context-aware route recommendations.

- **Why:** To provide users with enriched route recommendations that consider spatial information, points of interest (POIs) with coordinate data, and external API data for a more comprehensive and personalized travel experience. This addresses the problem of limited contextual information in the current route recommendation system.

## 2. Success Criteria
_This feature will be considered complete when the following conditions are met. These must be specific and measurable._

- [ ] The code runs without errors.

- [ ] All new unit tests pass.

- [ ] The feature meets all functional requirements described below.

- [ ] The code adheres to the project standards defined in `GEMINI.md`.

## 3. Context & Resources
_This section contains all the information needed to implement the feature correctly._

### ?? External Documentation:
_List any URLs for libraries, APIs, or tutorials._

- **Resource:** https://developers.kakao.com/docs/latest/ko/kakaonavi/common

   - **Purpose:** For integrating with the Kakao Navi API for route optimization and directions.

- **Resource:** https://visitbusan.net/

   - **Purpose:** For fetching additional POI data and context for route recommendations.

### ?? Internal Codebase Patterns:
_List any existing files or code snippets from this project that should be used as a pattern or inspiration._

- **File:** `src/busan/fastmcp-gemini-bridge.py`

 - **Reason:**  Use `get_route_with_recommendations` as a reference for structuring the route recommendation logic and API integration.

### ?? Known Pitfalls:
_List any critical warnings, rate limits, or tricky logic to be aware of._

- **Spatial Reference Systems:** Ensure proper SRID handling (e.g., EPSG:4326 or EPSG:5179) when working with PostGIS geometries, particularly when converting between different coordinate systems.
- **Null Coordinate Values:**  Handle cases where `has_coords=false` gracefully, as these POIs will not have associated coordinate data.
- **JSONB Data Handling:** Be mindful of the schema and content within the `row` JSONB column in the `places` table and ensure robust parsing and error handling when extracting data.
- **Rate Limiting**: Be aware of and handle potential rate limits on the Kakao Navi and Visit Busan APIs.

## 4. Implementation Blueprint
_This is the step-by-step plan for building the feature._

### Proposed File Structure:
_Show the desired directory tree, highlighting new or modified files._

```
src/
    busan/
        route_enhancements.py  (new)
        __init__.py
tests/
    busan/
        test_route_enhancements.py (new)
```

### Task Breakdown:
_Break the implementation into a sequence of logical tasks._

**Task 1: Data Retrieval and Preparation**

- Fetch POI data from the `places` table where `has_coords=true`.
- Implement functions to retrieve data from the Kakao Navi and Visit Busan APIs.
- Handle API authentication and error responses gracefully.
- Convert geographical coordinates to the appropriate Spatial Reference System (SRS).

**Task 2: Route Recommendation Logic**

- Implement the core logic for generating route recommendations based on user preferences (e.g., tourist, citizen).
- Utilize PostGIS functions (e.g., `ST_DWithin`) for spatial proximity calculations to find nearby POIs.
- Leverage pgvector embeddings to find similar POIs based on content and characteristics.
- Incorporate data from the `row` JSONB column in the `places` table to enhance recommendations with additional information (e.g., descriptions, guides).

**Task 3: Data Transformation and Output Formatting**

- Format the route recommendations into a JSON structure that includes information about the POIs (id, coords, address, description).
- Generate a Markdown representation of the route recommendations for easy readability.
- Implement error handling and logging for debugging and monitoring.

**Task 4: API Integration**

- Modify the existing `get_route_with_recommendations` function (if necessary) to incorporate the new route enhancement logic.
- Ensure compatibility with existing API endpoints and data formats.

## 5. Validation Plan
_How we will verify the implementation is correct._

### Unit Tests:
_Describe the specific test cases that need to be created._

- `test_fetch_poi_data():` Verifies that POI data is fetched correctly from the `places` table, specifically when `has_coords=true`.

- `test_kakao_api_integration():` Tests the integration with the Kakao Navi API and verifies that route optimization is working as expected. (mock the external API response)

- `test_spatial_proximity_calculation():` Validates that spatial proximity calculations using PostGIS functions are accurate.

- `test_embedding_similarity_search():` Checks that the pgvector embedding similarity search is returning relevant POIs.

- `test_jsonb_data_extraction():` Ensures that data is extracted correctly from the `row` JSONB column.

- `test_route_recommendation_generation():` Verifies that the route recommendation logic is generating accurate and relevant recommendations.

**Manual Test Command:**  
_Provide a simple command to run to see the feature in action._
```
python src/busan/fastmcp-gemini-bridge.py --location "부산역" --poi_count 3
```
**Expected Output:**
```json
{
  "route_recommendations": [
    {
      "order": 1,
      "id": 123,
      "address": "초량동 219",
      "coords": [35.1532, 129.1183],
      "has_coords": true,
      "description": "부산역 근처 관광 명소, 맛집",
      "guide": {
        "tourist": "부산 관광객, 꼭 가봐야 할 곳",
        "citizen": "동네 주민 추천, 숨겨진 맛집"
      }
    },
    {
          "order": 2,
          "id": 456,
          "address": "중앙동 100",
          "coords": [35.1432, 129.0183],
          "has_coords": true,
          "description": "남포동 영화 거리, 맛집",
          "guide": {
            "tourist": "영화 마니아 추천, 명작 상영",
            "citizen": "숨겨진 골목 맛집, 현지인 추천"
          }
    },
    {
          "order": 3,
          "id": 789,
          "address": "해운대 50",
          "coords": [35.1632, 129.1283],
          "has_coords": true,
          "description": "해운대 해수욕장 근처 맛집",
          "guide": {
            "tourist": "싱싱한 해산물, 바다 뷰 레스토랑",
            "citizen": "해운대 주민 추천, 가성비 맛집"
          }
        }
  ]
}
```
