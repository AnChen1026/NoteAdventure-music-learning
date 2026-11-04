"""
同一個任務指派被兩個請求同時發獎（例如學生連按兩次上傳）：

兩個執行緒都先讀到 completed = FALSE，之後才各自寫入。
預期只有一個成功發獎，XP、金幣與異動紀錄只增加一次。
"""

import threading

import pytest

from conftest import _server_connection, DB, query_one


def _execute(sql, params=None):
    conn = _server_connection(DB['test_database'])
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.lastrowid
    finally:
        conn.close()


@pytest.fixture
def ready_quest(app):
    teacher_id = _execute(
        "INSERT INTO teacher (teacher_name, email, password_hash) VALUES ('並發老師', 'race@test.local', 'x')"
    )
    student_id = _execute(
        "INSERT INTO student (teacher_id, username, password_hash, student_name) VALUES (%s, 'race_student', 'x', '並發學生')",
        (teacher_id,)
    )
    quest_id = _execute(
        "INSERT INTO quest_list (teacher_id, quest_name, quest_type, condition_type, condition_value, reward_xp, reward_coin) "
        "VALUES (%s, '並發任務', 'HIDDEN', 'PRACTICE_COUNT', 1, 120, 30)",
        (teacher_id,)
    )
    # 進度已達標、尚未發獎
    student_quest_id = _execute(
        "INSERT INTO student_quest (student_id, quest_id, period_key, progress_value) VALUES (%s, %s, 'ONCE', 1)",
        (student_id, quest_id)
    )
    return student_id, student_quest_id


def test_concurrent_reward_is_given_once(ready_quest, monkeypatch):
    from services import reward_service

    student_id, student_quest_id = ready_quest

    # 讓兩個執行緒都讀完「未完成」之後才往下寫，重現競態條件
    barrier = threading.Barrier(2, timeout=10)
    real_query_one = reward_service.db.query_one

    def query_then_wait(sql, params=None):
        result = real_query_one(sql, params)
        barrier.wait()
        return result

    monkeypatch.setattr(reward_service.db, 'query_one', query_then_wait)

    results = []
    threads = [
        threading.Thread(target=lambda: results.append(reward_service.give_quest_reward(student_quest_id)))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len([r for r in results if r]) == 1

    student = query_one('SELECT total_xp, total_coin FROM student WHERE student_id = %s', (student_id,))
    assert (student['total_xp'], student['total_coin']) == (120, 30)

    xp_rows = query_one('SELECT COUNT(*) AS n FROM xp_source WHERE student_id = %s', (student_id,))
    coin_rows = query_one('SELECT COUNT(*) AS n FROM coin_transaction WHERE student_id = %s', (student_id,))
    assert xp_rows['n'] == 1
    assert coin_rows['n'] == 1

    # 寵物階段在同一個 transaction 內依新 XP 更新（120 XP → 幼體）
    pet = query_one(
        'SELECT ps.xp_threshold FROM pet p JOIN pet_stage ps ON ps.stage_id = p.stage_id WHERE p.student_id = %s',
        (student_id,)
    )
    assert pet['xp_threshold'] == 100
