"""既存の SQLite (initiatives.db) のデータを Cloud Firestore へ移行するスクリプト。

前提:
  pip install google-cloud-firestore
  gcloud auth application-default login   # 一度だけ。ブラウザで許可する

使い方:
  python tools/migrate_sqlite_to_firestore.py path/to/initiatives.db

既に Firestore に同名のマスタ (departments/names/categories) がある場合はスキップし、
initiatives は重複チェックなしで全件追加する（再実行すると二重登録になるので注意）。
"""
import json
import sqlite3
import sys

from google.cloud import firestore

PROJECT_ID = "gyoseki-up-98j3h4t"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    db_path = sys.argv[1]

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    fs = firestore.Client(project=PROJECT_ID)

    # マスタ (name のみのテーブル) — 既存と重複しないよう追加
    for table in ("departments", "names", "categories"):
        existing = {d.to_dict().get("name") for d in fs.collection(table).stream()}
        added = 0
        for row in conn.execute(f"SELECT name FROM {table}"):
            if row["name"] not in existing:
                fs.collection(table).add({"name": row["name"]})
                added += 1
        print(f"{table}: {added} 件追加 (既存 {len(existing)} 件)")

    # 取り組み実績
    batch = fs.batch()
    count = 0
    for row in conn.execute("SELECT * FROM initiatives"):
        ref = fs.collection("initiatives").document()
        batch.set(ref, {
            "department": row["department"],
            "name": row["name"],
            "title": row["title"],
            "date": row["date"],
            "category": row["category"],
            "content": row["content"],
            "amount": int(row["amount"]),
            "createdAt": firestore.SERVER_TIMESTAMP,
        })
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = fs.batch()
    batch.commit()
    print(f"initiatives: {count} 件追加")

    # 設定
    settings = {}
    for row in conn.execute("SELECT key, value FROM settings"):
        settings[row["key"]] = row["value"]
    doc = {
        "about_text": settings.get("about_text", ""),
        "default_start": settings.get("default_start", ""),
        "default_end": settings.get("default_end", ""),
        "category_goals": json.loads(settings.get("category_goals") or "{}"),
    }
    fs.collection("settings").document("app").set(doc, merge=True)
    print("settings: 移行完了")


if __name__ == "__main__":
    main()
