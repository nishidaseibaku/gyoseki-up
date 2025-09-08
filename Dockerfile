FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY . .

# データベース用ディレクトリをボリュームとして定義
VOLUME ["/data"]
ENV DATABASE_PATH=/data/initiatives.db

# コンテナがリッスンするポートを指定
EXPOSE 5000

# アプリケーションの起動コマンド
CMD ["python", "app.py"]

