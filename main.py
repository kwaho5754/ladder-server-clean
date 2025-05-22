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
        return [{"value": "❌ 없음", "score": 0}]
    sorted_items = sorted(score_dict.items(), key=lambda x: -x[1])
    return [{"value": k, "score": v} for k, v in sorted_items[:1]]

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

        A = data[-96:]      # 최근
        B = data[-192:-96]  # 중간
        C = data[:-192]     # 과거

        result = {
            "예측회차": round_num,
            "시작방향": {
                "최근": top1(analyze_block(A, 0)),
                "중간": top1(analyze_block(B, 0)),
                "과거": top1(analyze_block(C, 0))
            },
            "줄수": {
                "최근": top1(analyze_block(A, 1)),
                "중간": top1(analyze_block(B, 1)),
                "과거": top1(analyze_block(C, 1))
            },
            "홀짝": {
                "최근": top1(analyze_block(A, 2)),
                "중간": top1(analyze_block(B, 2)),
                "과거": top1(analyze_block(C, 2))
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
