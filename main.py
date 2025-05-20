from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from collections import Counter

app = Flask(__name__)
CORS(app)

def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

def get_mirror_name(name):
    table = str.maketrans("좌우", "우좌")
    return name.translate(table)

@app.route("/predict", methods=["GET"])
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()

        if not isinstance(raw_data, list):
            return jsonify({"error": "Invalid data format"})

        data = raw_data[-288:]
        predictions = []

        # 최근 블럭 2~5줄 생성 후 각 블럭/대칭 블럭으로 과거 비교
        for size in range(2, 6):
            if len(data) < size:
                continue

            block = [convert(entry) for entry in data[-size:]]
            block_str = '>'.join(block)

            mirror_block = [get_mirror_name(b) for b in block]
            mirror_block_str = '>'.join(mirror_block)

            for pattern in [block_str, mirror_block_str]:
                for i in reversed(range(len(data) - size)):
                    past_block = [convert(entry) for entry in data[i:i + size]]
                    past_block_str = '>'.join(past_block)

                    if pattern == past_block_str:
                        if i > 0:
                            predictions.append(convert(data[i - 1]))  # 상단
                        if i + size < len(data):
                            predictions.append(convert(data[i + size]))  # 하단

        if not predictions:
            return jsonify({
                "예측회차": int(raw_data[-1]["date_round"]),
                "Top3 예측값": [{"value": "❌ 없음", "count": 0} for _ in range(3)]
            })

        counter = Counter(predictions)
        top3_raw = counter.most_common(3)
        top3 = [{"value": item, "count": count} for item, count in top3_raw]

        while len(top3) < 3:
            top3.append({"value": "❌ 없음", "count": 0})

        return jsonify({
            "예측회차": int(raw_data[-1]["date_round"]),
            "Top3 예측값": top3
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
