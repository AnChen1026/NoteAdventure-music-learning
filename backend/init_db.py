"""
backend/init_db.py｜容器啟動時準備資料庫

1. 資料庫沒有資料表時，執行 sql/music_rpg_schema_v2.sql 建表
   （本機 docker compose 由 MySQL 自動建表，這裡會直接略過）
2. NOTEADVENTURE_DEMO=1 時建立線上展示用示範資料

執行：python backend/init_db.py
"""

import re

from db import SqlUtils
from paths import project_path
from demo import demo_enabled, seed_demo

SCHEMA_PATH = project_path('backend', 'sql', 'music_rpg_schema_v2.sql')

db = SqlUtils()


# ======================================================
# 把 schema 檔拆成一句一句（略過 -- 註解行）
# ======================================================
def schema_statements():
    with open(SCHEMA_PATH, encoding='utf-8') as file:
        lines = [line for line in file if not line.strip().startswith('--')]
    text = ''.join(lines)
    return [part.strip() for part in re.split(r';\s*(?:\n|$)', text) if part.strip()]


def create_tables_if_missing():
    exist = db.query_one(
        """
        SELECT COUNT(*) AS n
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name = 'teacher';
        """
    )
    if exist['n'] > 0:
        return '資料表已存在，略過建表'
    if not db.execute_transaction([(sql, None) for sql in schema_statements()]):
        raise RuntimeError('建表失敗，請查看上方錯誤訊息')
    return '建表完成'


if __name__ == '__main__':
    print(create_tables_if_missing())
    if demo_enabled():
        print(seed_demo())
