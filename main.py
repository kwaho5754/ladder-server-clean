from flask import Flask, jsonify, render_template
from flask_cors import CORS
import requests
from collections import Counter
import os

app = Flask(__name__)
CORS(app)

def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

# 대칭 변환: 좌↔우, 홀↔짝
def mirror(block):
    result = []
    for b in block.split('>'):
        side = '우' if b[0] == '좌' else '좌'
        oe = '홀' if b[2] == '짝' else '짝'
        result.append(f"{side}{b[1]}{oe}")
    return '>'.join(result)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict")
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        raw_data = response.json()

        if not isinstance(raw_data, list) or len(raw_data) < 10:
            return jsonify({"error": "데이터 형식 또는 길이 오류"})

        data = raw_data[-288:]
        predictions = []

        # 역방향 블럭 생성 (과거 → 미래 방향)
        for size in range(2, 6):
            for i in range(len(data) - size - 1):  # 마지막 줄은 예측값이 없으므로 -1
                block = [convert(data[j]) for j in range(i, i + size)]
                block_str = '>'.join(block)
                block_mirror = mirror(block_str)

                # 미래에서 이 블럭이 등장하는지 찾기
                for k in range(i + 1, len(data) - size):
                    future_block = [convert(data[j]) for j in range(k, k + size)]
                    future_block_str = '>'.join(future_block)

                    if future_block_str == block_str or future_block_str == block_mirror:
                        # 일치한 경우 → 해당 블럭의 **다음 줄**을 예측값으로 채택
                        if k + size < len(data):
                            predictions.append(convert(data[k + size]))

        counter = Counter(predictions)
        top3_raw = counter.most_common(3)
        top3 = [{"value": item, "count": count} for item, count in top3_raw]

        while len(top3) < 3:
            top3.append({"value": "❌ 없음", "count": 0})

        return jsonify({
            "예측회차": int(raw_data[0]["date_round"]) + 1,
            "Top3 예측값": top3
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
