from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 🔧 블럭 생성 함수
def create_block(lines):
    return ",".join([f"{line['start_point']}{line['line_count']}{line['odd_even']}" for line in lines])

# 🔍 블럭 매칭 함수
def find_prediction_blocks(direction):
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        res = requests.get(url)
        data = res.json()

        recent_results = data[-288:]  # 분석 범위: 최근 288줄
        predictions = []

        for size in range(2, 7):
            if direction == "front":
                target_block = recent_results[:size]  # 앞 기준: 위에서부터 size개
            else:
                target_block = recent_results[-size:]  # 뒤 기준: 아래서부터 size개

            target_block_str = create_block(target_block)

            for i in range(size, len(recent_results)):
                if direction == "front":
                    past_block = recent_results[i:i+size]
                    if i + size >= len(recent_results):
                        break
                    upper_line = recent_results[i - 1]  # 매칭된 블럭 위쪽 줄
                else:
                    past_block = recent_results[i:i+size]
                    if i + size >= len(recent_results):
                        break
                    upper_line = recent_results[i - 1]  # 동일하게 상단값

                if create_block(past_block) == target_block_str:
                    predictions.append(f"{upper_line['start_point']}{upper_line['line_count']}{upper_line['odd_even']}")
                    break
            else:
                predictions.append("❌ 없음")

        return predictions[:5]

    except Exception as e:
        return ["❌ 오류"]

# ✅ /ping
@app.route("/ping")
def ping():
    return "pong"

# ✅ /predict
@app.route("/predict")
def predict():
    front_result = find_prediction_blocks("front")
    back_result = find_prediction_blocks("back")
    round_number = 288 - 120  # 예시 회차

    return jsonify({
        "예측회차": round_number,
        "앞 기준 예측값": front_result,
        "뒤 기준 예측값": back_result
    })

# 🚀 서버 실행
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
