import requests
import os
from collections import Counter
from flask import Flask, jsonify

app = Flask(__name__)

def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

def mirror(block):
    side = '우' if block[0] == '좌' else '좌'
    count = block[1]
    oe = '홀' if block[2] == '짝' else '짝'
    return f"{side}{count}{oe}"

def similar(block):
    side = block[0]  # 좌/우 유지
    count = block[1]
    oe = '홀' if block[2] == '짝' else '짝'
    return f"{side}{count}{oe}"

def generate_blocks(data):
    blocks = []
    for size in range(2, 6):
        if len(data) >= size:
            block = ''.join([convert(row) for row in data[-size:]])
            blocks.append((size, block))
    return blocks

def find_predictions(raw_data, blocks):
    total = len(raw_data)
    predictions = []

    for size, block in blocks:
        variants = [mirror(block), similar(block)]

        for use_block in variants:
            matched = False
            for i in range(total - size):
                compare = ''.join([convert(raw_data[i + j]) for j in range(size)])
                if compare == use_block:
                    matched = True
                    if i > 0:
                        predictions.append(convert(raw_data[i - 1]))
                    else:
                        predictions.append("❌ 없음")
                    if i + size < total:
                        predictions.append(convert(raw_data[i + size]))
                    else:
                        predictions.append("❌ 없음")
            if not matched:
                predictions.append("❌ 없음")
                predictions.append("❌ 없음")

    return predictions

@app.route("/predict")
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()

        if len(raw_data) < 10:
            return jsonify({"error": "데이터가 부족합니다"})

        last_round = int(raw_data[0]["date_round"])
        predict_round = last_round + 1

        recent = raw_data[-288:]
        blocks = generate_blocks(recent)
        predictions = find_predictions(raw_data, blocks)

        filtered = [p for p in predictions if p != "❌ 없음"]
        if len(filtered) >= 3:
            top3 = [item[0] for item in Counter(filtered).most_common(3)]
        else:
            top3 = [item[0] for item in Counter(filtered).most_common(3)]
            top3 += ["❌ 없음"] * (3 - len(top3))

        return jsonify({"round": predict_round, "top3": top3})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
