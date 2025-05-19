from flask import Flask, jsonify
from flask_cors import CORS
import requests
from collections import Counter
import os

app = Flask(__name__)
CORS(app)

# 변환 함수: 사다리 raw 데이터 → 한글 블럭 이름
def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

# 블럭 생성
def make_block(data, start, size):
    return '>'.join([convert(data[i]) for i in range(start, start + size)])

# 중간 줄만 대칭
def make_middle_mirror_block(data, start, size):
    if size < 3:
        return None
    block = [convert(data[i]) for i in range(start, start + size)]
    mid = size // 2
    side = '우' if block[mid][0] == '좌' else '좌'
    oe = '짝' if block[mid][2] == '홀' else '홀'
    block[mid] = f"{side}{block[mid][1]}{oe}"
    return '>'.join(block)

# 양 끝만 대칭 (중간은 그대로)
def make_edge_mirror_block(data, start, size):
    block = [convert(data[i]) for i in range(start, start + size)]
    if size < 2:
        return None
    # 앞쪽
    side_f = '우' if block[0][0] == '좌' else '좌'
    oe_f = '짝' if block[0][2] == '홀' else '홀'
    block[0] = f"{side_f}{block[0][1]}{oe_f}"
    # 뒤쪽
    side_l = '우' if block[-1][0] == '좌' else '좌'
    oe_l = '짝' if block[-1][2] == '홀' else '홀'
    block[-1] = f"{side_l}{block[-1][1]}{oe_l}"
    return '>'.join(block)

@app.route("/predict")
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        raw_data = response.json()

        if not isinstance(raw_data, list) or len(raw_data) < 10:
            return jsonify({"error": "데이터 형식 또는 길이 오류"})

        data = raw_data[-288:]

        predictions = []

        # 최신 블럭들(중간 대칭, 반중간 대칭만 적용)
        latest_blocks = []
        for size in range(2, 6):
            idx = len(data) - size
            m_block = make_middle_mirror_block(data, idx, size)
            e_block = make_edge_mirror_block(data, idx, size)
            if m_block:
                latest_blocks.append(m_block)
            if e_block:
                latest_blocks.append(e_block)

        # 과거 블럭과 매칭
        for size in range(2, 6):
            for i in range(len(data) - size):
                block = make_block(data, i, size)
                if block in latest_blocks:
                    if i > 0:
                        predictions.append(convert(data[i - 1]))  # 상단
                    if i + size < len(data):
                        predictions.append(convert(data[i + size]))  # 하단

        top3 = [item for item, _ in Counter(predictions).most_common(3)]
        while len(top3) < 3:
            top3.append("❌ 없음")

        return jsonify({
            "예측회차": int(raw_data[0]["date_round"]) + 1,
            "예측값 Top3": top3
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
