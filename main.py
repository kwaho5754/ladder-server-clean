from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import requests
from collections import Counter
import os

app = Flask(__name__)
CORS(app)

mirror_map = {
    '좌삼짝': '우삼홀', '우삼홀': '좌삼짝',
    '좌삼홀': '우삼짝', '우삼짝': '좌삼홀',
    '좌사짝': '우사홀', '우사홀': '좌사짝',
    '좌사홀': '우사짝', '우사짝': '좌사홀',
}

def get_transformed_block(block):
    return [mirror_map.get(b, b) for b in block]

def block_to_str(block):
    return '-'.join(block)

@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

@app.route('/predict')
def predict():
    url = "https://ntry.com/data/json/games/power_ladder/recent_result.json"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json()
        results = [row['result'] for row in data['rows']]
    except Exception as e:
        return jsonify({"error": str(e)})

    block_lengths = [2, 3, 4, 5]
    total_blocks = []

    for length in block_lengths:
        if len(results) < length + 1:
            continue
        recent_block = results[-length:]
        mirrored_block = get_transformed_block(recent_block)
        total_blocks.append(mirrored_block)

    prediction_candidates = []

    for blk in total_blocks:
        blk_str = block_to_str(blk)
        for i in range(len(results) - len(blk) - 1):
            comp_block = results[i:i+len(blk)]
            comp_str = block_to_str(get_transformed_block(comp_block))
            if comp_str == blk_str:
                upper = results[i-1] if i > 0 else None
                lower = results[i+len(blk)] if (i + len(blk)) < len(results) else None
                if upper: prediction_candidates.append(upper)
                if lower: prediction_candidates.append(lower)
                break

    if not prediction_candidates:
        top3 = ['❌ 없음'] * 3
    else:
        count = Counter(prediction_candidates)
        top3 = [item[0] for item in count.most_common(3)]
        while len(top3) < 3:
            top3.append('❌ 없음')

    return jsonify({'예측값 Top3': top3})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
