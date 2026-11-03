import os # 檢查檔案是否存在
import shutil # 複製檔案
from datetime import datetime
from db import SqlUtils

db = SqlUtils()

AUDIO_FOLDER = 'uploads/audio' # 音檔存放路徑


# ======================================================
# 儲存音檔並回傳存放路徑
# ======================================================
def save_audio_file(student, source_path):
    os.makedirs(AUDIO_FOLDER, exist_ok=True) # 建立音檔存放路徑
    file_ext = os.path.splitext(source_path)[1] # 檔案副檔名
    file_time = datetime.now().strftime('%Y%m%d_%H%M%S') # 檔案時間
    file_name = f"{student['student_id']}_{file_time}{file_ext}" # 檔案名稱
    audio_url = f'{AUDIO_FOLDER}/{file_name}'
    shutil.copy(source_path, audio_url) # 複製檔案
    return audio_url # 回傳檔案路徑


# ======================================================
# 建立練習錄音紀錄至資料庫
# ======================================================
def create_practice_upload(student, audio_url, song_name, audio_duration):
    sql = """
    INSERT INTO practice_upload (
    student_id,
    audio_url,
    song_name,
    audio_duration
    )
    VALUES (%s, %s, %s, %s)
    """
    rowcount = db.execute(sql,(student['student_id'],audio_url,song_name,audio_duration))
    if rowcount > 0:
        return '練習上傳成功'
    return '練習上傳失敗'


# ======================================================
# 顯示指定學生或全部學生的上傳紀錄
# ======================================================
def teacher_show_practice_upload(teacher, student_id=None):
    sql = """
    SELECT
        p.upload_id,
        s.student_name,
        p.song_name,
        p.audio_duration,
        p.audio_url,
        p.created_at
    FROM practice_upload p
    JOIN student s ON s.student_id = p.student_id
    WHERE s.teacher_id = %s
    """
    params = [teacher['teacher_id']]
    if student_id:
        sql += ' AND p.student_id = %s'
        params.append(student_id)
    sql += ' ORDER BY p.created_at DESC;'

    result = db.query_all(sql, params)
    if result:
        return result
    return '無上傳紀錄'


# ======================================================
# 老師取得單筆上傳（確認是自己學生的）
# ======================================================
def get_teacher_practice_upload(teacher, upload_id):
    sql = """
    SELECT
        p.upload_id,
        p.student_id,
        p.song_name,
        p.audio_duration,
        p.audio_url,
        p.created_at,
        s.student_name
    FROM practice_upload p
    JOIN student s ON s.student_id = p.student_id
    WHERE p.upload_id = %s
      AND s.teacher_id = %s;
    """
    return db.query_one(sql, (upload_id, teacher['teacher_id']))


# ======================================================
# 解析安全的本機音檔路徑（避免路徑穿越）
# ======================================================
def resolve_audio_path(audio_url):
    if not audio_url:
        return None
    abs_folder = os.path.abspath(AUDIO_FOLDER)
    abs_path = os.path.abspath(audio_url)
    try:
        common = os.path.commonpath([abs_folder, abs_path])
    except ValueError:
        return None
    if common != abs_folder:
        return None
    if not os.path.isfile(abs_path):
        return None
    return abs_path
