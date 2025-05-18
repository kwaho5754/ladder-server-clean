# ✅ 사다리 예측 시스템 - 완전 수정본 (앞/뒤 블럭 분리)
from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route("/ping")
def ping():
    return "pong"

@app.route("/predict")
def predict():
    try:
        # ✅ 최신 288줄 데이터 수집
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()["rows"]
        data = [f"{row['start_point'][-1]}{row['line_count']}{'홀' if row['odd_even'] == 'ODD' else '짝'}" for row in raw_data]
        recent_round = int(raw_data[0]["date_round"]) + 1  # 예측 회차 +1

        def make_blocks(data, direction="front"):
            blocks = []
            for size in range(2, 7):
                if direction == "front":
                    block = data[:size]
                else:
                    block = list(reversed(data[-size:]))
                blocks.append("".join(block))
            return blocks

        def find_predictions(blocks, full_data):
            results = []
            for blk in blocks:
                found = False
                for i in range(0, len(full_data) - 6):
                    for size in range(2, 7):
                        sample = full_data[i:i+size]
                        if len(sample) != len(blk):
                            continue
                        if "".join(sample) == blk:
                            if i > 0:
                                results.append(full_data[i-1])
                            else:
                                results.append("❌ 없음")
                            found = True
                            break
                    if found:
                        break
                if not found:
                    results.append("❌ 없음")
            return results[:5]

        front_blocks = make_blocks(data, direction="front")
        back_blocks = make_blocks(data, direction="back")
        front_preds = find_predictions(front_blocks, data)
        back_preds = find_predictions(back_blocks, data)

        return jsonify({
            "예측회차": recent_round,
            "앞기준 예측값": front_preds,
            "뒤기준 예측값": back_preds
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
