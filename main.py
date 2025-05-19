from flask import Flask, jsonify, send_from_directory
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

# 대칭 블럭: 좌우 + 홀짝 반전
def mirror(block):
    result = []
    for b in block.split('>'):
        side = '우' if b[0] == '좌' else '좌'
        oe = '짝' if b[2] == '홀' else '홀'
        result.append(f"{side}{b[1]}{oe}")
    return '>'.join(result)

# ✅ 블럭 생성: 최근 N줄 → 순서를 reversed() 해서 과거→최근 순으로 블럭 생성
def generate_blocks(data):
    blocks = []
    for size in range(2, 6):
        if len(data) < size:
            continue
        block_data = list(reversed(data[-size:]))  # ← 여기만 바뀜
        block = '>'.join([convert(entry) for entry in block_data])
        blocks.append((size, block))
    return blocks

# 전체 매칭 스캔 방식 → 상단/하단 예측값 전부 수집 → 빈도 기반 Top3 선택
def find_predictions(data, blocks):
    total = len(data)
    predictions = []

    for size, block in blocks:
        variants = [block, mirror(block)]  # 원본 + 대칭

        for use_block in variants:
            for i in range(total - size):  # 과거 → 최근 방향
                compare = '>'.join([convert(entry) for entry in data[i:i+size]])
                if compare == use_block:
                    if i > 0:
                        predictions.append(convert(data[i - 1]))  # 상단
                    if i + size < total:
                        predictions.append(convert(data[i + size]))  # 하단

    if not predictions:
        return ["❌ 없음", "❌ 없음", "❌ 없음"]

    top3 = [item for item, _ in Counter(predictions).most_common(3)]
    while len(top3) < 3:
        top3.append("❌ 없음")
    return top3

@app.route("/")
def root():
    return send_from_directory('.', 'index.html')

@app.route("/predict")
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        raw_data = response.json()

        if not isinstance(raw_data, list):
            return jsonify({"error": "Invalid data format"})

        if len(raw_data) < 3:
            return jsonify({"error": "데이터가 부족합니다"})

        last_round = int(raw_data[0]["date_round"])
        predict_round = last_round + 1

        recent = raw_data[-288:]
        blocks = generate_blocks(recent)
        top3 = find_predictions(recent, blocks)

        return jsonify({
            "예측회차": predict_round,
            "예측값 Top3": top3
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
