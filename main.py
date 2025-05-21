from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

# 완전 대칭
def get_full_mirror_name(name):
    side = '우' if '좌' in name else '좌'
    count = name[1]
    oe = '홀' if '짝' in name else '짝'
    return f"{side}{count}{oe}"

def find_prediction_by_blocksize(data, transform_func=None):
    result = {}
    for size in range(2, 6):
        if len(data) < size:
            result[f"{size}줄"] = "❌ 없음"
            continue
        block = [convert(entry) for entry in data[-size:]]
        if transform_func:
            block = [transform_func(b) for b in block]
        pattern = '>'.join(block)
        matched = False
        for i in reversed(range(len(data) - size)):
            past_block = [convert(entry) for entry in data[i:i + size]]
            past_block_str = '>'.join(past_block)
            if past_block_str == pattern:
                if i > 0:
                    result[f"{size}줄"] = convert(data[i - 1])
                elif i + size < len(data):
                    result[f"{size}줄"] = convert(data[i + size])
                else:
                    result[f"{size}줄"] = "❌ 없음"
                matched = True
                break
        if not matched:
            result[f"{size}줄"] = "❌ 없음"
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

        return jsonify({
            "예측회차": round_num,
            "원본": find_prediction_by_blocksize(data),
            "완전대칭": find_prediction_by_blocksize(data, get_full_mirror_name)
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
