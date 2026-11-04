"""
線上展示用示範資料（NOTEADVENTURE_DEMO=1）：

啟動時建表略過已存在的資料表 → 建立示範資料（走正式上傳與發獎流程）
→ 示範帳號可登入、不能改密碼 → 重複執行不會重複建立
"""

import pytest

from conftest import query_one


@pytest.fixture
def demo_on(app, monkeypatch):
    monkeypatch.setenv('NOTEADVENTURE_DEMO', '1')


def test_init_db_skips_existing_tables(app):
    from init_db import create_tables_if_missing
    assert create_tables_if_missing() == '資料表已存在，略過建表'


def test_seed_demo_and_lock_password(demo_on, make_client):
    from demo import seed_demo, DEMO_TEACHER_EMAIL, DEMO_TEACHER_PASSWORD, \
        DEMO_STUDENT_USERNAME, DEMO_STUDENT_PASSWORD

    assert seed_demo() == '示範資料建立完成'
    assert seed_demo() == '示範資料已存在，已重設密碼'

    student = query_one('SELECT total_xp, total_coin FROM student WHERE username = %s',
                        (DEMO_STUDENT_USERNAME,))
    assert student['total_xp'] > 0 and student['total_coin'] > 0

    student_client = make_client()
    response = student_client.post('/api/students/login', json={
        'username': DEMO_STUDENT_USERNAME, 'password': DEMO_STUDENT_PASSWORD})
    assert response.status_code == 200
    response = student_client.post('/api/students/change-password', json={
        'old_password': DEMO_STUDENT_PASSWORD, 'new_password': 'x', 'confirm_password': 'x'})
    assert response.status_code == 403

    teacher_client = make_client()
    response = teacher_client.post('/api/teachers/login', json={
        'email': DEMO_TEACHER_EMAIL, 'password': DEMO_TEACHER_PASSWORD})
    assert response.status_code == 200
    response = teacher_client.post('/api/teachers/change-password', json={
        'old_password': DEMO_TEACHER_PASSWORD, 'new_password': 'x', 'confirm_password': 'x'})
    assert response.status_code == 403
    response = teacher_client.post('/api/students/reset-password',
                                   json={'username': DEMO_STUDENT_USERNAME})
    assert response.status_code == 403


def test_db_session_uses_app_timezone(app):
    # 雲端 MySQL 預設 UTC；連線時改成與 Flask 相同時區，NOW() 才會等於 datetime.now()
    from datetime import datetime
    from db import SqlUtils
    row = SqlUtils().query_one('SELECT NOW() AS db_now')
    assert abs((row['db_now'] - datetime.now()).total_seconds()) < 60
