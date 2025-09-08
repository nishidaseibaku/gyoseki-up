from flask import Flask, jsonify, request, render_template
import json
from datetime import datetime

app = Flask(__name__)

# データストア（デモ用にメモリ上でデータを保持）
# 実際の運用ではデータベース（SQLite, PostgreSQLなど）に置き換えることを推奨します
initiatives = [
    {
        "id": 1,
        "department": "営業1課",
        "name": "山田 太郎",
        "date": "2025-08-15",
        "category": "粗利額アップ",
        "content": "新規大型案件の受注",
        "amount": 1500000,
    },
    {
        "id": 2,
        "department": "開発部",
        "name": "鈴木 一郎",
        "date": "2025-08-20",
        "category": "固定費コントロール",
        "content": "クラウドサーバー費用の最適化",
        "amount": 80000,
    },
    {
        "id": 3,
        "department": "営業2課",
        "name": "佐藤 花子",
        "date": "2025-08-25",
        "category": "粗利率改善",
        "content": "高利益率商品の提案比率向上",
        "amount": 250000,
    },
    {
        "id": 4,
        "department": "営業1課",
        "name": "高橋 健太",
        "date": "2025-09-01",
        "category": "粗利額アップ",
        "content": "アップセル提案による追加受注",
        "amount": 450000,
    },
]
next_id = 5

# フロントエンドのVue.jsアプリケーションを提供
@app.route('/')
def index():
    return render_template('index.html')

# API: 全ての取り組み実績を取得
@app.route('/api/initiatives', methods=['GET'])
def get_initiatives():
    return jsonify(initiatives)

# API: 新しい取り組み実績を追加
@app.route('/api/initiatives', methods=['POST'])
def add_initiative():
    global next_id
    data = request.json
    
    # 簡単なバリデーション
    if not all(k in data for k in ['department', 'name', 'date', 'category', 'content', 'amount']):
        return jsonify({"error": "Missing data"}), 400
    
    initiative = {
        "id": next_id,
        "department": data['department'],
        "name": data['name'],
        "date": data['date'],
        "category": data['category'],
        "content": data['content'],
        "amount": int(data['amount']),
    }
    initiatives.append(initiative)
    next_id += 1
    return jsonify(initiative), 201


# API: 既存の取り組み実績を更新
@app.route('/api/initiatives/<int:item_id>', methods=['PUT'])
def update_initiative(item_id):
    data = request.json
    for initiative in initiatives:
        if initiative["id"] == item_id:
            # 各フィールドを更新（指定が無ければ既存値を維持）
            initiative["department"] = data.get("department", initiative["department"])
            initiative["name"] = data.get("name", initiative["name"])
            initiative["date"] = data.get("date", initiative["date"])
            initiative["category"] = data.get("category", initiative["category"])
            initiative["content"] = data.get("content", initiative["content"])
            if "amount" in data:
                initiative["amount"] = int(data["amount"])
            return jsonify(initiative)
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
