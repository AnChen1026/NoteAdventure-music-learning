from datetime import datetime, timedelta

from db import SqlUtils
db = SqlUtils()

# ======================================================
# 老師任務查看
# ======================================================
def teacher_show_quest(teacher):
    sql = """
    SELECT quest_id 任務編號,quest_name 任務名稱, quest_type 任務類型, condition_type 任務條件類型, condition_value 任務條件數值, reward_xp 獎勵經驗, reward_coin 獎勵金幣, is_repeatable 是否為重複任務, is_active 任務是否啟用,
           (SELECT COUNT(*) FROM student_quest sq WHERE sq.quest_id = q.quest_id) 指派次數
    FROM quest_list q
    WHERE teacher_id = %s;
    """
    result = db.query_all(sql, (teacher['teacher_id'],))
    if result:
        return result
    return '無任務資料'

# ======================================================
# 學生任務查看
# ======================================================
def student_show_quest(student):
    sql = """
    SELECT q.quest_name, q.quest_type, q.condition_type, q.condition_value,
           q.reward_xp, q.reward_coin, sq.progress_value, sq.expires_at,
           CASE
               WHEN sq.completed = TRUE THEN 'COMPLETED'
               WHEN sq.expires_at IS NULL OR sq.expires_at > NOW() THEN 'ACTIVE'
               ELSE 'EXPIRED'
           END AS quest_status
    FROM student_quest sq
    JOIN quest_list q ON q.quest_id = sq.quest_id
    WHERE sq.student_id = %s
    AND (q.quest_type != 'HIDDEN' OR sq.completed = TRUE)
    ORDER BY sq.completed, sq.expires_at;
    """
    result = db.query_all(sql, (student['student_id'],))
    if result:
        return result
    return '無任務資料'

# ======================================================
# 更新任務進度
# ======================================================
def update_quest_progress(student):
    # 只計算進行中，且 MVP 第一版支援的任務條件
    sql = """
    SELECT sq.student_quest_id, sq.assigned_at, sq.expires_at,
           q.quest_name, q.condition_type, q.condition_value
    FROM student_quest sq
    JOIN quest_list q ON q.quest_id = sq.quest_id
    WHERE sq.student_id = %s
    AND sq.completed = FALSE
    AND (sq.expires_at IS NULL OR sq.expires_at > NOW())
    AND q.condition_type IN ('PRACTICE_COUNT', 'DISTINCT_SONGS');
    """
    quest_result = db.query_all(sql, (student['student_id'],))
    if not quest_result:
        return []

    progress_list = []
    for quest in quest_result:
        if quest['condition_type'] == 'DISTINCT_SONGS':
            count_type = 'COUNT(DISTINCT song_name)'
        else:
            count_type = 'COUNT(*)'

        # 只計算任務期間內的上傳
        count_sql = f"""
        SELECT {count_type} AS progress_value
        FROM practice_upload
        WHERE student_id = %s
        AND created_at >= %s
        """
        params = [student['student_id'], quest['assigned_at']]
        if quest['expires_at']:
            count_sql += ' AND created_at <= %s'
            params.append(quest['expires_at'])

        progress_value = db.query_one(count_sql, params)['progress_value']

        update_sql = """
        UPDATE student_quest
        SET progress_value = %s
        WHERE student_quest_id = %s;
        """
        db.execute(update_sql, (progress_value, quest['student_quest_id']))

        progress_list.append({
            'student_quest_id': quest['student_quest_id'],
            'quest_name': quest['quest_name'],
            'progress_value': progress_value,
            'condition_value': quest['condition_value']
        })
    return progress_list


# ======================================================
# 老師建立任務
# ======================================================
def create_quest(teacher, quest_name, quest_type, condition_type, condition_value,
                 reward_xp, reward_coin, is_repeatable):
    sql = """
    INSERT INTO quest_list (
    teacher_id,
    quest_name,
    quest_type,
    condition_type,
    condition_value,
    reward_xp,
    reward_coin,
    is_repeatable
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    rowcount = db.execute(
        sql,
        (
            teacher['teacher_id'],
            quest_name,
            quest_type,
            condition_type,
            condition_value,
            reward_xp,
            reward_coin,
            bool(is_repeatable)
        )
    )
    if rowcount > 0:
        return '任務新建成功'
    return '任務建立失敗'


# ======================================================
# 依任務類型計算期限與期間代碼
# DAILY 一天、WEEKLY 七天（ISO 週）、HIDDEN 無期限
# ======================================================
def quest_period(quest_type, assigned_at):
    if quest_type == 'HIDDEN':
        return None, 'ONCE'
    if quest_type == 'DAILY':
        return assigned_at + timedelta(days=1), assigned_at.strftime('%Y-%m-%d')
    iso = assigned_at.isocalendar()
    return assigned_at + timedelta(days=7), f'{iso.year}-W{iso.week:02d}'


# ======================================================
# 老師指派任務給學生
# 成功回傳 dict；失敗回傳錯誤訊息字串
# ======================================================
def assign_quest(teacher, quest_id, student_id):
    # 只能指派自己啟用中的任務
    quest = db.query_one(
        """
        SELECT quest_id, quest_name, quest_type
        FROM quest_list
        WHERE quest_id = %s
        AND teacher_id = %s
        AND is_active = TRUE;
        """,
        (quest_id, teacher['teacher_id'])
    )
    if not quest:
        return '查無此任務或任務未啟用'

    # 只能指派給自己的學生
    student = db.query_one(
        """
        SELECT student_id, student_name
        FROM student
        WHERE student_id = %s
        AND teacher_id = %s;
        """,
        (student_id, teacher['teacher_id'])
    )
    if not student:
        return '查無此學生'

    # 去掉微秒：MySQL DATETIME 會四捨五入到秒，可能把指派時間進位到下一秒，漏算同一秒內的上傳
    assigned_at = datetime.now().replace(microsecond=0)
    expires_at, period_key = quest_period(quest['quest_type'], assigned_at)

    exist = db.query_one(
        """
        SELECT student_quest_id
        FROM student_quest
        WHERE student_id = %s
        AND quest_id = %s
        AND period_key = %s;
        """,
        (student_id, quest_id, period_key)
    )
    if exist:
        return f'此期間已指派過該任務（{period_key}）'

    rowcount = db.execute(
        """
        INSERT INTO student_quest (
        student_id,
        quest_id,
        assigned_at,
        expires_at,
        period_key
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (student_id, quest_id, assigned_at, expires_at, period_key)
    )
    if rowcount > 0:
        return {
            'period_key': period_key,
            'assigned_at': assigned_at,
            'expires_at': expires_at
        }
    return '任務指派失敗'


# ======================================================
# 查詢老師自己的任務（含指派次數）；查無回傳 None
# ======================================================
def get_teacher_quest(teacher, quest_id):
    return db.query_one(
        """
        SELECT q.quest_id, q.quest_type, q.condition_type,
               (SELECT COUNT(*) FROM student_quest sq WHERE sq.quest_id = q.quest_id) AS assigned_count
        FROM quest_list q
        WHERE q.quest_id = %s
        AND q.teacher_id = %s;
        """,
        (quest_id, teacher['teacher_id'])
    )


# ======================================================
# 老師修改任務
# 已指派過的任務不可改任務類型與條件類型（避免期限與進度計算跟歷史不一致）
# ======================================================
def update_quest(teacher, quest_id, quest_name, quest_type, condition_type, condition_value,
                 reward_xp, reward_coin, is_repeatable):
    quest = get_teacher_quest(teacher, quest_id)
    if not quest:
        return '查無此任務'
    if quest['assigned_count'] > 0 and (
            quest['quest_type'] != quest_type or quest['condition_type'] != condition_type):
        return '任務已指派過，不可修改任務類型或條件類型'

    rowcount = db.execute(
        """
        UPDATE quest_list
        SET quest_name = %s,
            quest_type = %s,
            condition_type = %s,
            condition_value = %s,
            reward_xp = %s,
            reward_coin = %s,
            is_repeatable = %s
        WHERE quest_id = %s
        AND teacher_id = %s;
        """,
        (quest_name, quest_type, condition_type, condition_value,
         reward_xp, reward_coin, bool(is_repeatable), quest_id, teacher['teacher_id'])
    )
    # 內容沒變時 rowcount 為 0，也算成功；-1 才是執行失敗
    if rowcount < 0:
        return '任務修改失敗'
    return '任務修改成功'


# ======================================================
# 老師啟用／停用任務
# 停用後不可再指派；已指派的任務照常進行
# ======================================================
def set_quest_active(teacher, quest_id, is_active):
    if not get_teacher_quest(teacher, quest_id):
        return '查無此任務'

    rowcount = db.execute(
        """
        UPDATE quest_list
        SET is_active = %s
        WHERE quest_id = %s
        AND teacher_id = %s;
        """,
        (bool(is_active), quest_id, teacher['teacher_id'])
    )
    if rowcount < 0:
        return '任務狀態更新失敗'
    return '任務已啟用' if is_active else '任務已停用'


# ======================================================
# 老師刪除任務
# 只能刪除從未指派過的任務；有指派紀錄請改用停用，保留任務歷史
# ======================================================
def delete_quest(teacher, quest_id):
    quest = get_teacher_quest(teacher, quest_id)
    if not quest:
        return '查無此任務'
    if quest['assigned_count'] > 0:
        return '任務已有指派紀錄，無法刪除，請改用停用'

    rowcount = db.execute(
        """
        DELETE FROM quest_list
        WHERE quest_id = %s
        AND teacher_id = %s;
        """,
        (quest_id, teacher['teacher_id'])
    )
    if rowcount > 0:
        return '任務已刪除'
    return '任務刪除失敗'
