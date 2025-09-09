FROM python:3.9-alpine

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && adduser -D appuser

# アプリケーションのソースコードをコピー
COPY . .

# 非特権ユーザーで実行
USER appuser

# データベース用ディレクトリをボリュームとして定義
VOLUME ["/data"]
ENV DATABASE_PATH=/data/initiatives.db

# コンテナがリッスンするポートを指定
EXPOSE 5000

# アプリケーションの起動コマンド
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

