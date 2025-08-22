# ai-api
 .gemini랑 prp는 context engineering 자동화 툴이라 무시해도 됨

 FastAPI /recommend를 호출

 요청 Json 스키마
 {
  "origin": [37.3943486341, 127.1102429320],
  "destination": [37.4019998201, 127.1086051847],
  "waypoints": [[37.3963909492,127.1134193605]],          // 선택
  "limit": 5,
  "preferences": "tourist",
  "options": {
    "priority": "RECOMMEND",
    "alternatives": true,          // ✅ 다중경로 ON
    "summary": true,
    "road_details": false,
    "avoid": ["toll","motorway"],
    "car_fuel": "GASOLINE",
    "car_type": 1,
    "car_hipass": false
  }
}
