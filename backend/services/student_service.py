from db import SqlUtils
from utils.username_utils import generate_student_username, generate_temp_password
from utils.password_utils import hash_password, check_password

db = SqlUtils()


# ================================================
# 展示學生清單
# ================================================
def show_student(teacher):
    sql = """
    select student_id 序號, username 帳號, student_name 姓名, total_xp 經驗值, total_coin 金幣數 from student where teacher_id = %s;
    """

    result = db.query_all(sql, teacher['teacher_id'])
    if result:
        print('開啟學生列表')
        return result
    else:
        return '沒有學生資料'


# ================================================
# 查詢單一學生資料
# ================================================
def get_student(student_id):
    sql = """
    SELECT *
    FROM student
    WHERE student_id = %s;
    """
    return db.query_one(sql, (student_id,))


# ================================================
# 新增學生並取得帳號密碼
# ================================================
def create_student(teacher, student_name):
    user_name = generate_student_username(teacher['teacher_id'])
    password = generate_temp_password()
    password_hash = hash_password(password)
    sql = """
    INSERT INTO student (teacher_id, username, password_hash, student_name)
    VALUES (%s, %s, %s, %s);
    """

    rowcount = db.execute(sql, (teacher['teacher_id'], user_name, password_hash, student_name))
    if rowcount > 0:
        return user_name, password
    return None


# ================================================
# 老師重置學生密碼
# ================================================
def reset_student_password(username):
    password = generate_temp_password()
    password_hash = hash_password(password)
    sql = """
    UPDATE student
    SET password_hash = %s,
        password_changed = FALSE
    WHERE username = %s;
    """
    rowcount = db.execute(sql, (password_hash, username))
    if rowcount > 0:
        return f'密碼修改成功\n新密碼{password}'
    else:
        return '找不到該學生帳號'


# ================================================
# 學生登入功能
# ================================================
def login_student(username, password):
    sql = """
    SELECT *
    FROM student
    WHERE username = %s;
    """
    try:
        result = db.query_one(sql, (username,))
        if result is None:
            print("查無此學生帳號")
            return None
        is_correct = check_password(password, result["password_hash"])
        if is_correct:
            print(f"登入成功，{result['student_name']} 您好")
            return result
        else:
            print("密碼錯誤")
            return None
    except Exception as e:
        print("登入失敗：", e)
        return None


# ================================================
# 學生修改密碼（回傳結果訊息；成功後標記已改過初始密碼）
# ================================================
def change_student_password(student_id, old_password, new_password, confirm_password):
    row = db.query_one(
        """
        SELECT password_hash
        FROM student
        WHERE student_id = %s;
        """,
        (student_id,)
    )
    if not row or not check_password(old_password, row['password_hash']):
        return '舊密碼錯誤'
    if new_password != confirm_password:
        return '兩次新密碼不一致'
    if new_password == old_password:
        return '新密碼不可與舊密碼相同'

    rowcount = db.execute(
        """
        UPDATE student
        SET password_hash = %s,
            password_changed = TRUE
        WHERE student_id = %s;
        """,
        (hash_password(new_password), student_id)
    )
    if rowcount > 0:
        return '密碼修改成功'
    return '密碼修改失敗'


# ================================================
# 確認學生帳號屬於這位老師
# ================================================
def teacher_has_student(teacher, username):
    sql = """
    SELECT student_id
    FROM student
    WHERE username = %s
    AND teacher_id = %s;
    """
    return db.query_one(sql, (username, teacher['teacher_id'])) is not None
