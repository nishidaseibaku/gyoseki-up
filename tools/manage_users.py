"""管理者用: ユーザー名/パスワードでログインするアカウントを作成・管理するスクリプト。

このアプリにセルフサインアップ画面は無い。新しい利用者を追加するときは、
管理者がこのスクリプトを実行してアカウントを発行する。

ユーザー名は Firebase Authentication のメール/パスワードプロバイダを使うため、
public/index.html の LOGIN_EMAIL_DOMAIN と同じ疑似メールドメインに変換して登録する
（実在するメールアドレスである必要はない）。

前提:
  pip install firebase-admin
  gcloud auth application-default login   # 一度だけ。ブラウザで許可する

--project には対象の Firebase プロジェクトIDを必ず指定する（安全のためデフォルト値は無い）。

ローカルの Firebase Emulator に対して実行する場合は、実行前に別ターミナルで
`firebase emulators:start` を起動したうえで、このスクリプトを実行するターミナルで
以下の環境変数を設定する（本番へは書き込まれなくなる）:
  set FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
  set FIRESTORE_EMULATOR_HOST=localhost:8080

表示名は、新規登録画面での氏名・所属（社/課）の自動選択に使われるため、
設定画面の「氏名」マスタに登録されている氏名と一致させておくとよい。

使い方:
  python tools/manage_users.py --project <PROJECT_ID> create <username> <password> <表示名>
  python tools/manage_users.py --project <PROJECT_ID> reset-password <username> <新パスワード>
  python tools/manage_users.py --project <PROJECT_ID> disable <username>
  python tools/manage_users.py --project <PROJECT_ID> enable <username>
  python tools/manage_users.py --project <PROJECT_ID> list
"""
import argparse

import firebase_admin
from firebase_admin import auth, credentials, firestore

LOGIN_EMAIL_DOMAIN = "gyoseki-up.local"  # public/index.html の LOGIN_EMAIL_DOMAIN と合わせる


def to_pseudo_email(username):
    return f"{username.strip().lower()}@{LOGIN_EMAIL_DOMAIN}"


def cmd_create(args):
    email = to_pseudo_email(args.username)
    user = auth.create_user(email=email, password=args.password, display_name=args.display_name)
    firestore.client().collection("users").document(user.uid).set({
        "username": args.username.strip().lower(),
        "name": args.display_name,
    })
    print(f"作成しました: uid={user.uid} username={args.username} email={email}")


def cmd_reset_password(args):
    user = auth.get_user_by_email(to_pseudo_email(args.username))
    auth.update_user(user.uid, password=args.new_password)
    print(f"パスワードを変更しました: username={args.username}")


def cmd_disable(args):
    user = auth.get_user_by_email(to_pseudo_email(args.username))
    auth.update_user(user.uid, disabled=True)
    print(f"無効化しました: username={args.username}")


def cmd_enable(args):
    user = auth.get_user_by_email(to_pseudo_email(args.username))
    auth.update_user(user.uid, disabled=False)
    print(f"有効化しました: username={args.username}")


def cmd_list(args):
    profiles = {d.id: d.to_dict() for d in firestore.client().collection("users").stream()}
    for user in auth.list_users().iterate_all():
        profile = profiles.get(user.uid, {})
        status = "無効" if user.disabled else "有効"
        username = profile.get("username", "?")
        name = profile.get("name", "")
        print(f"{username:20s} {name:15s} {status}  ({user.email})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, help="対象のFirebaseプロジェクトID")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="アカウントを新規作成")
    p.add_argument("username")
    p.add_argument("password")
    p.add_argument("display_name")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("reset-password", help="パスワードを変更")
    p.add_argument("username")
    p.add_argument("new_password")
    p.set_defaults(func=cmd_reset_password)

    p = sub.add_parser("disable", help="アカウントを無効化")
    p.add_argument("username")
    p.set_defaults(func=cmd_disable)

    p = sub.add_parser("enable", help="アカウントを再有効化")
    p.add_argument("username")
    p.set_defaults(func=cmd_enable)

    sub.add_parser("list", help="アカウント一覧を表示").set_defaults(func=cmd_list)

    args = parser.parse_args()
    firebase_admin.initialize_app(credentials.ApplicationDefault(), {"projectId": args.project})
    args.func(args)


if __name__ == "__main__":
    main()
