from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/ping")
def ping():
    return "pong"

@app.route("/predict")
def predict():
    # 예측 로직 (생략)
    return jsonify({"예측회차": 123, "앞기준 예측값": ["좌2짝", "우3홀", "좌4짝"]})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
