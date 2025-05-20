from flask import Flask, jsonify, render_template
from flask_cors import CORS
import requests
from collections import Counter
import os
import random

app = Flask(__name__)
CORS(app)

def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

def reverse_block(block):
    return list(reversed(block))

def get_mirror_name(name):
    table = str.maketrans("좌우", "우좌")
    return name.translate(table)

def convert_block_to_str(block):
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
        seen_matches = set()
        used_prediction_positions = set()
        debug_logs = []

        for size in range(2, 6):  # 2~5줄 고정 블럭
            for i in range(len(data) - size - 1):
                base_block = [convert(data[j]) for j in range(i, i + size)]

                # 역정렬 블럭
                rev_block = reverse_block(base_block)
                rev_block_str = convert_block_to_str(rev_block)

                # 역정렬 + 대칭 블럭
                mirror_rev_block = [get_mirror_name(x) for x in rev_block]
                mirror_rev_block_str = convert_block_to_str(mirror_rev_block)

                candidate_blocks = [
                    ("역정렬", rev_block_str),
                    ("역정렬대칭", mirror_rev_block_str)
                ]

                for block_type, block_str in candidate_blocks:
                    for k in range(i + size, len(data) - size):
                        past_block = [convert(data[j]) for j in range(k, k + size)]
                        past_block_str = convert_block_to_str(past_block)

                        if past_block_str == block_str:
                            match_key = (block_str, k)
                            if match_key in seen_matches:
                                continue
                            seen_matches.add(match_key)

                            match_log = {
                                "블럭유형": block_type,
                                "블럭": block_str,
                                "현재위치(i)": i,
                                "매칭위치(k)": k,
                                "예측값": []
                            }

                            prediction_candidates = []
                            if k > 0 and k - 1 not in used_prediction_positions:
                                prediction_candidates.append(("상단(k-1)", k - 1))
                            if k + size < len(data) and k + size not in used_prediction_positions:
                                prediction_candidates.append(("하단(k+size)", k + size))

                            if prediction_candidates:
                                choice = random.choice(prediction_candidates)
                                label, pos = choice
                                result = convert(data[pos])
                                predictions.append(result)
                                used_prediction_positions.add(pos)
                                match_log["예측값"].append({"위치": label, "값": result})

                            debug_logs.append(match_log)
                            break  # 한 번 매칭되면 다음 블럭으로

        counter = Counter(predictions)
        top3_raw = counter.most_common(3)
        top3 = [{"value": item, "count": count} for item, count in top3_raw]

        while len(top3) < 3:
            top3.append({"value": "❌ 없음", "count": 0})

        return jsonify({
            "예측회차": int(raw_data[0]["date_round"]) + 1,
            "Top3 예측값": top3,
            "디버깅로그": debug_logs
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
