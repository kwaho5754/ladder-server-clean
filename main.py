from flask import Flask, jsonify, render_template
from flask_cors import CORS
import requests
from collections import Counter
import os

app = Flask(__name__)
CORS(app)

# 결과를 한글 블럭명으로 변환
def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

# 대칭 변환
def mirror(block):
    result = []
    for b in block.split('>'):
        side = '우' if b[0] == '좌' else '좌'
        oe = '짝' if b[2] == '홀' else '홀'
        result.append(f"{side}{b[1]}{oe}")
    return '>'.join(result)

# 구조 반복 (좌우 흐름만)
def make_direction_pattern_block(data, start, size):
    return '>'.join([
        '좌' if data[i]['start_point'] == 'LEFT' else '우'
        for i in range(start, start + size)
    ])

# 중간 대칭 블럭 (중간 줄만 반전)
def make_middle_mirror_block(data, start, size):
    if size < 3:
        return None
    block = [convert(data[i]) for i in range(start, start + size)]
    mid = size // 2
    side = '우' if block[mid][0] == '좌' else '좌'
    oe = '짝' if block[mid][2] == '홀' else '홀'
    block[mid] = f"{side}{block[mid][1]}{oe}"
    return '>'.join(block)

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
        latest_blocks = []

        for size in range(2, 6):
            idx = len(data) - size
            block = '>'.join([convert(data[i]) for i in range(idx, len(data))])
            latest_blocks.append(block)
            latest_blocks.append(mirror(block))
            latest_blocks.append(make_direction_pattern_block(data, idx, size))
            mid_block = make_middle_mirror_block(data, idx, size)
            if mid_block:
                latest_blocks.append(mid_block)

        for size in range(2, 6):
            for i in range(len(data) - size):
                compare_blocks = [
                    '>'.join([convert(data[j]) for j in range(i, i + size)]),
                    mirror('>'.join([convert(data[j]) for j in range(i, i + size)])),
                    make_direction_pattern_block(data, i, size),
                    make_middle_mirror_block(data, i, size)
                ]
                for block in compare_blocks:
                    if block and block in latest_blocks:
                        if i > 0:
                            predictions.append(convert(data[i - 1]))
                        if i + size < len(data):
                            predictions.append(convert(data[i + size]))

        top3 = [item for item, _ in Counter(predictions).most_common(3)]
        while len(top3) < 3:
            top3.append("❌ 없음")

        return jsonify({
            "예측회차": int(raw_data[0]["date_round"]) + 1,
            "Top3 예측값": top3
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
