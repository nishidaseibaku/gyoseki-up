# 業績アップ取り組みダッシュボード

社内の業績改善への取り組みを全社で共有し、可視化するためのダッシュボードアプリケーションです。

## 機能
- 取り組み内容の登録・一覧表示
- 全体の貢献金額や総件数の集計
- 分類別・部門別の貢献金額のグラフ表示
- 設定画面で氏名一覧をCSVからインポート
- Microsoft 365 (Entra ID) アカウントによるログイン（社内限定アクセス）

## 使用技術
- ホスティング: Firebase Hosting
- データベース: Cloud Firestore（ブラウザから直接アクセス、サーバーレス）
- 認証: Firebase Authentication（Microsoft プロバイダ / OpenID Connect）
- フロントエンド: Vue.js 3, Vue Router, Chart.js, Bootstrap 5, Tom Select（すべてCDN）

Firebase プロジェクト: `gyoseki-dashboard-westa`（東京リージョン asia-northeast1）

## ディレクトリ構成
```
├── firebase.json            # Hosting / Firestore / Emulator 設定
├── .firebaserc              # デフォルトプロジェクト
├── firestore.rules          # セキュリティルール（ログイン必須）
├── firestore.indexes.json
├── public/
│   └── index.html           # アプリ本体（SPA）
└── tools/
    └── migrate_sqlite_to_firestore.py  # 旧SQLiteデータの移行スクリプト
```

## 開発

ローカルでは Firebase Emulator Suite を使います（`localhost` でアクセスすると自動的にエミュレータへ接続します）。

```
npm install -g firebase-tools   # 未導入の場合
firebase emulators:start
```

ブラウザで `http://localhost:5000` を開きます。ログインはエミュレータの擬似アカウントが使えます。

## デプロイ

```
firebase deploy --only hosting,firestore
```

公開URL: https://gyoseki-dashboard-westa.web.app

## 認証の設定（初回のみ）

Microsoft ログインを有効にするには Azure ポータルでのアプリ登録が必要です。

1. [Azure ポータル](https://portal.azure.com) → Microsoft Entra ID → アプリの登録 → 新規登録
   - サポートされているアカウントの種類: **この組織ディレクトリのみのアカウント**（シングルテナント。これが社外アカウント排除の要）
   - リダイレクトURI (Web): `https://gyoseki-dashboard-westa.firebaseapp.com/__/auth/handler`
2. 「証明書とシークレット」でクライアントシークレットを作成し、値を控える
3. [Firebase Console](https://console.firebase.google.com/project/gyoseki-dashboard-westa/authentication/providers) → Authentication → ログイン方法 → Microsoft を有効化
   - Azure のアプリケーション (クライアント) ID とシークレットを貼り付ける
4. `public/index.html` の `MS_TENANT` に Azure のディレクトリ (テナント) ID を設定するとログイン画面が自組織に固定される

## 旧バージョンからのデータ移行

旧 Flask + SQLite 版（git 履歴参照）のデータベースがある場合:

```
pip install google-cloud-firestore
gcloud auth application-default login
python tools/migrate_sqlite_to_firestore.py path/to/initiatives.db
```
