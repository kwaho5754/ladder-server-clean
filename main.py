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

# 유사 대칭 블럭: 홀짝만 반전 (좌우는 유지)
def similar(block):
    result = []
    for b in block.split('>'):
        side = b[0]
        oe = '짝' if b[2] == '홀' else '홀'
        result.append(f"{side}{b[1]}{oe}")
    return '>'.join(result)

# 최근 블럭 리스트 생성 (2~5줄)
def generate_blocks(data):
    blocks = []
    for size in range(2, 6):
        if len(data) < size:
            continue
        block = '>'.join([convert(entry) for entry in data[-size:]])
        blocks.append((size, block))
    return blocks

# 예측값 추출 함수 (블럭당 상단/하단 2개씩)
def find_predictions(data, blocks):
    total = len(data)
    predictions = []

    for size, block in blocks:
        variants = [mirror(block), similar(block)]

        for use_block in variants:
            for i in range(total - size):
                compare = '>'.join([convert(entry) for entry in data[i:i+size]])
                if compare == use_block:
                    if i > 0:
                        predictions.append(convert(data[i - 1]))  # 상단
                    if i + size < total:
                        predictions.append(convert(data[i + size]))  # 하단
                    break
            else:
                predictions.append("❌ 없음")
                predictions.append("❌ 없음")

    return predictions

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

        # 최근 확정된 회차를 기준으로 예측 회차 계산
        confirmed = [entry for entry in raw_data if entry.get("result")]
        if not confirmed:
            return jsonify({"error": "확정된 회차 정보가 없습니다"})

        last_round = int(confirmed[-1]["date_round"])
        predict_round = last_round + 1

        recent = raw_data[-288:]
        blocks = generate_blocks(recent)
        predictions = find_predictions(recent, blocks)

        filtered = [p for p in predictions if p != "❌ 없음"]
        top3 = [item for item, _ in Counter(filtered).most_common(3)]

        while len(top3) < 3:
            top3.append("❌ 없음")

        return jsonify({
            "예측회차": predict_round,
            "예측값 Top3": top3
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
