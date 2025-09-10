# 業績アップ取り組みダッシュボード

社内の業績改善への取り組みを全社で共有し、可視化するためのダッシュボードアプリケーションです。

## 機能
- 取り組み内容の登録・一覧表示
- 全体の貢献金額や総件数の集計
- 分類別・部門別の貢献金額のグラフ表示
- 設定画面で氏名一覧をCSVからインポート

## 使用技術
- バックエンド: Flask (Python) / Gunicorn
- フロントエンド: Vue.js, Bootstrap
- データベース: SQLite
- コンテナ: Docker (軽量な Python Alpine ベースイメージ)

## 実行方法

### Docker での起動
1. イメージをビルド
   `docker build -t performance-dashboard .`
2. コンテナを起動
   `docker run -p 5000:5000 -v $(pwd)/data:/data performance-dashboard`

   `/data` にマウントしたディレクトリに SQLite データベースが保存されます。  
   初回起動時にデータが存在しない場合はサンプルデータが自動登録されます。
3. ブラウザで `http://localhost:5000` にアクセス

### Windows 上での起動
1. 仮想環境を作成して依存パッケージをインストール
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. アプリケーションを起動
   ```
   start_windows.bat
   ```

## ディレクトリ構成
```
├── Dockerfile
├── README.md
├── app.py
├── requirements.txt
└── templates/
    └── index.html
```

