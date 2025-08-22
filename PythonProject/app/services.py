import os
import logging
import requests
import numpy as np
import psycopg2
import psycopg2.extras
from psycopg2 import sql

# 로깅
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 환경 변수
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

KAKAO_NAVI_API_KEY = os.environ["KAKAO_NAVI_API_KEY"]
VISIT_BUSAN_API_ENDPOINT = "https://visitbusan.net/api/your_endpoint"

def connect_to_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            database=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        logging.info("Connected to DB")
        return conn
    except Exception as e:
        logging.error(f"DB 연결 실패: {e}")
        return None

def fetch_poi_data(conn, limit=10, offset=0):
    poi_data = []
    cur = None
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = sql.SQL("""
            SELECT id, address, lat, lng, has_coords, row, embedding
            FROM places
            WHERE has_coords = true
            ORDER BY id
            LIMIT %s OFFSET %s
        """)
        cur.execute(query, (limit, offset))
        poi_data = cur.fetchall()
        logging.info(f"Fetched {len(poi_data)} POIs")
    except Exception as e:
        logging.error(f"Error fetching POIs: {e}")
    finally:
        if cur:
            cur.close()
    return poi_data

def cosine_similarity(a, b):
    a_vec, b_vec = np.array(a), np.array(b)
    if np.linalg.norm(a_vec) == 0 or np.linalg.norm(b_vec) == 0:
        return 0.0
    return float(np.dot(a_vec, b_vec) / (np.linalg.norm(a_vec) * np.linalg.norm(b_vec)))

def get_kakao_navi_route(origin, destination):
    url = "https://apis-navi.kakaomobility.com/v1/directions"
    headers = {"Authorization": f"KakaoAK {KAKAO_NAVI_API_KEY}"}
    params = {
        "origin": f"{origin[1]},{origin[0]}",       # lon,lat
        "destination": f"{destination[1]},{destination[0]}",
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["routes"][0]["summary"]
    except Exception as e:
        logging.warning(f"Kakao Navi API error: {e}")
        return None

def get_visit_busan_data(poi_id):
    url = f"{VISIT_BUSAN_API_ENDPOINT}?poi_id={poi_id}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.warning(f"Visit Busan API error for POI {poi_id}: {e}")
        return None

def generate_route_recommendations(poi_data, origin, destination, user_preferences):
    recs = []
    for poi in poi_data:
        coords = [poi["lat"], poi["lng"]]
        desc = (poi.get("row") or {}).get("description", "")
        emb = poi.get("embedding") or []

        # 현재는 자기 자신과의 유사도(1.0)인 placeholder
        sim = cosine_similarity(emb, emb)

        sum_to = get_kakao_navi_route(origin, coords)
        sum_from = get_kakao_navi_route(coords, destination)
        if not sum_to or not sum_from:
            continue

        total_dist = sum_to["distance"] + sum_from["distance"]
        total_dur = sum_to["duration"] + sum_from["duration"]

        weight = 1.0 if user_preferences == "tourist" else 1.2
        score = sim * weight

        visit_data = get_visit_busan_data(poi["id"])
        guide = {
            "tourist": "기본 관광객 안내 정보",
            "citizen": "기본 시민 안내 정보"
        }
        if visit_data:
            guide["tourist"] = visit_data.get("tourist_guide", guide["tourist"])
            guide["citizen"] = visit_data.get("citizen_guide", guide["citizen"])

        recs.append({
            "id": poi["id"],
            "address": poi["address"],
            "coords": coords,
            "description": desc,
            "similarity": sim,
            "distance": total_dist,
            "duration": total_dur,
            "score": score,
            "guide": guide
        })

    recs.sort(key=lambda x: x["score"], reverse=True)
    for idx, r in enumerate(recs, start=1):
        r["order"] = idx
    return recs
