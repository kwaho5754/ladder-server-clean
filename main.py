from flask import Flask, jsonify
from flask_cors import CORS
import requests
from collections import Counter
import os

app = Flask(__name__)
CORS(app)

# 원본 블럭 → 좌3짝 형태
def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

# 홀짝 흐름 블럭 → 홀 > 짝 > 홀
def make_odd_even_block(data, start, size):
    return '>'.join([
        '짝' if data[i]['odd_even'] == 'EVEN' else '홀'
        for i in range(start, start + size)
    ])

# 구조 반복 블럭 → 방향 흐름 or 좌3 > 우4 > 좌3
def make_direction_pattern_block(data, start, size):
    return '>'.join([
        '좌' if data[i]['start_point'] == 'LEFT' else '우'
        for i in range(start, start + size)
    ])

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

        # 최신 블럭 준비 (홀짝 흐름 + 방향 흐름)
        latest_blocks = []
        for size in range(2, 6):
            idx = len(data) - size
            oe_block = make_odd_even_block(data, idx, size)
            dir_block = make_direction_pattern_block(data, idx, size)
            latest_blocks.extend([oe_block, dir_block])

        # 과거 블럭 탐색 (정방향)
        for size in range(2, 6):
            for i in range(len(data) - size):
                oe_block = make_odd_even_block(data, i, size)
                dir_block = make_direction_pattern_block(data, i, size)

                for block in [oe_block, dir_block]:
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
