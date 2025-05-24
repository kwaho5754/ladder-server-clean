# ⬇️ main.py — 정방향 4줄 블럭 원본 매칭 기반 예측 (Top3 출력)

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

@app.route("/predict")
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        raw = requests.get(url).json()
        data = raw[-288:]
        round_num = int(raw[0]['date_round']) + 1

        recent_block = [convert(d) for d in data[-4:]]  # 최근 4줄 블럭
        all_blocks = [convert(d) for d in data]
        candidates = []

        for i in range(len(all_blocks) - 3):
            block = all_blocks[i:i+4]
            if block == recent_block:
                if i - 1 >= 0:
                    candidates.append(convert(data[i - 1]))
                if i + 4 < len(data):
                    candidates.append(convert(data[i + 4]))

        freq = Counter(candidates)
        top3 = []
        for i, (val, cnt) in enumerate(freq.most_common(3)):
            top3.append({"값": val, "횟수": cnt})
        while len(top3) < 3:
            top3.append({"값": "❌ 없음", "횟수": 0})

        return jsonify({"예측회차": round_num, "Top3": top3})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
