# ✅ 사다리 예측 시스템 - 정방향/역방향 블럭 기반 예측 정식 구현
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
        # 1. 데이터 불러오기
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()["rows"]

        # 2. 예측 회차
        latest_round = int(raw_data[0]["date_round"]) + 1

        # 3. 변환: 좌/우 + 숫자 + 홀짝 → 문자열 블럭화
        def convert(row):
            lr = "좌" if row["start_point"] == "LEFT" else "우"
            oe = "홀" if row["odd_even"] == "ODD" else "짝"
            return f"{lr}{row['line_count']}{oe}"

        recent_data = [convert(r) for r in raw_data][:288]

        # 4. 블럭 생성 함수
        def make_blocks(data, direction="front"):
            blocks = []
            for size in range(2, 7):
                if direction == "front":
                    block = data[:size]
                else:
                    block = data[-size:]
                blocks.append("".join(block))
            return blocks

        # 5. 블럭 매칭
        def match_block(blocks, full_data):
            predictions = []
            for blk in blocks:
                for i in range(288, len(full_data)):
                    for size in range(2, 7):
                        candidate = [convert(full_data[j]) for j in range(i, i + size) if j < len(full_data)]
                        if "".join(candidate) == blk:
                            if i > 0:
                                pred = convert(full_data[i - 1])
                                predictions.append(pred)
                            else:
                                predictions.append("❌ 없음")
                            break
                    if len(predictions) >= 5:
                        break
                if len(predictions) >= 5:
                    break
            while len(predictions) < 5:
                predictions.append("❌ 없음")
            return predictions

        # 6. 최종 실행
        front_blocks = make_blocks(recent_data, direction="front")
        back_blocks = make_blocks(recent_data, direction="back")
        front_preds = match_block(front_blocks, raw_data)
        back_preds = match_block(back_blocks, raw_data)

        return jsonify({
            "예측회차": latest_round,
            "앞기준 예측값": front_preds,
            "뒤기준 예측값": back_preds
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
