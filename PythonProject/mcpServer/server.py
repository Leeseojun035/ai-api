# mcp_server/server.py
import os, requests
from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

KAKAO_NAVI_API_KEY = os.getenv("KAKAO_NAVI_API_KEY", "")
app = FastAPI(title="MCP Tool Server (Kakao Navi Waypoints)")

class MultiRoutesInput(BaseModel):
    origin: List[float]                   # [lat, lng]
    destination: List[float]              # [lat, lng]
    waypoints: Optional[List[List[float]]] = []
    options: Optional[Dict[str, Any]] = {}

def _to_xy(ll):  # [lat,lng] -> {"x": lng, "y": lat}
    return {"x": ll[1], "y": ll[0]}

def _normalize_routes(data: Dict[str, Any]) -> Dict[str, Any]:
    routes = []
    for i, r in enumerate(data.get("routes", []), start=1):
        s = r.get("summary", {})
        fare = s.get("fare", {}) if isinstance(s.get("fare", {}), dict) else {}
        routes.append({
            "id": f"r{i}",
            "summary": {
                "distance": s.get("distance", 0),
                "duration": s.get("duration", 0),
                "toll": fare.get("toll", 0)
            },
            # 필요 시 폴리라인 재구성: sections[].roads[].vertexes 사용
            "vertexes": ((r.get("sections") or [{}])[0].get("roads") or [{}])[0].get("vertexes")
        })
    return {"routes": routes, "provider": "kakao-navi"}

@app.post("/tools/get_multi_routes")
def get_multi_routes(inp: MultiRoutesInput):
    if not KAKAO_NAVI_API_KEY:
        return {"error": "missing KAKAO_NAVI_API_KEY"}

    payload: Dict[str, Any] = {
        "origin": _to_xy(inp.origin),
        "destination": _to_xy(inp.destination),
        # 기본값들: 문서 기준
        "priority":      (inp.options or {}).get("priority", "RECOMMEND"),
        "car_fuel":      (inp.options or {}).get("car_fuel", "GASOLINE"),
        "car_hipass":    (inp.options or {}).get("car_hipass", False),
        "alternatives":  (inp.options or {}).get("alternatives", True),   # 다중경로 ON
        "road_details":  (inp.options or {}).get("road_details", False),
        "summary":       (inp.options or {}).get("summary", False),
    }
    # 선택 필드
    if (inp.options or {}).get("car_type") is not None:
        payload["car_type"] = inp.options["car_type"]
    if (inp.options or {}).get("avoid"):
        # 문서 규격: 배열
        av = inp.options["avoid"]
        payload["avoid"] = av if isinstance(av, list) else str(av).split("|")
    if (inp.options or {}).get("roadevent") is not None:
        payload["roadevent"] = inp.options["roadevent"]

    # 경유지 (최대 30개, 총 거리 < 1500km 유의)
    if inp.waypoints:
        payload["waypoints"] = [ _to_xy(wp) for wp in inp.waypoints ]

    headers = {
        "Authorization": f"KakaoAK {KAKAO_NAVI_API_KEY}",
        "Content-Type": "application/json"
    }
    url = "https://apis-navi.kakaomobility.com/v1/waypoints/directions"
    r = requests.post(url, headers=headers, json=payload, timeout=10)
    r.raise_for_status()
    return _normalize_routes(r.json())
