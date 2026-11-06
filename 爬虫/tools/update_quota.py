# -*- coding: utf-8 -*-
"""一次性脚本：调整订阅套餐配额（免费版 3/日·15/月；基础版 10/100；专业版 30/300；旗舰版 60/600），
并同步所有生效订阅的等级快照、清零已用计数（配额下调避免用户被旧计数锁死）。

依赖：pip install pymysql（本机 PATH python 已装）
"""
import pymysql
from dbconn import password

NEW_PLANS = {
    "免费版": (3, 15),    # 免费版保留每日限制
    "基础版": (0, 100),   # 付费方案只限每月次数：quota_day=0 表示每日不限
    "专业版": (0, 300),
    "旗舰版": (0, 600),
}

conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", password=password(),
                       database="hw_price", charset="utf8mb4", autocommit=False)
try:
    cur = conn.cursor()

    print("== 调整前套餐 ==")
    cur.execute("SELECT id, plan_name, quota_day, quota_month FROM t_subscription_plan WHERE status=1 ORDER BY sort_order, id")
    for r in cur.fetchall():
        print("  ", r)

    print("== 调整前生效订阅 ==")
    cur.execute("""SELECT s.id, u.username, s.plan_id, s.plan_name, s.quota_day, s.quota_month,
                          s.day_used, s.month_used
                   FROM t_user_subscription s LEFT JOIN t_user u ON u.id = s.user_id
                   WHERE s.status = 1""")
    for r in cur.fetchall():
        print("  ", r)

    print("== 更新套餐配额 ==")
    for name, (d, m) in NEW_PLANS.items():
        n = cur.execute("UPDATE t_subscription_plan SET quota_day=%s, quota_month=%s WHERE plan_name=%s", (d, m, name))
        print("  %s -> 日 %s / 月 %s，rows=%s" % (name, d, m, n))

    print("== 同步生效订阅快照并清零已用计数 ==")
    n = cur.execute("""UPDATE t_user_subscription s
                       JOIN t_subscription_plan p ON p.id = s.plan_id
                       SET s.quota_day = p.quota_day,
                           s.quota_month = p.quota_month,
                           s.day_used = 0,
                           s.month_used = 0
                       WHERE s.status = 1""")
    print("  rows=", n)

    conn.commit()
    print("COMMIT OK")
finally:
    conn.close()
