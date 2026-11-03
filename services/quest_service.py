from db import SqlUtils
db = SqlUtils()

# ======================================================
# 老師任務查看
# ======================================================
def teacher_show_quest(teacher):
    sql = """
    SELECT quest_id 任務編號,quest_name 任務名稱, quest_type 任務類型, condition_type 任務條件類型, condition_value 任務條件數值, reward_xp 獎勵經驗, reward_coin 獎勵金幣, is_repeatable 是否為重複任務, is_active 任務是否啟用
    FROM quest_list
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
