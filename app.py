from flask import Flask, jsonify, request, render_template, g
import sqlite3
import os
import json


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
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            amount INTEGER NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.commit()

    # 既存テーブルに title 列がない場合は追加
    c.execute("PRAGMA table_info(initiatives)")
    columns = [row[1] for row in c.fetchall()]
    if "title" not in columns:
        c.execute("ALTER TABLE initiatives ADD COLUMN title TEXT NOT NULL DEFAULT ''")
        conn.commit()

    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO categories (name) VALUES (?)",
            [("粗利率改善",), ("固定費コントロール",), ("粗利額アップ",)],
        )

    c.execute("SELECT COUNT(*) FROM departments")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO departments (name) VALUES (?)",
            [("営業1課",), ("開発部",), ("営業2課",)],
        )

    c.execute("SELECT COUNT(*) FROM names")
    if c.fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO names (name) VALUES (?)",
            [("山田 太郎",), ("鈴木 一郎",), ("佐藤 花子",), ("高橋 健太",)],
        )

    c.execute("SELECT COUNT(*) FROM initiatives")
    if c.fetchone()[0] == 0:
        samples = [
            (
                "営業1課",
                "山田 太郎",
                "大型案件受注",
                "2025-08-15",
                "粗利額アップ",
                "新規大型案件の受注",
                1500000,
            ),
            (
                "開発部",
                "鈴木 一郎",
                "サーバー費用最適化",
                "2025-08-20",
                "固定費コントロール",
                "クラウドサーバー費用の最適化",
                80000,
            ),
            (
                "営業2課",
                "佐藤 花子",
                "高利益率提案",
                "2025-08-25",
                "粗利率改善",
                "高利益率商品の提案比率向上",
                250000,
            ),
            (
                "営業1課",
                "高橋 健太",
                "アップセル追加受注",
                "2025-09-01",
                "粗利額アップ",
                "アップセル提案による追加受注",
                450000,
            ),
        ]
        c.executemany(
            """
            INSERT INTO initiatives (
                department, name, title, date, category, content, amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            samples,
        )
        conn.commit()

    c.execute("SELECT COUNT(*) FROM settings WHERE key = 'goal_amount'")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO settings (key, value) VALUES ('goal_amount', '0')"
        )
        conn.commit()

    c.execute("SELECT COUNT(*) FROM settings WHERE key = 'about_text'")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO settings (key, value) VALUES ('about_text', '業績アップ活動とは、売上の向上やコスト削減など会社の収益性を高めるための取り組みの総称です。')"
        )
        conn.commit()

    c.execute("SELECT COUNT(*) FROM settings WHERE key = 'default_start'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO settings (key, value) VALUES ('default_start', '')")
        conn.commit()

    c.execute("SELECT COUNT(*) FROM settings WHERE key = 'default_end'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO settings (key, value) VALUES ('default_end', '')")
        conn.commit()

    c.execute("SELECT COUNT(*) FROM settings WHERE key = 'category_goals'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO settings (key, value) VALUES ('category_goals', '{}')")
        conn.commit()
    conn.close()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


init_db()


# フロントエンドのVue.jsアプリケーションを提供
@app.route("/")
def index():
    return render_template("index.html")


# API: 全ての取り組み実績を取得（期間指定可能）
@app.route("/api/initiatives", methods=["GET"])
def get_initiatives():
    conn = get_db()
    start = request.args.get("start")
    end = request.args.get("end")

    query = "SELECT * FROM initiatives"
    params = []
    if start and end:
        query += " WHERE date BETWEEN ? AND ?"
        params.extend([start, end])
    elif start:
        query += " WHERE date >= ?"
        params.append(start)
    elif end:
        query += " WHERE date <= ?"
        params.append(end)

    initiatives = [dict(row) for row in conn.execute(query, params)]
    return jsonify(initiatives)


# API: 初期表示用データを一括取得
@app.route("/api/bootstrap", methods=["GET"])
def bootstrap_data():
    conn = get_db()
    start = request.args.get("start")
    end = request.args.get("end")

    query = "SELECT * FROM initiatives"
    params = []
    if start and end:
        query += " WHERE date BETWEEN ? AND ?"
        params.extend([start, end])
    elif start:
        query += " WHERE date >= ?"
        params.append(start)
    elif end:
        query += " WHERE date <= ?"
        params.append(end)

    initiatives = [dict(row) for row in conn.execute(query, params)]
    departments = [dict(row) for row in conn.execute("SELECT * FROM departments ORDER BY name")]
    names = [dict(row) for row in conn.execute("SELECT * FROM names ORDER BY name")]
    categories = [dict(row) for row in conn.execute("SELECT * FROM categories ORDER BY name")]
    about_row = conn.execute("SELECT value FROM settings WHERE key = 'about_text'").fetchone()
    goals_row = conn.execute("SELECT value FROM settings WHERE key = 'category_goals'").fetchone()
    about_text = about_row["value"] if about_row else ""
    category_goals = json.loads(goals_row["value"]) if goals_row and goals_row["value"] else {}
    return jsonify(
        {
            "initiatives": initiatives,
            "departments": departments,
            "names": names,
            "categories": categories,
            "about_text": about_text,
            "category_goals": category_goals,
        }
    )


# API: 新しい取り組み実績を追加
@app.route("/api/initiatives", methods=["POST"])
def add_initiative():
    data = request.json

    # 簡単なバリデーション
    if not all(
        k in data for k in ["department", "name", "title", "date", "category", "content", "amount"]
    ):
        return jsonify({"error": "Missing data"}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO initiatives (department, name, title, date, category, content, amount)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["department"],
            data["name"],
            data["title"],
            data["date"],
            data["category"],
            data["content"],
            int(data["amount"]),
        ),
    )
    conn.commit()
    item_id = c.lastrowid

    return (
        jsonify(
            {
                "id": item_id,
                "department": data["department"],
                "name": data["name"],
                "title": data["title"],
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
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM initiatives WHERE id = ?", (item_id,))
    row = c.fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404

    updated = {
        "department": data.get("department", row["department"]),
        "name": data.get("name", row["name"]),
        "title": data.get("title", row["title"]),
        "date": data.get("date", row["date"]),
        "category": data.get("category", row["category"]),
        "content": data.get("content", row["content"]),
        "amount": int(data.get("amount", row["amount"])),
    }

    c.execute(
        """
        UPDATE initiatives
        SET department = ?, name = ?, title = ?, date = ?, category = ?, content = ?, amount = ?
        WHERE id = ?
        """,
        (
            updated["department"],
            updated["name"],
            updated["title"],
            updated["date"],
            updated["category"],
            updated["content"],
            updated["amount"],
            item_id,
        ),
    )
    conn.commit()

    return jsonify({"id": item_id, **updated})


# API: 取り組みを削除
@app.route("/api/initiatives/<int:item_id>", methods=["DELETE"])
def delete_initiative(item_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM initiatives WHERE id = ?", (item_id,))
    if c.rowcount == 0:
        return jsonify({"error": "Not found"}), 404
    conn.commit()
    return "", 204


# 共通関数: シンプルな設定マスタのCRUD(追加と一覧)
def handle_simple_table(table_name):
    conn = get_db()
    c = conn.cursor()
    if request.method == "GET":
        rows = [dict(row) for row in c.execute(f"SELECT * FROM {table_name} ORDER BY name")]
        return jsonify(rows)
    else:
        data = request.json or {}
        if "name" not in data:
            return jsonify({"error": "Missing name"}), 400
        c.execute(f"INSERT INTO {table_name} (name) VALUES (?)", (data["name"],))
        conn.commit()
        item_id = c.lastrowid
        return jsonify({"id": item_id, "name": data["name"]}), 201


def handle_simple_table_item(table_name, item_id):
    conn = get_db()
    c = conn.cursor()
    if request.method == "PUT":
        data = request.json or {}
        if "name" not in data:
            return jsonify({"error": "Missing name"}), 400
        c.execute(
            f"UPDATE {table_name} SET name = ? WHERE id = ?",
            (data["name"], item_id),
        )
        if c.rowcount == 0:
            return jsonify({"error": "Not found"}), 404
        conn.commit()
        return jsonify({"id": item_id, "name": data["name"]})
    else:
        c.execute(f"DELETE FROM {table_name} WHERE id = ?", (item_id,))
        if c.rowcount == 0:
            return jsonify({"error": "Not found"}), 404
        conn.commit()
        return "", 204


@app.route("/api/departments", methods=["GET", "POST"])
def manage_departments():
    return handle_simple_table("departments")


@app.route("/api/departments/<int:item_id>", methods=["PUT", "DELETE"])
def manage_department_item(item_id):
    return handle_simple_table_item("departments", item_id)


@app.route("/api/names", methods=["GET", "POST"])
def manage_names():
    return handle_simple_table("names")


@app.route("/api/names/<int:item_id>", methods=["PUT", "DELETE"])
def manage_name_item(item_id):
    return handle_simple_table_item("names", item_id)


@app.route("/api/categories", methods=["GET", "POST"])
def manage_categories():
    return handle_simple_table("categories")


@app.route("/api/categories/<int:item_id>", methods=["PUT", "DELETE"])
def manage_category_item(item_id):
    return handle_simple_table_item("categories", item_id)


@app.route("/api/goal", methods=["GET", "PUT"])
def manage_goal():
    conn = get_db()
    c = conn.cursor()
    if request.method == "GET":
        c.execute("SELECT value FROM settings WHERE key = 'goal_amount'")
        row = c.fetchone()
        goal = int(row["value"]) if row else 0
        return jsonify({"goal": goal})
    else:
        data = request.json or {}
        if "goal" not in data:
            return jsonify({"error": "Missing goal"}), 400
        goal = int(data["goal"])
        c.execute(
            """
            INSERT INTO settings (key, value) VALUES ('goal_amount', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (goal,),
        )
        conn.commit()
        return jsonify({"goal": goal})


@app.route("/api/about", methods=["GET", "PUT"])
def manage_about():
    conn = get_db()
    c = conn.cursor()
    if request.method == "GET":
        c.execute("SELECT value FROM settings WHERE key = 'about_text'")
        row = c.fetchone()
        text = row["value"] if row else ""
        return jsonify({"text": text})
    else:
        data = request.json or {}
        if "text" not in data:
            return jsonify({"error": "Missing text"}), 400
        c.execute(
            """
            INSERT INTO settings (key, value) VALUES ('about_text', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (data["text"],),
        )
        conn.commit()
        return jsonify({"text": data["text"]})


@app.route("/api/default-period", methods=["GET", "PUT"])
def manage_default_period():
    conn = get_db()
    c = conn.cursor()
    if request.method == "GET":
        c.execute("SELECT value FROM settings WHERE key = 'default_start'")
        row_start = c.fetchone()
        c.execute("SELECT value FROM settings WHERE key = 'default_end'")
        row_end = c.fetchone()
        return jsonify(
            {
                "start": row_start["value"] if row_start else "",
                "end": row_end["value"] if row_end else "",
            }
        )
    else:
        data = request.json or {}
        start = data.get("start", "")
        end = data.get("end", "")
        c.execute(
            """
            INSERT INTO settings (key, value) VALUES ('default_start', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (start,),
        )
        c.execute(
            """
            INSERT INTO settings (key, value) VALUES ('default_end', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (end,),
        )
        conn.commit()
        return jsonify({"start": start, "end": end})


@app.route("/api/category-goals", methods=["GET", "PUT"])
def manage_category_goals():
    conn = get_db()
    c = conn.cursor()
    if request.method == "GET":
        c.execute("SELECT value FROM settings WHERE key = 'category_goals'")
        row = c.fetchone()
        goals = json.loads(row["value"]) if row and row["value"] else {}
        return jsonify(goals)
    else:
        data = request.json or {}
        c.execute(
            """
            INSERT INTO settings (key, value) VALUES ('category_goals', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (json.dumps(data),),
        )
        conn.commit()
        return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

