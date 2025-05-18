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
        # 최신 288줄 데이터 가져오기
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        data = response.json()
        recent_results = [item["result"] for item in data[:288]]

        def make_block_name(block):
            return "-".join(block)

        def find_matches(direction):
            predictions = []
            searched = set()
            recent_range = range(2, 7)  # 2~6줄 블럭
            for size in recent_range:
                if direction == "front":
                    target_block = recent_results[:size]
                    past_range = range(size, len(recent_results))
                else:  # "back"
                    target_block = list(reversed(recent_results[:size]))
                    past_range = range(size, len(recent_results))

                target_name = make_block_name(target_block)

                for i in past_range:
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
                            result = recent_results[upper_index]
                            predictions.append(result)
                        else:
                            predictions.append("❌ 없음")
                        break

                if len(predictions) > 0:
                    break

            if len(predictions) == 0:
                predictions.append("❌ 없음")
            return predictions

        # 앞/뒤 기준 각각 5개 예측값 확보
        front_preds = []
        back_preds = []

        while len(front_preds) < 5:
            result = find_matches("front")
            front_preds.extend(result)
            if result == ["❌ 없음"]:
                break

        while len(back_preds) < 5:
            result = find_matches("back")
            back_preds.extend(result)
            if result == ["❌ 없음"]:
                break

        while len(front_preds) < 5:
            front_preds.append("❌ 없음")
        while len(back_preds) < 5:
            back_preds.append("❌ 없음")

        return jsonify({
            "예측회차": 288 + 1,
            "앞기준 예측값": front_preds[:5],
            "뒤기준 예측값": back_preds[:5]
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
