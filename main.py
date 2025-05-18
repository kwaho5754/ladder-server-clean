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
        data = response.json()[:288]

        def convert(row):
            lr = '좌' if row['start_point'] == 'LEFT' else '우'
            odd = '홀' if row['odd_even'] == 'ODD' else '짝'
            return f"{lr}{row['line_count']}{odd}"

        recent_results = [convert(row) for row in data]

        def make_block_name(block):
            return "-".join(block)

        def find_prediction_blocks(direction):
            results = []
            for size in range(2, 7):
                if direction == "front":
                    target_block = recent_results[:size]
                else:  # back
                    target_block = list(reversed(recent_results[:size]))

                target_name = make_block_name(target_block)

                for i in range(size, len(recent_results)):
                    if i + size > len(recent_results):
                        continue

                    if direction == "front":
                        past_block = recent_results[i:i+size]
                    else:
                        past_block = list(reversed(recent_results[i:i+size]))

                    if make_block_name(past_block) == target_name:
                        upper_index = i - 1
                        if upper_index >= 0:
                            results.append(recent_results[upper_index])
                        else:
                            results.append("❌ 없음")
                        break

                if len(results) >= 5:
                    break

            while len(results) < 5:
                results.append("❌ 없음")

            return results[:5]

        front_preds = find_prediction_blocks("front")
        back_preds = find_prediction_blocks("back")

        return jsonify({
            "예측회차": data[0].get("date_round", "없음"),
            "앞기준 예측값": front_preds,
            "뒤기준 예측값": back_preds
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
