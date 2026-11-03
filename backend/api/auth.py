"""
api/auth.py｜登入／登出／改密碼／老師註冊

登入成功後會寫入 Flask session（role + id），之後其他 API 用 guards 檢查。
商業邏輯轉呼叫：
- services.teacher_service（老師登入／註冊／改密碼）
- services.student_service（學生登入／改密碼）
"""

from flask import Blueprint, request, jsonify, session
from services.teacher_service import (
    login_teacher,
    create_teacher,
    teacher_email_exists,
    change_teacher_password
)
from services.student_service import login_student, change_student_password
from api.guards import get_login_teacher, get_login_student

auth_bp = Blueprint('auth', __name__)

# 改密碼結果訊息 → HTTP 狀態碼
PASSWORD_STATUS = {
    '密碼修改成功': 200,
    '舊密碼錯誤': 401,
    '密碼修改失敗': 500
}


# ======================================================
# 老師公開資料（不回傳密碼）
# ======================================================
def teacher_public(teacher):
    return {
        'teacher_id': teacher['teacher_id'],
        'teacher_name': teacher['teacher_name'],
        'email': teacher['email']
    }


# ======================================================
# 學生公開資料（不回傳密碼）
# ======================================================
def student_public(student):
    return {
        'student_id': student['student_id'],
        'teacher_id': student['teacher_id'],
        'username': student['username'],
        'student_name': student['student_name'],
        'password_changed': bool(student['password_changed']),
        'total_xp': student['total_xp'],
        'total_coin': student['total_coin']
    }


# ======================================================
# 老師註冊
# ======================================================
@auth_bp.post('/api/teachers/register')
def api_teacher_register():
    data = request.get_json(silent=True) or {}
    teacher_name = str(data.get('teacher_name', '')).strip()
    email = str(data.get('email', '')).strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if teacher_name == '' or email == '' or password == '' or confirm_password == '':
        return jsonify({'message': '請完整填寫姓名、電子信箱與密碼'}), 400
    if password != confirm_password:
        return jsonify({'message': '兩次密碼不一致'}), 400

    if teacher_email_exists(email):
        return jsonify({'message': '此電子信箱已註冊'}), 409

    result = create_teacher(teacher_name, email, password)
    if result == '老師帳號建立成功':
        return jsonify({'message': result}), 201
    return jsonify({'message': result}), 500


# ======================================================
# 老師登入
# ======================================================
@auth_bp.post('/api/teachers/login')
def api_teacher_login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if email == '' or password == '':
        return jsonify({'message': '請輸入電子信箱與密碼'}), 400

    teacher = login_teacher(email, password)
    if not teacher:
        return jsonify({'message': '電子信箱或密碼錯誤'}), 401

    # session：記住這位使用者，之後的 API 才能知道是誰
    session.clear()
    session['role'] = 'teacher'
    session['teacher_id'] = teacher['teacher_id']

    return jsonify({
        'message': '登入成功',
        'role': 'teacher',
        'user': teacher_public(teacher)
    })


# ======================================================
# 學生登入
# ======================================================
@auth_bp.post('/api/students/login')
def api_student_login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if username == '' or password == '':
        return jsonify({'message': '請輸入帳號與密碼'}), 400

    student = login_student(username, password)
    if not student:
        return jsonify({'message': '帳號或密碼錯誤'}), 401

    session.clear()
    session['role'] = 'student'
    session['student_id'] = student['student_id']

    return jsonify({
        'message': '登入成功',
        'role': 'student',
        'user': student_public(student)
    })


# ======================================================
# 查詢目前登入者
# ======================================================
@auth_bp.get('/api/me')
def api_me():
    role = session.get('role')

    if role == 'teacher':
        teacher, error = get_login_teacher()
        if error:
            return jsonify({'message': '尚未登入'}), 401
        return jsonify({
            'role': 'teacher',
            'user': teacher_public(teacher)
        })

    if role == 'student':
        student, error = get_login_student()
        if error:
            return jsonify({'message': '尚未登入'}), 401
        return jsonify({
            'role': 'student',
            'user': student_public(student)
        })

    return jsonify({'message': '尚未登入'}), 401


# ======================================================
# 老師修改密碼
# ======================================================
@auth_bp.post('/api/teachers/change-password')
def api_teacher_change_password():
    teacher, error = get_login_teacher()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if old_password == '' or new_password == '' or confirm_password == '':
        return jsonify({'message': '請完整輸入舊密碼與新密碼'}), 400

    result = change_teacher_password(
        teacher['teacher_id'], old_password, new_password, confirm_password
    )
    return jsonify({'message': result}), PASSWORD_STATUS.get(result, 400)


# ======================================================
# 學生修改密碼
# ======================================================
@auth_bp.post('/api/students/change-password')
def api_student_change_password():
    student, error = get_login_student()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if old_password == '' or new_password == '' or confirm_password == '':
        return jsonify({'message': '請完整輸入舊密碼與新密碼'}), 400

    result = change_student_password(
        student['student_id'], old_password, new_password, confirm_password
    )
    return jsonify({'message': result}), PASSWORD_STATUS.get(result, 400)


# ======================================================
# 登出
# ======================================================
@auth_bp.post('/api/logout')
def api_logout():
    session.clear()
    return jsonify({'message': '已登出'})
