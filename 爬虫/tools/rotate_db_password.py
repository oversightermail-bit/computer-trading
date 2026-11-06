# -*- coding: utf-8 -*-
"""Rotate local MySQL root password: old hardcoded 123456 -> new password in .dbsecret.

Run once: python tools/rotate_db_password.py
"""
import pymysql
from dbconn import password as read_new_password

OLD = "123456"
NEW = read_new_password()

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password=OLD,
                       charset="utf8mb4", autocommit=True)
cur = conn.cursor()
cur.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (NEW,))
print("ALTER USER OK")
conn.close()

c2 = pymysql.connect(host="127.0.0.1", port=3306, user="root", password=NEW, charset="utf8mb4")
cur2 = c2.cursor()
cur2.execute("SELECT VERSION()")
print("new password connect OK:", cur2.fetchone()[0])
c2.close()

try:
    c3 = pymysql.connect(host="127.0.0.1", port=3306, user="root", password=OLD, charset="utf8mb4")
    print("WARN: old password still works!")
    c3.close()
except Exception as e:
    print("old password rejected OK:", type(e).__name__)
