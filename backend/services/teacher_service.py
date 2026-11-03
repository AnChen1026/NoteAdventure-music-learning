from db import SqlUtils
from utils.password_utils import hash_password, check_password
db = SqlUtils()


# ================================================
# 新增老師功能
# ================================================
def create_teacher(teacher_name, email, password):
    sql = """
    INSERT INTO teacher (teacher_name, email, password_hash)
    VALUES (%s, %s, %s);
    """
    password_hash = hash_password(password)
    result = db.execute(sql, (teacher_name, email, password_hash))

    if result > 0:
        return '老師帳號建立成功'
    else:
        return '老師帳號建立失敗'


# ================================================
# 老師登入功能
# ================================================
def login_teacher(email, password):
    sql = """
    SELECT teacher_id, teacher_name, email, password_hash
    FROM teacher
    WHERE email = %s;
    """
    try:
        result = db.query_one(sql, (email,))
        if result is None:
            print("查無此老師帳號")
            return None
        is_correct = check_password(password, result["password_hash"])
        if is_correct:
            print(f"登入成功，{result['teacher_name']} 老師您好")
            return result
        else:
            print("密碼錯誤")
            return None
    except Exception as e:
        print("老師登入失敗：", e)
        return None


# ================================================
# 檢查電子信箱是否已註冊
# ================================================
def teacher_email_exists(email):
    sql = """
    SELECT teacher_id
    FROM teacher
    WHERE email = %s;
    """
    return db.query_one(sql, (email,)) is not None


# ================================================
# 老師修改密碼（回傳結果訊息）
# ================================================
def change_teacher_password(teacher_id, old_password, new_password, confirm_password):
    row = db.query_one(
        """
        SELECT password_hash
        FROM teacher
        WHERE teacher_id = %s;
        """,
        (teacher_id,)
    )
    if not row or not check_password(old_password, row['password_hash']):
        return '舊密碼錯誤'
    if new_password != confirm_password:
        return '兩次新密碼不一致'
    if new_password == old_password:
        return '新密碼不可與舊密碼相同'

    rowcount = db.execute(
        """
        UPDATE teacher
        SET password_hash = %s
        WHERE teacher_id = %s;
        """,
        (hash_password(new_password), teacher_id)
    )
    if rowcount > 0:
        return '密碼修改成功'
    return '密碼修改失敗'
