from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os
from collections import defaultdict, Counter

app = Flask(__name__)
CORS(app)

def convert(entry):
    side = '좌' if entry['start_point'] == 'LEFT' else '우'
    count = str(entry['line_count'])
    oe = '짝' if entry['odd_even'] == 'EVEN' else '홀'
    return f"{side}{count}{oe}"

def split_components(name):
    return name[0], name[1], name[2]

def calculate_score(value, recent_list, total_list, block_sequence):
    score = 0.0
    reasons = []

    # 빈도 점수
    recent_count = recent_list.count(value)
    total_count = total_list.count(value)
    freq_score = recent_count * 1.0 + (total_count / 10.0) * 0.5
    score += freq_score
    reasons.append(f"빈도 점수: {freq_score}점 (최근 {recent_count}회, 전체 {total_count}회)")

    # 블럭 반복 보정 (과거 블럭에서 다음 줄 값이 예측값과 같을 경우)
    block_matches = 0
    for i in range(len(block_sequence) - 4):
        if block_sequence[i:i+3] == block_sequence[-3:]:
            if i + 3 < len(block_sequence) and block_sequence[i+3] == value:
                block_matches += 1
    if block_matches > 0:
        block_score = block_matches * 1.0
        score += block_score
        reasons.append(f"블럭 반복 보정: +{block_score}점 ({block_matches}회 적중)")

    # 밸런스 반등 보정
    counter = Counter(recent_list)
    if value in ['좌', '우'] and counter:
        opp = '우' if value == '좌' else '좌'
        if counter[opp] >= 16:
            score += 1.5
            reasons.append(f"밸런스 보정: {opp} 편향 → {value} +1.5점")
    if value in ['홀', '짝'] and counter:
        opp = '짝' if value == '홀' else '홀'
        if counter[opp] >= 16:
            score += 1.5
            reasons.append(f"밸런스 보정: {opp} 편향 → {value} +1.5점")

    # 연속 반복 감점
    max_streak = 0
    current_streak = 0
    for v in recent_list:
        if v == value:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    if max_streak >= 5:
        score -= 1.0
        reasons.append(f"연속 반복 감점: {max_streak}회 연속 → -1.0점")

    return {
        "value": value,
        "score": round(score, 2),
        "recent": recent_count,
        "total": total_count,
        "reasons": reasons
    }

def predict_element(data, index):
    recent = data[-20:]
    recent_values = [split_components(convert(d))[index] for d in recent]
    total_values = [split_components(convert(d))[index] for d in data]
    block_sequence = [split_components(convert(d))[index] for d in data]

    candidates = list(set(total_values))
    scored = [calculate_score(v, recent_values, total_values, block_sequence) for v in candidates]
    return max(scored, key=lambda x: x['score'])

@app.route("/predict", methods=["GET"])
def predict():
    try:
        url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
        response = requests.get(url)
        raw_data = response.json()

        data = raw_data[-288:]
        round_num = int(raw_data[-1]["date_round"]) + 1

        result = {
            "예측회차": round_num,
            "예측값": {
                "시작방향": predict_element(data, 0),
                "줄수": predict_element(data, 1),
                "홀짝": predict_element(data, 2)
            }
        }
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
