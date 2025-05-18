# ✅ 사다리 예측 시스템 - 정식 구조 반영 main.py
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
        recent_round = int(raw_data[0]["date_round"]) + 1  # 회차 +1 적용

        def make_blocks(data, reverse=False):
            """2~6줄 고정 블럭 생성"""
            blocks = []
            for size in range(2, 7):
                block = data[:size] if not reverse else [s[::-1] for s in data[-size:]]
                blocks.append("".join(block))
            return blocks

        def find_prediction(blocks, all_data):
            """블럭 매칭하여 상단 결과 추출"""
            results = []
            for blk in blocks:
                for i in range(len(all_data)-6):
                    for size in range(2, 7):
                        sample = all_data[i:i+size]
                        if len(sample) != len(blk): continue
                        name = "".join(sample)
                        if name == blk and i > 0:
                            results.append(all_data[i-1])
                            break
                    if len(results) == len(blocks): break
                if len(results) < len(blocks):
                    results.append("❌ 없음")
            return results[:5]

        front_blocks = make_blocks(data, reverse=False)
        back_blocks = make_blocks(data, reverse=True)
        front_preds = find_prediction(front_blocks, data)
        back_preds = find_prediction(back_blocks, data)

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
