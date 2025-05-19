from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import requests
from collections import Counter
import os

app = Flask(__name__)
CORS(app)

def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

def mirror(block):
    result = []
    for b in block.split('>'):
        side = '우' if b[0] == '좌' else '좌'
        oe = '짝' if b[2] == '홀' else '홀'
        result.append(f"{side}{b[1]}{oe}")
    return '>'.join(result)

# 🔍 블럭 생성 디버그
def generate_blocks(data):
    blocks = []
    for size in range(2, 6):
        if len(data) < size:
            continue
        block_data = list(data[:size])  # 과거 기준 블럭
        block = '>'.join([convert(entry) for entry in block_data])
        print(f"[DEBUG] 생성된 블럭(size={size}): {block}")
        blocks.append((size, block))
    return blocks

# 🔍 매칭 & 예측 디버그
def find_predictions(data, blocks):
    total = len(data)
    predictions = []

    for size, block in blocks:
        variants = [block, mirror(block)]
        print(f"[DEBUG] 비교 블럭: {block} / 대칭: {variants[1]}")
        for use_block in variants:
            for i in range(total - size):
                compare = '>'.join([convert(entry) for entry in data[i:i+size]])
                if compare == use_block:
                    up = convert(data[i - 1]) if i > 0 else "❌"
                    down = convert(data[i + size]) if i + size < total else "❌"
                    print(f"[MATCH] index={i}, 매칭 블럭={use_block}, 상단={up}, 하단={down}")
                    if i > 0:
                        predictions.append(up)
                    if i + size < total:
                        predictions.append(down)

    if not predictions:
        print("[DEBUG] 예측값 없음 → ❌ 없음 3개 리턴")
        return ["❌ 없음", "❌ 없음", "❌ 없음"]

    top3 = [item for item, _ in Counter(predictions).most_common(3)]
    print(f"[RESULT] Top3 예측값: {top3}")
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

        # 🔍 recent 순서 확인
        recent = list(reversed(raw_data[-288:]))
        print(f"[DEBUG] recent[0] 회차(가장 과거): {recent[0]['date_round']}")
        print(f"[DEBUG] recent[-1] 회차(가장 최신): {recent[-1]['date_round']}")

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
