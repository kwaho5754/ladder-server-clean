from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 🔧 블럭 문자열 변환 함수 (예: 좌4짝 → L4E)
def convert(entry):
    start = 'L' if entry['start_point'] == 'LEFT' else 'R'
    count = str(entry['line_count'])
    oe = 'E' if entry['odd_even'] == 'EVEN' else 'O'
    return f"{start}{count}{oe}"

# 🔧 블럭 문자열 → 한글 변환 함수
def to_korean(block_code):
    if block_code == "❌ 없음":
        return "❌ 없음"
    start = "좌" if block_code[0] == "L" else "우"
    count = block_code[1]
    oe = "짝" if block_code[2] == "E" else "홀"
    return f"{start}{count}{oe}"

# 🔍 앞 기준 예측 함수
def predict_forward(data):
    recent = data[-288:]
    total = len(recent)
    predictions = []

    print(f"[디버그] 총 줄 수: {total}")

    for size in range(2, 7):
        if total <= size:
            continue
        recent_block = ''.join([convert(entry) for entry in recent[-size:]])
        print(f"[디버그] 최근 블럭({size}줄): {recent_block}")

        for i in range(total - size):
            past_block = ''.join([convert(entry) for entry in recent[i:i + size]])
            if recent_block == past_block and i > 0:
                result = convert(recent[i - 1])
                predictions.append(result)
                print(f"[매칭] 블럭({size}줄) 일치 → 예측값: {result}")
                break
        else:
            predictions.append("❌ 없음")
            print(f"[미매칭] 블럭({size}줄) → 예측값 없음")

    return predictions[:5]

# 📡 API
@app.route("/predict", methods=["GET"])
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()

        if not isinstance(raw_data, list):
            return jsonify({"error": "Invalid data format"})

        predictions = predict_forward(raw_data)
       round_number = int(raw_data[0]["date_round"]) + 1

        return jsonify({
            "예측회차": round_number,
            "앞기준 예측값": [to_korean(p) for p in predictions]
        })

    except Exception as e:
        return jsonify({"error": str(e)})

# 🟢 실행
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
