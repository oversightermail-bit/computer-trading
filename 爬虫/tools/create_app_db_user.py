# -*- coding: utf-8 -*-
"""Create least-privilege MySQL user 'hwapp' for the app backend (CRUD on hw_price only).

Usage: python tools/create_app_db_user.py <hwapp_password>
"""
import sys

import pymysql

from dbconn import password as root_password

NEW = sys.argv[1]

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password=root_password(),
                       charset="utf8mb4", autocommit=True)
cur = conn.cursor()
cur.execute("CREATE USER IF NOT EXISTS 'hwapp'@'localhost' IDENTIFIED BY %s", (NEW,))
cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON hw_price.* TO 'hwapp'@'localhost'")
print("hwapp user created/granted")
conn.close()

# verify
c2 = pymysql.connect(host="127.0.0.1", port=3306, user="hwapp", password=NEW,
                     database="hw_price", charset="utf8mb4")
cur2 = c2.cursor()
cur2.execute("SELECT COUNT(*) FROM t_user")
print("hwapp connect OK, t_user rows:", cur2.fetchone()[0])
try:
    cur2.execute("CREATE TABLE IF NOT EXISTS _perm_test (id INT)")
    print("WARN: hwapp has DDL rights (unexpected)")
except Exception as e:
    print("hwapp DDL denied OK:", type(e).__name__)
c2.close()
