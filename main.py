# ✅ 전체 수정된 main.py
from flask import Flask, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# 🔧 예측용 함수 (앞 기준만)
def predict_ladder():
    try:
        # 1. 최신 데이터 요청
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        data = response.json()

        # 2. 분석 대상 추출 (최근 288줄)
        recent_data = data[-288:]
        total_lines = len(recent_data)
        print(f"\n[디버그] 총 줄 수: {total_lines}")

        # 3. 예측 회차
        last_round = recent_data[-1]["date_round"]
        predicted_round = int(last_round) + 1

        # 4. 블럭 매칭 기반 예측값 추출
        predictions = []
        for block_size in range(2, 7):  # 2줄 ~ 6줄
            if total_lines <= block_size:
                continue

            # 4-1. 최근 블럭 생성
            recent_block = recent_data[-block_size:]
            recent_block_name = "".join([
                item["start_point"][0] + str(item["line_count"]) + item["odd_even"][0]
                for item in recent_block
            ])
            print(f"[디버그] 최근 블럭({block_size}줄): {recent_block_name}")

            # 4-2. 과거 블럭들과 비교
            for i in range(total_lines - block_size):
                past_block = recent_data[i:i + block_size]
                past_block_name = "".join([
                    item["start_point"][0] + str(item["line_count"]) + item["odd_even"][0]
                    for item in past_block
                ])
                if recent_block_name == past_block_name:
                    # 매칭되면 바로 상단 결과 추출
                    if i > 0:
                        result = recent_data[i - 1]
                        result_name = (
                            result["start_point"][0] + str(result["line_count"]) + result["odd_even"][0]
                        )
                        print(f"[매칭] 블럭({block_size}줄) 일치 → 예측값: {result_name}")
                        predictions.append(result_name)
                        break  # 한 블럭 사이즈에서 매칭되면 바로 다음 사이즈로 넘어감

        # 5. 예측 리스트 구성 (중복 허용, 없으면 없음으로 채움)
        if not predictions:
            predictions = ["❌ 없음"] * 5
        elif len(predictions) < 5:
            predictions += ["❌ 없음"] * (5 - len(predictions))

        # 6. 결과 리턴
        return {
            "예측회차": predicted_round,
            "앞기준 예측값": predictions[:5]
        }

    except Exception as e:
        return {"error": str(e)}

# ✅ API 엔드포인트
@app.route("/predict")
def predict():
    result = predict_ladder()
    return jsonify(result)

@app.route("/ping")
def ping():
    return "pong"

# ✅ 실행
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
