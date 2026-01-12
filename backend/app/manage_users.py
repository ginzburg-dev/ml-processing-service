
import sys
import argparse
import getpass
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.database import UserDatabase
from backend.app.config import MLServiceConfig

import structlog

LOGGER = structlog.get_logger()


def main():
    config = MLServiceConfig(dotenv=True)
    database = UserDatabase(config.db_path)

    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    c = sub.add_parser("create")
    c.add_argument("username")
    c.add_argument("--role", default="user")

    su = sub.add_parser("set-username")
    su.add_argument("user_id", type=int)
    su.add_argument("new_username")

    sp = sub.add_parser("set-password")
    sp.add_argument("user_id", type=int)

    sr = sub.add_parser("set-role")
    sr.add_argument("user_id", type=int)
    sr.add_argument("new_role")

    d = sub.add_parser("delete")
    d.add_argument("user_id", type=int)

    args = p.parse_args()

    if args.cmd == "list":
        for uid, uname, role in database.list_users():
            print(uid, uname, role)

    elif args.cmd == "create":
        password = getpass.getpass("Password: ")
        try:
            database.create_user(args.username, password, role=args.role)
        except ValueError as e:
            print(e)

    elif args.cmd == "set-username":
        database.set_username(args.user_id, args.new_username)

    elif args.cmd == "set-password":
        new_password = getpass.getpass("Password: ")
        database.set_password(args.user_id, new_password)

    elif args.cmd == "set-role":
        database.set_role(args.user_id, args.new_role)

    elif args.cmd == "delete":
        database.delete_user(args.user_id)

if __name__ == "__main__":
    main()
