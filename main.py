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
        # 최신 288줄 데이터 수집
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        data = response.json()
        recent_results = [item["result"] for item in data[:288]]

        def make_block_name(block):
            return "-".join(block)

        def find_top_matches(direction):
            results = []
            for size in range(2, 7):  # 2~6줄 블럭
                if direction == "front":
                    target_block = recent_results[:size]
                else:  # "back"
                    target_block = list(reversed(recent_results[:size]))
                target_name = make_block_name(target_block)

                for i in range(size, len(recent_results)):
                    if i + size > len(recent_results):
                        continue
                    if direction == "front":
                        past_block = recent_results[i:i+size]
                    else:
                        past_block = list(reversed(recent_results[i:i+size]))
                    past_name = make_block_name(past_block)
                    if past_name == target_name:
                        upper_index = i - 1
                        if upper_index >= 0:
                            results.append(recent_results[upper_index])
                        else:
                            results.append("❌ 없음")
                        break
                if results:
                    break
            if not results:
                results.append("❌ 없음")
            return results[0]

        # 앞/뒤 기준 예측값 각각 5개 확보
        front_preds, back_preds = [], []

        for _ in range(5):
            result = find_top_matches("front")
            front_preds.append(result)

        for _ in range(5):
            result = find_top_matches("back")
            back_preds.append(result)

        return jsonify({
            "예측회차": 288 + 1,
            "앞기준 예측값": front_preds,
            "뒤기준 예측값": back_preds
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
