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

# 비대칭 블럭 여부 확인 (좌↔우, 홀↔짝 전환이 없는 블럭)
def is_strictly_non_mirrored(block_list):
    for b in block_list:
        if ('좌' in b and '우' in b) or ('짝' in b and '홀' in b):
            return False
    return True

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
        seen_blocks = set()

        print("\n✅ [디버깅] 최근 블럭 수집 시작")
        for size in range(2, 6):
            idx = len(data) - size
            current_block = [convert(data[i]) for i in range(idx, len(data))]
            current_block_str = '>'.join(current_block)

            if not is_strictly_non_mirrored(current_block):
                continue  # 대칭 성분이 섞인 블럭은 제외

            seen_blocks.add(current_block_str)
            print(f"📌 [최근 블럭 등록] {current_block_str}")

        print("\n✅ [디버깅] 과거 블럭 비교 및 예측값 수집")
        for size in range(2, 6):
            for i in range(len(data) - size):
                past_block = [convert(data[j]) for j in range(i, i + size)]
                past_block_str = '>'.join(past_block)

                if not is_strictly_non_mirrored(past_block):
                    continue

                if past_block_str in seen_blocks:
                    continue

                if i > 0:
                    pred_top = convert(data[i - 1])
                    predictions.append(pred_top)
                    print(f"⬆️ 상단 예측: {past_block_str} → {pred_top}")
                if i + size < len(data):
                    pred_bottom = convert(data[i + size])
                    predictions.append(pred_bottom)
                    print(f"⬇️ 하단 예측: {past_block_str} → {pred_bottom}")

        print(f"\n📊 총 예측 후보 개수: {len(predictions)}")

        counter = Counter(predictions)
        top3_raw = counter.most_common(3)
        print("\n🏆 Top 3 예측 결과 (빈도수 포함):")
        for idx, (item, count) in enumerate(top3_raw, 1):
            print(f"{idx}위: {item} (빈도: {count})")

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
