from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

def predict_ladder():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()["rows"]

        if len(raw_data) < 288:
            return {"error": "데이터 부족"}

        # 좌우 + 줄수 + 홀짝 문자열로 변환
        data = [f"{row['start_point'][0]}{row['line_count']}{'짝' if row['odd_even'] == 'EVEN' else '홀'}" for row in raw_data]
        round_number = int(raw_data[0]["date_round"]) + 1

        candidates = []
        for size in range(2, 7):
            target_block = data[-size:]
            target_name = "".join(target_block)

            for i in range(len(data) - size):
                block = data[i:i+size]
                if "".join(block) == target_name and i > 0:
                    candidates.append(data[i - 1])

            if len(candidates) >= 5:
                break

        result = []
        for c in candidates:
            if c not in result:
                result.append(c)
            if len(result) >= 5:
                break
        while len(result) < 5:
            result.append("❌ 없음")

        return {
            "예측회차": round_number,
            "앞기준 예측값": result
        }

    except Exception as e:
        return {"error": str(e)}

@app.route("/ping")
def ping():
    return "pong"

@app.route("/predict")
def predict():
    return jsonify(predict_ladder())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
