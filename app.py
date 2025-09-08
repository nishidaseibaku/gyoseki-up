from flask import Flask, jsonify, request, render_template
import sqlite3
import os


app = Flask(__name__)

# データベースのパス（ボリュームマウントを想定）
DATABASE = os.environ.get("DATABASE_PATH", "/data/initiatives.db")


def init_db():
    """テーブルが存在しない場合は作成し、データが無ければサンプルを投入"""
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS initiatives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT NOT NULL,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            amount INTEGER NOT NULL
        )
        """
    )
    conn.commit()

    c.execute("SELECT COUNT(*) FROM initiatives")
    if c.fetchone()[0] == 0:
        samples = [
            ("営業1課", "山田 太郎", "2025-08-15", "粗利額アップ", "新規大型案件の受注", 1500000),
            ("開発部", "鈴木 一郎", "2025-08-20", "固定費コントロール", "クラウドサーバー費用の最適化", 80000),
            ("営業2課", "佐藤 花子", "2025-08-25", "粗利率改善", "高利益率商品の提案比率向上", 250000),
            ("営業1課", "高橋 健太", "2025-09-01", "粗利額アップ", "アップセル提案による追加受注", 450000),
        ]
        c.executemany(
            """
            INSERT INTO initiatives (
                department, name, date, category, content, amount
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            samples,
        )
        conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


init_db()


# フロントエンドのVue.jsアプリケーションを提供
@app.route("/")
def index():
    return render_template("index.html")


# API: 全ての取り組み実績を取得
@app.route("/api/initiatives", methods=["GET"])
def get_initiatives():
    conn = get_db_connection()
    initiatives = [dict(row) for row in conn.execute("SELECT * FROM initiatives")]
    conn.close()
    return jsonify(initiatives)


# API: 新しい取り組み実績を追加
@app.route("/api/initiatives", methods=["POST"])
def add_initiative():
    data = request.json

    # 簡単なバリデーション
    if not all(
        k in data for k in ["department", "name", "date", "category", "content", "amount"]
    ):
        return jsonify({"error": "Missing data"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO initiatives (department, name, date, category, content, amount)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data["department"],
            data["name"],
            data["date"],
            data["category"],
            data["content"],
            int(data["amount"]),
        ),
    )
    conn.commit()
    item_id = c.lastrowid
    conn.close()

    return (
        jsonify(
            {
                "id": item_id,
                "department": data["department"],
                "name": data["name"],
                "date": data["date"],
                "category": data["category"],
                "content": data["content"],
                "amount": int(data["amount"]),
            }
        ),
        201,
    )


# API: 既存の取り組み実績を更新
@app.route("/api/initiatives/<int:item_id>", methods=["PUT"])
def update_initiative(item_id):
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM initiatives WHERE id = ?", (item_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    updated = {
        "department": data.get("department", row["department"]),
        "name": data.get("name", row["name"]),
        "date": data.get("date", row["date"]),
        "category": data.get("category", row["category"]),
        "content": data.get("content", row["content"]),
        "amount": int(data.get("amount", row["amount"])),
    }

    c.execute(
        """
        UPDATE initiatives
        SET department = ?, name = ?, date = ?, category = ?, content = ?, amount = ?
        WHERE id = ?
        """,
        (
            updated["department"],
            updated["name"],
            updated["date"],
            updated["category"],
            updated["content"],
            updated["amount"],
            item_id,
        ),
    )
    conn.commit()
    conn.close()

    return jsonify({"id": item_id, **updated})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

