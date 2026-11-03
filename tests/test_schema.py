"""
建表腳本：在全新的空資料庫上，backend/sql/music_rpg_schema_v2.sql 每一句都要能執行成功。
"""

from conftest import query_one


def test_schema_runs_on_empty_database(schema_failures):
    assert schema_failures == [], '建表腳本有語句執行失敗：\n' + '\n'.join(schema_failures)


def test_pet_stages_seeded(app):
    row = query_one('SELECT COUNT(*) AS n FROM pet_stage')
    assert row['n'] == 4
