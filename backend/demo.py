"""
backend/demo.py｜線上展示用示範帳號與資料

NOTEADVENTURE_DEMO=1 時：
- 啟動時建立示範老師、學生、任務、商品與練習紀錄（已存在就只重設密碼）
- 示範帳號不能改密碼，避免公開帳號被別人鎖住
"""

import io
import os
import tempfile
import wave

from db import SqlUtils
from utils.password_utils import hash_password
from services.quest_service import create_quest, assign_quest, update_quest_progress
from services.reward_service import give_quest_rewards
from services.shop_service import create_shop_item
from services.practice_service import save_audio_file, create_practice_upload

db = SqlUtils()

DEMO_TEACHER_EMAIL = 'demo@noteadventure.app'
DEMO_TEACHER_PASSWORD = 'demo1234'
DEMO_STUDENT_USERNAME = 'demo_student'
DEMO_STUDENT_PASSWORD = 'demo1234'


def demo_enabled():
    return os.environ.get('NOTEADVENTURE_DEMO', '').lower() in ('1', 'true', 'yes')


def is_demo_teacher(teacher):
    return demo_enabled() and teacher.get('email') == DEMO_TEACHER_EMAIL


def is_demo_student(student):
    return demo_enabled() and student.get('username') == DEMO_STUDENT_USERNAME


# ======================================================
# 產生一段無聲 wav 當示範錄音
# ======================================================
def _silent_wav(seconds):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    with wave.open(temp, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(8000)
        wav_file.writeframes(b'\x00\x00' * 8000 * seconds)
    temp.close()
    return temp.name


def _practice(student, song_name, seconds):
    path = _silent_wav(seconds)
    try:
        create_practice_upload(student, save_audio_file(student, path), song_name, seconds)
    finally:
        os.remove(path)


# ======================================================
# 建立示範資料；已存在則只把密碼重設回公開密碼
# ======================================================
def seed_demo():
    teacher = db.query_one('SELECT * FROM teacher WHERE email = %s', (DEMO_TEACHER_EMAIL,))
    if teacher:
        db.execute('UPDATE teacher SET password_hash = %s WHERE teacher_id = %s',
                   (hash_password(DEMO_TEACHER_PASSWORD), teacher['teacher_id']))
        db.execute('UPDATE student SET password_hash = %s WHERE username = %s',
                   (hash_password(DEMO_STUDENT_PASSWORD), DEMO_STUDENT_USERNAME))
        # 重算示範學生的任務進度，補發已達標的獎勵
        student = db.query_one('SELECT * FROM student WHERE username = %s', (DEMO_STUDENT_USERNAME,))
        if student:
            give_quest_rewards(update_quest_progress(student))
        return '示範資料已存在，已重設密碼'

    db.execute('INSERT INTO teacher (teacher_name, email, password_hash) VALUES (%s, %s, %s)',
               ('示範老師', DEMO_TEACHER_EMAIL, hash_password(DEMO_TEACHER_PASSWORD)))
    teacher = db.query_one('SELECT * FROM teacher WHERE email = %s', (DEMO_TEACHER_EMAIL,))

    # 示範學生已改過密碼，登入後不會被要求改密碼
    db.execute(
        """
        INSERT INTO student (teacher_id, username, password_hash, student_name, password_changed)
        VALUES (%s, %s, %s, %s, TRUE)
        """,
        (teacher['teacher_id'], DEMO_STUDENT_USERNAME, hash_password(DEMO_STUDENT_PASSWORD), '小音')
    )
    student = db.query_one('SELECT * FROM student WHERE username = %s', (DEMO_STUDENT_USERNAME,))

    quests = [
        ('每日練琴一次', 'DAILY', 'PRACTICE_COUNT', 1, 20, 10),
        ('本週練習五次', 'WEEKLY', 'PRACTICE_COUNT', 5, 80, 40),
        ('本週練三首不同曲子', 'WEEKLY', 'DISTINCT_SONGS', 3, 60, 30),
        ('第一次上傳練習', 'HIDDEN', 'PRACTICE_COUNT', 1, 50, 20),
    ]
    for name, quest_type, condition_type, value, xp, coin in quests:
        create_quest(teacher, name, quest_type, condition_type, value, xp, coin, True)
    for quest in db.query_all('SELECT quest_id FROM quest_list WHERE teacher_id = %s',
                              (teacher['teacher_id'],)):
        assign_quest(teacher, quest['quest_id'], student['student_id'])

    create_shop_item(teacher, '寵物帽子', 'VIRTUAL', 30, None, '讓寵物戴上小帽子')
    create_shop_item(teacher, '貼紙一張', 'PHYSICAL', 20, 10, '下次上課時跟老師領取')
    create_shop_item(teacher, '下課選一首喜歡的歌', 'PHYSICAL', 80, None, '下課前五分鐘由你選曲')

    # 走正式流程：上傳 → 更新進度 → 發獎
    for song_name, seconds in (('小星星', 3), ('小蜜蜂', 4)):
        _practice(student, song_name, seconds)
        give_quest_rewards(update_quest_progress(student))
    return '示範資料建立完成'
