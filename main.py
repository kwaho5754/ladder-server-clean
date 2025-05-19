from flask import Flask, jsonify
from flask_cors import CORS
import requests
from collections import defaultdict, Counter
import os

app = Flask(__name__)
CORS(app)

# 변환 함수: 사다리 raw 데이터 → 한글 블럭 이름
def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

# 블럭 생성: 특정 위치 기준 size개의 변환값 블럭 생성
def make_block(data, start, size):
    return '>'.join([convert(entry) for entry in data[start:start + size]])

@app.route("/predict")
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        raw_data = response.json()

        if not isinstance(raw_data, list) or len(raw_data) < 10:
            return jsonify({"error": "데이터 형식 또는 길이 오류"})

        data = raw_data[-288:]  # 최신순 (최근 → 과거)

        block_map = defaultdict(list)  # 블럭 → 다음 결과 리스트

        # 블럭 생성 및 매핑 (뒤에서부터 거꾸로 탐색)
        for size in range(2, 6):
            for i in reversed(range(len(data) - size - 1)):
                block = make_block(data, i, size)
                next_result = convert(data[i + size])
                block_map[block].append(next_result)

        # 가장 마지막 줄 기준 블럭 생성 (최근 데이터 맨 끝)
        predictions = []
        for size in range(2, 6):
            if len(data) < size:
                continue
            current_block = make_block(data, len(data) - size, size)
            variants = [current_block]

            for block in variants:
                if block in block_map:
                    most_common = Counter(block_map[block]).most_common(1)
                    if most_common:
                        predictions.append(most_common[0][0])

        top3 = [item for item, _ in Counter(predictions).most_common(3)]
        while len(top3) < 3:
            top3.append("❌ 없음")

        return jsonify({
            "예측회차": int(raw_data[0]["date_round"]) + 1,
            "Top3 예측값": top3
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
