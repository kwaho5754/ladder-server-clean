from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from collections import Counter

app = Flask(__name__)
CORS(app)

# 변환: 데이터 → 블럭 이름
def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

# 블럭 변형: 원본 → 유사1~3 (방향, 홀짝, 줄수)
def generate_variants(block):
    variants = [block]
    def flip(block):  # 방향 + 홀짝 반전
        side = '우' if block[0] == '좌' else '좌'
        count = block[1]
        oe = '홀' if block[2] == '짝' else '짝'
        return f"{side}{count}{oe}"
    def flip_oe(block):
        return block[:2] + ('홀' if block[2] == '짝' else '짝')
    def plus_count(block):
        return block[0] + str(min(int(block[1]) + 1, 5)) + block[2]
    variants.append(flip(block))
    variants.append(flip_oe(block))
    variants.append(plus_count(block))
    return variants

# 블럭 매칭 + 상하 예측값 수집
def predict_from_block(data, size):
    predictions = []
    for i in range(len(data) - size):
        block = [convert(d) for d in data[i:i+size]]
        variants = [generate_variants(b) for b in block]
        all_blocks = list(zip(*variants))  # 4개의 블럭 조합 생성

        for variant_block in all_blocks:
            for j in range(len(data) - size):
                target = [convert(d) for d in data[j:j+size]]
                if target == list(variant_block):
                    if j > 0:
                        predictions.append(convert(data[j-1]))  # 상단값
                    if j + size < len(data):
                        predictions.append(convert(data[j+size]))  # 하단값
    return predictions

# API
@app.route("/predict", methods=["GET"])
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()
        data = raw_data[-288:]
        round_num = int(raw_data[-1]['date_round']) + 1

        all_preds = []
        for size in range(2, 6):
            all_preds += predict_from_block(data, size)

        counter = Counter(all_preds)
        result = [item for item, _ in counter.most_common(9)]

        while len(result) < 9:
            result.append("❌ 없음")

        return jsonify({
            "예측회차": round_num,
            "예측값": result
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
