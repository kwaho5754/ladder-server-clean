# ✅ 코드복사 버튼 누르기 쉽게 상단 고정
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
        raw_data = response.json()["rows"]
        if not raw_data or len(raw_data) < 10:
            return jsonify({"error": "데이터 부족"})

        # 🔽 데이터 변환 (가장 오래된 게 앞쪽)
        data = [
            f"{row['start_point']}{row['line_count']}{row['odd_even']}"
            for row in reversed(raw_data)
        ]
        current_round = int(raw_data[0]["date_round"]) + 1

        predictions = []

        # 🔁 블럭 크기 2~6줄 시도
        for size in range(2, 7):
            target_block = data[-size:]  # 최신 블럭
            found = False

            # 🔁 과거에서 일치하는 블럭 찾기
            for i in range(len(data) - size - 1, 0, -1):  # -1은 result 때문에
                compare_block = data[i:i+size]
                if compare_block == target_block:
                    result = data[i - 1] if i - 1 >= 0 else "❌ 없음"
                    predictions.append(result)
                    found = True
                    break

            if not found:
                predictions.append("❌ 없음")

        return jsonify({
            "예측회차": current_round,
            "앞기준 예측값": predictions[:5]  # 총 5개만 출력
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
