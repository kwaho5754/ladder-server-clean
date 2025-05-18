from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route("/predict")
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        data = response.json()

        rows = [
            f"{item['start_point'][0]}{item['line_count']}{item['odd_even'][0]}"
            for item in data
        ]

        rows.reverse()
        latest_index = len(rows) - 1
        all_blocks = {}
        prediction = []

        print(f"[디버그] 총 줄 수: {len(rows)}")

        for block_size in range(2, 7):
            recent_block = ''.join(rows[-block_size:])
            print(f"[디버그] 최근 블럭({block_size}줄): {recent_block}")

            for i in range(0, len(rows) - block_size):
                block = ''.join(rows[i:i + block_size])
                if block == recent_block:
                    if i > 0:
                        result = rows[i - 1]
                        prediction.append(result)
                        print(f"[매칭] {block_size}줄 블럭 일치 → 예측값: {result}")
                        break
                    else:
                        print(f"[주의] 블럭은 일치했으나 상단 결과 없음")
            if len(prediction) >= 5:
                break

        while len(prediction) < 5:
            prediction.append("❌ 없음")

        return jsonify({
            "예측회차": latest_index + 1,
            "앞기준 예측값": prediction[:5]
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
