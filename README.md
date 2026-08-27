# 業績アップ取り組みダッシュボード

社内の業績改善への取り組みを全社で共有し、可視化するためのダッシュボードアプリケーションです。

## 機能
- 取り組み内容の登録・一覧表示（検索・並び替え・CSVエクスポート）
- 設定画面で社・課・氏名・分類マスタを追加/編集/削除（氏名はCSVからの一括インポートも可能）
- ユーザー名・パスワードによるログイン（アカウントは管理者が事前作成、社内限定アクセス）

## 使用技術
- ホスティング: Firebase Hosting
- データベース: Cloud Firestore（ブラウザから直接アクセス、サーバーレス）
- 認証: Firebase Authentication（メール/パスワードプロバイダ）
- フロントエンド: Vue.js 3, Vue Router, Bootstrap 5, Tom Select（すべてCDN）

外部システムとの連携は行わず、氏名・部門などのマスタデータもすべてこのアプリの中で管理する。

Firebase プロジェクト: `gyoseki-up-98j3h4t`（東京リージョン asia-northeast1）

## ディレクトリ構成
```
├── firebase.json            # Hosting / Firestore / Emulator 設定
├── .firebaserc              # デフォルトプロジェクト
├── firestore.rules          # セキュリティルール（ログイン必須）
├── firestore.indexes.json
├── public/
│   └── index.html           # アプリ本体（SPA）
└── tools/
    ├── manage_users.py                    # ログインアカウントの作成・管理スクリプト
    └── migrate_sqlite_to_firestore.py     # 旧SQLiteデータの移行スクリプト
```

## 開発

ローカルでは Firebase Emulator Suite を使います（`localhost` でアクセスすると自動的にエミュレータへ接続します）。

```
npm install -g firebase-tools   # 未導入の場合
firebase emulators:start
```

ブラウザで `http://localhost:5000` を開きます。ログインには `tools/manage_users.py` でエミュレータ上に作成したテストアカウントを使います（後述）。

## デプロイ

```
firebase deploy --only hosting,firestore
```

公開URL: https://gyoseki-up-98j3h4t.web.app

## ログインアカウントの管理

このアプリにセルフサインアップ画面は無く、利用者は管理者が事前に作成したアカウントでログインする。
ログイン画面の「ユーザー名」は、内部的には Firebase Authentication のメール/パスワードプロバイダに
疑似メールアドレス（`<ユーザー名>@gyoseki-up.local`。`public/index.html` の `LOGIN_EMAIL_DOMAIN` で定義）
として登録される。実在するメールアドレスは不要。

アカウントの作成・パスワードリセット・無効化は `tools/manage_users.py` で行う。
表示名などに日本語を含む引数を渡す場合、Git Bash では文字化けすることがあるため
**PowerShell から実行する**こと。

```
pip install firebase-admin
gcloud auth application-default login   # 一度だけ

# アカウント作成
python tools/manage_users.py --project gyoseki-up-98j3h4t create <ユーザー名> <パスワード> <表示名>

# パスワードリセット
python tools/manage_users.py --project gyoseki-up-98j3h4t reset-password <ユーザー名> <新パスワード>

# 無効化 / 再有効化 / 一覧
python tools/manage_users.py --project gyoseki-up-98j3h4t disable <ユーザー名>
python tools/manage_users.py --project gyoseki-up-98j3h4t enable <ユーザー名>
python tools/manage_users.py --project gyoseki-up-98j3h4t list
```

ローカルの Emulator に対して実行する場合は、`firebase emulators:start` を起動した状態で、
別ターミナルで以下の環境変数を設定してから実行する（本番データには影響しない）。

```
set FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
set FIRESTORE_EMULATOR_HOST=localhost:8080
```

## マスタデータ（社・課・氏名・分類）

外部システムとの同期は行わず、設定画面（ログイン後「設定」メニュー）からアプリ内で直接管理する。

氏名は「社 → 課 → 氏名」の階層で管理する。1人の氏名は必ずどこか1つの課に属し、
1つの課は必ずどこか1つの社に属する（社・課を先に登録してから氏名を追加する）。
取り組み実績の登録画面では氏名を選ぶと、その人が属する社・課が自動的に設定される。
氏名は一件ずつの追加・編集・削除のほか、指定した課へのCSVファイルからの一括インポートにも対応する。

## 旧バージョンからのデータ移行

旧 Flask + SQLite 版（git 履歴参照）のデータベースがある場合:

```
pip install google-cloud-firestore
gcloud auth application-default login
python tools/migrate_sqlite_to_firestore.py path/to/initiatives.db
```
