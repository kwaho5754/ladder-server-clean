from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from collections import defaultdict

app = Flask(__name__)
CORS(app)

def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

def get_full_mirror_name(name):
    side = '우' if '좌' in name else '좌'
    count = name[1]
    oe = '홀' if '짝' in name else '짝'
    return f"{side}{count}{oe}"

def weighted_prediction(data, transform_func=None):
    weights = {2: 0.5, 3: 1.0, 4: 2.0, 5: 3.0}
    scores = defaultdict(float)

    for size in range(2, 6):
        if len(data) < size:
            continue
        block = [convert(entry) for entry in data[-size:]]
        if transform_func:
            block = [transform_func(b) for b in block]
        pattern = '>'.join(block)

        for i in reversed(range(len(data) - size)):
            past_block = [convert(entry) for entry in data[i:i + size]]
            if pattern == '>'.join(past_block):
                if i > 0:
                    scores[convert(data[i - 1])] += weights[size]
                if i + size < len(data):
                    scores[convert(data[i + size])] += weights[size]
    return scores

def top3_from_scores(score_dict):
    sorted_items = sorted(score_dict.items(), key=lambda x: -x[1])
    result = [{"value": val, "score": round(score, 2)} for val, score in sorted_items[:3]]
    while len(result) < 3:
        result.append({"value": "❌ 없음", "score": 0.0})
    return result

@app.route("/predict", methods=["GET"])
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()
        if not isinstance(raw_data, list):
            return jsonify({"error": "Invalid data format"})

        data = raw_data[-288:]
        round_num = int(raw_data[-1]["date_round"])

        origin_scores = weighted_prediction(data)
        mirror_scores = weighted_prediction(data, transform_func=get_full_mirror_name)

        return jsonify({
            "예측회차": round_num,
            "원본 Top3": top3_from_scores(origin_scores),
            "대칭 Top3": top3_from_scores(mirror_scores)
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
