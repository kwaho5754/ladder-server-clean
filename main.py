from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 블럭 생성 함수
def create_blocks(data, direction):
    blocks = []
    max_block_size = 6
    min_block_size = 2
    length = len(data)

    if direction == "front":
        for size in range(min_block_size, max_block_size + 1):
            block = data[-size:]
            blocks.append(("".join(block), size))
    elif direction == "back":
        for size in range(min_block_size, max_block_size + 1):
            block = [entry[-1] for entry in data[-size:]]
            blocks.append(("".join(block), size))
    return blocks

# 예측 함수
def predict_ladder():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()["rows"]

        if len(raw_data) < 288:
            return {"error": "데이터 부족"}

        data = [f"{row['start_point'][0]}{row['line_count']}{'짝' if row['odd_even'] == 'EVEN' else '홀'}" for row in raw_data]
        round_number = int(raw_data[0]["date_round"]) + 1

        candidates_front = []
        candidates_back = []

        for size in range(2, 7):
            target_block = data[-size:]
            target_name = "".join(target_block)

            # 앞 기준
            for i in range(len(data) - size):
                block = data[i:i+size]
                if "".join(block) == target_name and i > 0:
                    candidates_front.append(data[i-1])

            # 뒤 기준
            target_block_back = [d[-1] for d in data[-size:]]
            target_name_back = "".join(target_block_back)
            for i in range(len(data) - size):
                block = [d[-1] for d in data[i:i+size]]
                if "".join(block) == target_name_back and i > 0:
                    candidates_back.append(data[i-1])

            if len(candidates_front) >= 5 and len(candidates_back) >= 5:
                break

        def finalize_predictions(candidates):
            result = []
            for c in candidates:
                if c not in result:
                    result.append(c)
                if len(result) >= 5:
                    break
            while len(result) < 5:
                result.append("❌ 없음")
            return result

        front_result = finalize_predictions(candidates_front)
        back_result = finalize_predictions(candidates_back)

        return {
            "예측회차": round_number,
            "앞기준 예측값": front_result,
            "뒤기준 예측값": back_result
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
