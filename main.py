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
        seen_matches = set()
        used_prediction_positions = set()  # 예측 위치 중복 제한
        debug_logs = []  # 디버깅 기록

        for size in range(2, 6):  # 2~5줄 고정 블럭
            for i in range(len(data) - size - 1, 0, -1):  # 아래에서 위로 블럭 생성
                block = [convert(data[j]) for j in range(i, i + size)]
                block_str = '>'.join(block)

                for k in range(0, i - size):  # 위쪽 블럭 탐색
                    past_block = [convert(data[j]) for j in range(k, k + size)]
                    past_block_str = '>'.join(past_block)

                    if past_block_str == block_str:
                        match_key = (block_str, k)
                        if match_key in seen_matches:
                            continue
                        seen_matches.add(match_key)

                        match_log = {
                            "블럭": block_str,
                            "생성위치(i)": i,
                            "매칭위치(k)": k,
                            "예측값": []
                        }

                        # 예측 위치 기준 중복 제한
                        if k > 0 and k - 1 not in used_prediction_positions:
                            result = convert(data[k - 1])
                            predictions.append(result)
                            used_prediction_positions.add(k - 1)
                            match_log["예측값"].append({"위치": "상단(k-1)", "값": result})

                        if k + size < len(data) and k + size not in used_prediction_positions:
                            result = convert(data[k + size])
                            predictions.append(result)
                            used_prediction_positions.add(k + size)
                            match_log["예측값"].append({"위치": "하단(k+size)", "값": result})

                        debug_logs.append(match_log)

        counter = Counter(predictions)
        top3_raw = counter.most_common(3)
        top3 = [{"value": item, "count": count} for item, count in top3_raw]

        while len(top3) < 3:
            top3.append({"value": "❌ 없음", "count": 0})

        return jsonify({
            "예측회차": int(raw_data[0]["date_round"]) + 1,
            "Top3 예측값": top3,
            "디버깅로그": debug_logs  # 전체 블럭 매칭 및 예측 위치 로그 출력
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
