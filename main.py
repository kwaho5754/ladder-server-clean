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

# 대칭 변환
def mirror_block(block):
    mirrored = []
    for b in block.split('>'):
        side = '우' if b[0] == '좌' else '좌'
        oe = '짝' if b[2] == '홀' else '홀'
        mirrored.append(f"{side}{b[1]}{oe}")
    return '>'.join(mirrored)

@app.route("/predict")
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        raw_data = response.json()

        if not isinstance(raw_data, list) or len(raw_data) < 10:
            return jsonify({"error": "데이터 형식 또는 길이 오류"})

        data = raw_data[-288:]  # 최신 288줄

        predictions = []

        # 최신 블럭들(원본 + 대칭) 준비
        latest_blocks = []
        for size in range(2, 6):
            if len(data) >= size:
                latest = make_block(data, len(data) - size, size)
                latest_blocks.append(latest)
                latest_blocks.append(mirror_block(latest))

        # 과거부터 정방향 순회하며 블럭 생성 및 매칭
        for size in range(2, 6):
            for i in range(len(data) - size):
                block = make_block(data, i, size)
                if block in latest_blocks:
                    # 상단값
                    if i > 0:
                        predictions.append(convert(data[i - 1]))
                    # 하단값
                    if i + size < len(data):
                        predictions.append(convert(data[i + size]))

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
