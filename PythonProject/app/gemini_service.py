# app/gemini_service.py
import os
import requests
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MCP_BASE = os.getenv("MCP_BASE", "http://mcp:8765")  # docker compose 서비스명 사용

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing")
genai.configure(api_key=GEMINI_API_KEY)

def call_get_multi_routes(origin, destination, waypoints=None, options=None):
    """
    MCP 서버의 툴 HTTP 프록시를 호출 (간단/안정 패턴).
    실제 fastmcp는 MCP 프로토콜이지만, 우리는 서버에 HTTP 프록시를 같이 띄워서 호출한다.
    """
    url = f"{MCP_BASE}/tools/get_multi_routes"
    payload = {
        "origin": origin,
        "destination": destination,
        "waypoints": waypoints or [],
        "options": options or {"multi": True}
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()

def plan_route_with_gemini(user_text, origin, destination, poi_summaries):
    """
    1) (필요 시) MCP 툴로 카카오 다중경로 가져오기
    2) RAG 결과(POI 요약) + 다중경로 후보를 Gemini에 넣고 최종 추천문/JSON 생성
    """
    # 다중경로 받아오기 (지금은 항상 호출, 조건부 호출로 바꿔도 됨)
    multi_routes = call_get_multi_routes(origin, destination)

    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = f"""
    사용자 의도: {user_text}
    출발지: {origin}, 도착지: {destination}

    후보 POI 요약 (RAG 결과라고 가정):
    {poi_summaries}

    아래는 카카오 내비 다중경로 후보입니다(툴 호출 결과):
    {multi_routes}

    요구사항:
    - 총 소요시간 우선, 요금은 가능한 낮게
    - 사용자 선호(관광/시민)를 반영
    - 결과는 한국어 설명 + JSON 요약을 함께 제공

    JSON 스키마 예:
    {{
      "selected":[{{"route_id":"...", "reason":"..."}}],
      "alternatives":[{{"route_id":"...", "tradeoff":"..."}}]
    }}
    """
    res = model.generate_content(prompt)
    return res.text  # 프론트에서 그대로 출력하거나, JSON 파싱해도 됨
