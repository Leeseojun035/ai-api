# app/routes.py
from fastapi import APIRouter, HTTPException
from app.models import RecommendRequest
from app.services import connect_to_db, fetch_poi_data
from app.gemini_service import plan_route_with_gemini

router = APIRouter()

@router.post("/recommend")
def recommend(req: RecommendRequest):
    # 1) DB에서 POI 후보/요약 (간단 예: 앞 N개만)
    conn = connect_to_db()
    if not conn:
        raise HTTPException(status_code=500, detail="DB 연결 실패")
    try:
        pois = fetch_poi_data(conn, limit=req.limit)
    finally:
        conn.close()

    # 2) 간단한 POI 요약 문자열 (초기엔 하드 요약, 나중에 RAG로 교체)
    summaries = "\n".join([
        f"- {p['address']} ({p['lat']},{p['lng']}): { (p.get('row') or {}).get('description','') }"
        for p in pois
    ])

    # 3) Gemini에게 최종 플래닝 요청 (내부에서 MCP 툴 호출)
    result_text = plan_route_with_gemini(
        user_text=f"preferences={req.preferences}",
        origin=req.origin,
        destination=req.destination,
        poi_summaries=summaries
    )

    return {"result": result_text}
