"""管理者用: 共有ログインパスワードを設定・変更するスクリプト。

このアプリのログイン画面にID入力欄は無く、共有のパスワードのみでログインする
（ユーザーごとの個別アカウントという概念を持たない）。内部的には Firebase
Authentication のメール/パスワードプロバイダを使うため、固定の疑似メールアドレス
（public/index.html の APP_LOGIN_EMAIL と同じ値）に対して1つだけアカウントを持ち、
そのパスワードを変更することでログインパスワードを更新する。

前提:
  pip install firebase-admin
  gcloud auth application-default login   # 一度だけ。ブラウザで許可する

--project には対象の Firebase プロジェクトIDを必ず指定する（安全のためデフォルト値は無い）。

ローカルの Firebase Emulator に対して実行する場合は、実行前に別ターミナルで
`firebase emulators:start` を起動したうえで、このスクリプトを実行するターミナルで
以下の環境変数を設定する（本番へは書き込まれなくなる）:
  set FIREBASE_AUTH_EMULATOR_HOST=localhost:9099

使い方:
  python tools/manage_password.py --project <PROJECT_ID> set-password <新パスワード>
"""
import argparse

import firebase_admin
from firebase_admin import auth, credentials

APP_LOGIN_EMAIL = "app@gyoseki-up.local"  # public/index.html の APP_LOGIN_EMAIL と合わせる


def cmd_set_password(args):
    try:
        user = auth.get_user_by_email(APP_LOGIN_EMAIL)
        auth.update_user(user.uid, password=args.password)
        print("パスワードを変更しました。")
    except auth.UserNotFoundError:
        auth.create_user(email=APP_LOGIN_EMAIL, password=args.password)
        print("アカウントを作成し、パスワードを設定しました。")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, help="対象のFirebaseプロジェクトID")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("set-password", help="ログインパスワードを設定・変更（アカウントが無ければ作成）")
    p.add_argument("password")
    p.set_defaults(func=cmd_set_password)

    args = parser.parse_args()
    firebase_admin.initialize_app(credentials.ApplicationDefault(), {"projectId": args.project})
    args.func(args)


if __name__ == "__main__":
    main()
