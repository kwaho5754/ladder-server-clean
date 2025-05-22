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

def analyze_block(data, target_index):
    counts = defaultdict(int)
    for entry in data:
        side, count, oe = split_components(convert(entry))
        key = (side, count, oe)[target_index]
        counts[key] += 1
    return counts

def top1(score_dict):
    if not score_dict:
        return "❌ 없음"
    return max(score_dict.items(), key=lambda x: x[1])[0]

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

        start = top1(analyze_block(data, 0))  # 시작방향
        count = top1(analyze_block(data, 1))  # 줄수
        oe = top1(analyze_block(data, 2))     # 홀짝

        result = {
            "예측회차": round_num,
            "예측값": {
                "시작방향": start,
                "줄수": count,
                "홀짝": oe
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
