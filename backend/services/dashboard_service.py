from db import SqlUtils

db = SqlUtils()


# ======================================================
# 查詢單一 COUNT 結果
# ======================================================
def _count(sql, params):
    row = db.query_one(sql, params)
    if not row:
        return 0
    return int(row['cnt'])


# ======================================================
# 老師 Dashboard：彙總數字與近期清單
# ======================================================
def get_teacher_dashboard(teacher):
    teacher_id = teacher['teacher_id']

    student_count = _count(
        """
        SELECT COUNT(*) AS cnt
        FROM student
        WHERE teacher_id = %s;
        """,
        (teacher_id,)
    )

    active_quest_count = _count(
        """
        SELECT COUNT(*) AS cnt
        FROM quest_list
        WHERE teacher_id = %s
        AND is_active = TRUE;
        """,
        (teacher_id,)
    )

    # 進行中：未完成，且尚未到期（無期限也算進行中）
    active_assignment_count = _count(
        """
        SELECT COUNT(*) AS cnt
        FROM student_quest sq
        JOIN student s ON s.student_id = sq.student_id
        WHERE s.teacher_id = %s
        AND sq.completed = FALSE
        AND (sq.expires_at IS NULL OR sq.expires_at > NOW());
        """,
        (teacher_id,)
    )

    expired_assignment_count = _count(
        """
        SELECT COUNT(*) AS cnt
        FROM student_quest sq
        JOIN student s ON s.student_id = sq.student_id
        WHERE s.teacher_id = %s
        AND sq.completed = FALSE
        AND sq.expires_at IS NOT NULL
        AND sq.expires_at <= NOW();
        """,
        (teacher_id,)
    )

    upload_count_7d = _count(
        """
        SELECT COUNT(*) AS cnt
        FROM practice_upload p
        JOIN student s ON s.student_id = p.student_id
        WHERE s.teacher_id = %s
        AND p.created_at >= (NOW() - INTERVAL 7 DAY);
        """,
        (teacher_id,)
    )

    pending_redeem_count = _count(
        """
        SELECT COUNT(*) AS cnt
        FROM purchase_record p
        JOIN student s ON s.student_id = p.student_id
        WHERE s.teacher_id = %s
        AND p.status = 'PURCHASED';
        """,
        (teacher_id,)
    )

    students = db.query_all(
        """
        SELECT
            student_id AS 序號,
            username AS 帳號,
            student_name AS 姓名,
            total_xp AS 經驗值,
            total_coin AS 金幣數
        FROM student
        WHERE teacher_id = %s
        ORDER BY student_id;
        """,
        (teacher_id,)
    ) or []

    recent_uploads = db.query_all(
        """
        SELECT
            s.student_name AS 學生,
            p.song_name AS 曲目,
            p.audio_duration AS 秒數,
            p.created_at AS 上傳時間
        FROM practice_upload p
        JOIN student s ON s.student_id = p.student_id
        WHERE s.teacher_id = %s
        ORDER BY p.created_at DESC
        LIMIT 10;
        """,
        (teacher_id,)
    ) or []

    active_assignments = db.query_all(
        """
        SELECT
            s.student_name AS 學生,
            q.quest_name AS 任務,
            sq.progress_value AS 目前進度,
            q.condition_value AS 目標,
            sq.expires_at AS 截止時間
        FROM student_quest sq
        JOIN student s ON s.student_id = sq.student_id
        JOIN quest_list q ON q.quest_id = sq.quest_id
        WHERE s.teacher_id = %s
        AND sq.completed = FALSE
        AND (sq.expires_at IS NULL OR sq.expires_at > NOW())
        ORDER BY sq.expires_at IS NULL, sq.expires_at, sq.student_quest_id
        LIMIT 10;
        """,
        (teacher_id,)
    ) or []

    pending_redeems = db.query_all(
        """
        SELECT
            s.student_name AS 學生,
            i.item_name AS 商品,
            p.price AS 價格,
            p.created_at AS 購買時間
        FROM purchase_record p
        JOIN student s ON s.student_id = p.student_id
        JOIN shop_item i ON i.item_id = p.item_id
        WHERE s.teacher_id = %s
        AND p.status = 'PURCHASED'
        ORDER BY p.created_at
        LIMIT 10;
        """,
        (teacher_id,)
    ) or []

    return {
        'summary': {
            'student_count': student_count,
            'active_quest_count': active_quest_count,
            'active_assignment_count': active_assignment_count,
            'expired_assignment_count': expired_assignment_count,
            'upload_count_7d': upload_count_7d,
            'pending_redeem_count': pending_redeem_count
        },
        'students': students,
        'recent_uploads': recent_uploads,
        'active_assignments': active_assignments,
        'pending_redeems': pending_redeems
    }
