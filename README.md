業績アップ取り組みダッシュボード社内の業績改善への取り組みを全社で共有し、可視化するためのダッシュボードアプリケーションです。✨ 機能業績改善の取り組み内容をフォームから簡単に入力・登録できます。登録された実績が一覧で表示されます。全体の貢献金額や総件数をリアルタイムで集計します。「分類別」「部門別」の貢献金額をグラフで可視化します。🛠️ 使用技術バックエンド: Flask (Python)フロントエンド: Vue.js, Bootstrapコンテナ: Docker🚀 実行方法このアプリケーションはDockerを使用して簡単に起動できます。前提条件Docker がインストールされていること。手順リポジトリをクローンまたはダウンロードこのプロジェクトのファイル (Dockerfile, requirements.txt, app.py, templates/, README.md) を同じディレクトリに配置します。Dockerイメージをビルドターミナルを開き、Dockerfile があるディレクトリで以下のコマンドを実行します。docker build -t performance-dashboard .
Dockerコンテナを実行ビルドが完了したら、以下のコマンドでコンテナを起動します。docker run -p 5000:5000 performance-dashboard
アプリケーションにアクセスWebブラウザを開き、以下のアドレスにアクセスしてください。http://localhost:5000ダッシュボードが表示され、新しい取り組みの登録や実績の確認ができます。📂 ディレクトリ構成.
├── Dockerfile          # Dockerコンテナの定義ファイル
├── README.md           # このファイル
├── app.py              # Flaskアプリケーション本体
├── requirements.txt    # Pythonの依存ライブラリ
└── templates/
    └── index.html      # フロントエンドのHTML/Vue.jsファイル

🖥️ Windowsでの実行
1. 仮想環境を作成して依存パッケージをインストールします。
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. アプリケーションを起動するには以下を実行します。
   ```
   start_windows.bat
   ```
