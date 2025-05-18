# ✅ 사다리 예측 시스템 - main.py (정방향/역방향 블럭 기반 예측)
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
        # ✅ 데이터 불러오기
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()["rows"]
        data = [f"{row['start_point'][-1]}{row['line_count']}{'홀' if row['odd_even'] == 'ODD' else '짝'}" for row in raw_data]

        def make_blocks(data, is_reverse=False):
            """2~6줄 고정 블럭 생성"""
            blocks = []
            direction = "뒤" if is_reverse else "앞"
            length = len(data)

            for size in range(2, 7):  # 2~6줄
                for i in range(length - size + 1):
                    idx = length - i - size
                    block = data[idx:idx+size] if not is_reverse else [s[::-1] for s in data[idx:idx+size]]
                    blocks.append(("".join(block), idx))  # (블럭명, 시작위치)
            return blocks

        def find_predictions(current_blocks, all_data):
            """블럭 매칭하여 상단 결과 추출"""
            predictions = []
            seen_blocks = set()

            for blk_name, idx in current_blocks:
                if blk_name in seen_blocks:
                    continue
                seen_blocks.add(blk_name)
                for past_i in range(len(all_data) - len(blk_name)):
                    for size in range(2, 7):
                        if past_i + size >= len(all_data):
                            continue
                        candidate = all_data[past_i:past_i+size]
                        candidate_name = "".join(candidate)
                        if candidate_name == blk_name:
                            if past_i > 0:
                                predictions.append(all_data[past_i - 1])
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

        # ✅ 앞/뒤 블럭 생성
        recent_data = data[:288]
        front_blocks = make_blocks(recent_data, is_reverse=False)
        back_blocks = make_blocks(recent_data, is_reverse=True)

        # ✅ 예측값 계산
        front_preds = find_predictions(front_blocks, recent_data)
        back_preds = find_predictions(back_blocks, recent_data)

        # ✅ 예측 회차는 가장 최신 회차 + 1
        last_round = int(raw_data[0]["date_round"]) + 1

        return jsonify({
            "예측회차": last_round,
            "앞기준 예측값": front_preds,
            "뒤기준 예측값": back_preds
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
