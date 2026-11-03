"""
tests/conftest.py｜測試共用設定

- 讀取專案根目錄 config.ini 的連線資訊，但一律改用「<資料庫名稱>_test」測試資料庫
- 每次測試開始時：DROP → CREATE 測試資料庫，再逐句執行 sql/music_rpg_schema_v2.sql
- 上傳的音檔寫到暫存資料夾，不會留在專案裡
正式資料庫不會被讀寫。
"""

import configparser
import os
import re
import sys
from pathlib import Path

import pymysql
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / 'sql' / 'music_rpg_schema_v2.sql'
sys.path.insert(0, str(ROOT))


# ======================================================
# 連線設定：環境變數優先，其次 config.ini
# ======================================================
def _db_settings():
    config = configparser.ConfigParser()
    config.read(ROOT / 'config.ini', encoding='utf-8')

    def setting(env_name, key, default):
        value = os.environ.get(env_name)
        if value:
            return value
        if config.has_option('DB', key):
            return config.get('DB', key)
        return default

    base_name = setting('NOTEADVENTURE_DB_NAME', 'database', 'music_rpg_v2')
    test_name = os.environ.get('NOTEADVENTURE_TEST_DB_NAME') or f'{base_name}_test'
    return {
        'host': setting('NOTEADVENTURE_DB_HOST', 'host', 'localhost'),
        'user': setting('NOTEADVENTURE_DB_USER', 'user', 'root'),
        'password': setting('NOTEADVENTURE_DB_PASSWORD', 'password', ''),
        'port': int(setting('NOTEADVENTURE_DB_PORT', 'port', '3306')),
        'test_database': test_name,
    }


DB = _db_settings()

# 安全檢查：只允許名稱以 _test 結尾的資料庫，避免誤刪正式資料
if not DB['test_database'].endswith('_test'):
    raise RuntimeError(f"測試資料庫名稱必須以 _test 結尾：{DB['test_database']}")

# 讓 db.py 連到測試資料庫（db.py 會優先讀環境變數）
os.environ['NOTEADVENTURE_DB_HOST'] = DB['host']
os.environ['NOTEADVENTURE_DB_USER'] = DB['user']
os.environ['NOTEADVENTURE_DB_PASSWORD'] = DB['password']
os.environ['NOTEADVENTURE_DB_PORT'] = str(DB['port'])
os.environ['NOTEADVENTURE_DB_NAME'] = DB['test_database']


# ======================================================
# 把 schema 檔拆成一句一句（略過 -- 註解行）
# ======================================================
def schema_statements():
    lines = []
    for line in SCHEMA_PATH.read_text(encoding='utf-8').splitlines():
        if line.strip().startswith('--'):
            continue
        lines.append(line)
    text = '\n'.join(lines)
    return [part.strip() for part in re.split(r';\s*(?:\n|$)', text) if part.strip()]


def _server_connection(database=None):
    return pymysql.connect(
        host=DB['host'],
        user=DB['user'],
        password=DB['password'],
        port=DB['port'],
        database=database,
        charset='utf8mb4',
        autocommit=True,
    )


# ======================================================
# 重建測試資料庫；回傳 schema 中執行失敗的語句
# ======================================================
def rebuild_test_database():
    name = DB['test_database']
    conn = _server_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP DATABASE IF EXISTS `{name}`')
            cursor.execute(
                f'CREATE DATABASE `{name}` '
                'DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci'
            )
    finally:
        conn.close()

    failures = []
    conn = _server_connection(name)
    try:
        with conn.cursor() as cursor:
            for statement in schema_statements():
                try:
                    cursor.execute(statement)
                except pymysql.MySQLError as error:
                    first_line = statement.splitlines()[0][:60]
                    failures.append(f'{first_line} → {error.args[0]} {error.args[1]}')
    finally:
        conn.close()
    return failures


@pytest.fixture(scope='session')
def schema_failures():
    return rebuild_test_database()


@pytest.fixture(scope='session')
def app(schema_failures, tmp_path_factory):
    # 上傳音檔用相對路徑 uploads/audio，切到暫存資料夾避免寫進專案
    work_dir = tmp_path_factory.mktemp('work')
    old_cwd = os.getcwd()
    os.chdir(work_dir)

    from app import create_app
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    yield flask_app

    os.chdir(old_cwd)


@pytest.fixture(scope='session')
def make_client(app):
    """每呼叫一次就是一個獨立的瀏覽器（各自的登入 cookie）。"""
    def _make():
        return app.test_client()
    return _make


def query_one(sql, params=None):
    """測試用：直接查測試資料庫。"""
    conn = _server_connection(DB['test_database'])
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()
    finally:
        conn.close()
