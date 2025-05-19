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

@app.route("/sliding_predict")
def sliding_predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        raw_data = response.json()

        if not isinstance(raw_data, list) or len(raw_data) < 10:
            return jsonify({"error": "데이터 형식 또는 길이 오류"})

        data = list(reversed(raw_data[-288:]))  # 과거 → 최근 순서

        block_map = defaultdict(list)  # 블러그 → 다음 경기 결과

        # 플러그 다양화: 각 경기차가 다음과 어떻게 연결되는가
        for size in range(2, 6):  # 2~5줄 블러그
            for i in range(len(data) - size - 1):
                block = make_block(data, i, size)
                next_result = convert(data[i + size])
                block_map[block].append(next_result)

        # 가장 최근 블러그 하나 생성 후 예측
        predictions = []
        for size in range(2, 6):
            if len(data) < size:
                continue
            current_block = make_block(data, -size, size)
            variants = [current_block, ]  # 현재의 블러그 바로 해석

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
            "Top3 예측값 (sliding)": top3
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
