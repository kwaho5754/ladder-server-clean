from flask import Flask, jsonify, render_template
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

# 비대칭 블럭인지 확인 (좌↔우, 홀↔짝 섞인 블럭은 False)
def is_strictly_non_mirrored(block_list):
    sides = [b[0] for b in block_list]
    parities = [b[2] for b in block_list]
    return (all(s == sides[0] for s in sides) and all(p == parities[0] for p in parities))

@app.route("/")
def index():
    return render_template("index.html")

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
        seen_blocks = set()

        # 최근 블럭 (원본 제거용 기준)
        for size in range(2, 6):
            idx = len(data) - size
            block = [convert(data[i]) for i in range(idx, len(data))]
            if not is_strictly_non_mirrored(block):
                continue
            block_str = '>'.join(block)
            seen_blocks.add(block_str)

        # 과거 블럭 중: 원본과 다르고 비대칭 유지 블럭만 예측
        for size in range(2, 6):
            for i in range(len(data) - size):
                block = [convert(data[j]) for j in range(i, i + size)]
                block_str = '>'.join(block)

                if not is_strictly_non_mirrored(block):
                    continue  # 대칭 포함된 블럭은 제외
                if block_str in seen_blocks:
                    continue  # 최근 블럭과 동일한 건 제외

                if i > 0:
                    predictions.append(convert(data[i - 1]))
                if i + size < len(data):
                    predictions.append(convert(data[i + size]))

        counter = Counter(predictions)
        top3_raw = counter.most_common(3)
        top3 = [{"value": item, "count": count} for item, count in top3_raw]

        while len(top3) < 3:
            top3.append({"value": "❌ 없음", "count": 0})

        return jsonify({
            "예측회차": int(raw_data[0]["date_round"]) + 1,
            "Top3 예측값": top3
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
