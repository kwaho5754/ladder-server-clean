from flask import Flask, jsonify
from flask_cors import CORS
import requests
from collections import Counter
import os

app = Flask(__name__)
CORS(app)

# 변환 함수: 좌3짝 형태로 변환
def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

# 구조 반복 블럭: 방향 흐름만 추출
def make_direction_pattern_block(data, start, size):
    return '>'.join([
        '좌' if data[i]['start_point'] == 'LEFT' else '우'
        for i in range(start, start + size)
    ])

# 중간 대칭 블럭: 중간 줄만 좌우 반전
def make_middle_mirror_block(data, start, size):
    if size < 3:
        return None
    block = [convert(data[i]) for i in range(start, start + size)]
    mid = size // 2
    side = '우' if block[mid][0] == '좌' else '좌'
    oe = '짝' if block[mid][2] == '홀' else '홀'
    block[mid] = f"{side}{block[mid][1]}{oe}"
    return '>'.join(block)

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

        # 최신 블럭들 준비 (구조 반복 + 중간 대칭)
        latest_blocks = []
        for size in range(2, 6):
            idx = len(data) - size
            dir_block = make_direction_pattern_block(data, idx, size)
            mid_block = make_middle_mirror_block(data, idx, size)
            latest_blocks.append(dir_block)
            if mid_block:
                latest_blocks.append(mid_block)

        # 과거 블럭과 비교
        for size in range(2, 6):
            for i in range(len(data) - size):
                dir_block = make_direction_pattern_block(data, i, size)
                mid_block = make_middle_mirror_block(data, i, size)

                for block in [dir_block, mid_block]:
                    if block and block in latest_blocks:
                        if i > 0:
                            predictions.append(convert(data[i - 1]))  # 상단
                        if i + size < len(data):
                            predictions.append(convert(data[i + size]))  # 하단

        top3 = [item for item, _ in Counter(predictions).most_common(3)]
        while len(top3) < 3:
            top3.append("❌ 없음")

        return jsonify({
            "예측회차": int(raw_data[0]["date_round"]) + 1,
            "예측값 Top3": top3
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
