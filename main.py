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

def mirror_component(c, mode):
    if mode == 'side':
        return '우' if c == '좌' else '좌'
    elif mode == 'oe':
        return '짝' if c == '홀' else '홀'
    return c

def analyze_component_blocks(data, mode, apply_mirror=False):
    weights = {3: 1.0, 4: 1.5, 5: 2.0, 6: 2.5, 7: 3.0}
    scores = defaultdict(float)

    components = []
    for entry in data:
        full = convert(entry)
        side, count, oe = split_components(full)
        val = side if mode == 'side' else oe
        if apply_mirror:
            val = mirror_component(val, mode)
        components.append(val)

    for size in range(3, 8):
        if len(components) < size:
            continue
        recent_block = components[-size:]
        pattern = '>'.join(recent_block)

        for i in range(len(components) - size):
            past_block = components[i:i+size]
            if pattern == '>'.join(past_block):
                weight = weights[size]
                if i > 0:
                    val = components[i-1]
                    if apply_mirror:
                        val = mirror_component(val, mode)
                    scores[val] += weight / 2
                if i + size < len(components):
                    val = components[i+size]
                    if apply_mirror:
                        val = mirror_component(val, mode)
                    scores[val] += weight / 2

    return scores

def top_elements(score_dict):
    sorted_items = sorted(score_dict.items(), key=lambda x: -x[1])
    return [{"value": k, "score": round(v, 2)} for k, v in sorted_items[:3]]

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

        result = {
            "예측회차": round_num,
            "시작방향 원본": top_elements(analyze_component_blocks(data, 'side', apply_mirror=False)),
            "시작방향 대칭": top_elements(analyze_component_blocks(data, 'side', apply_mirror=True)),
            "홀짝 원본": top_elements(analyze_component_blocks(data, 'oe', apply_mirror=False)),
            "홀짝 대칭": top_elements(analyze_component_blocks(data, 'oe', apply_mirror=True))
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
