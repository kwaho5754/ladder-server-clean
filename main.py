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

def split_components(name):
    return name[0], name[1], name[2]

def score_by_element(data, recent_len, index):
    total_counts = defaultdict(int)
    recent_counts = defaultdict(int)

    components = [split_components(convert(d)) for d in data]
    for i, comp in enumerate(components):
        key = comp[index]
        total_counts[key] += 1
        if i >= len(components) - recent_len:
            recent_counts[key] += 1

    all_keys = set(total_counts.keys()).union(set(recent_counts.keys()))
    scored = []
    for key in all_keys:
        recent = recent_counts[key]
        total = total_counts[key]
        score = round(recent * 1.0 + (total / 10) * 0.5, 2)
        scored.append({
            "value": key,
            "recent": recent,
            "total": total,
            "score": score
        })
    top = sorted(scored, key=lambda x: -x["score"])
    return top[0]

@app.route("/predict", methods=["GET"])
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()
        if not isinstance(raw_data, list):
            return jsonify({"error": "Invalid data format"})

        data = raw_data[-288:]
        round_num = int(raw_data[-1]["date_round"]) + 1

        result = {
            "예측회차": round_num,
            "예측값": {
                "시작방향": score_by_element(data, 20, 0),
                "줄수": score_by_element(data, 20, 1),
                "홀짝": score_by_element(data, 20, 2)
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
