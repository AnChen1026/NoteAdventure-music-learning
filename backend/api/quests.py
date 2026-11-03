"""
api/quests.py｜任務模板與指派

- 老師：列表／建立／修改／啟停／刪除／指派 → quest_service
- 學生：查看自己的指派 → student_show_quest
"""

from flask import Blueprint, request, jsonify
from api.guards import get_login_teacher, get_login_student, json_safe
from services.quest_service import (
    teacher_show_quest,
    student_show_quest,
    create_quest,
    update_quest,
    set_quest_active,
    delete_quest,
    assign_quest
)

quests_bp = Blueprint('quests', __name__)

QUEST_TYPES = {'DAILY', 'WEEKLY', 'HIDDEN'}
CONDITION_TYPES = {
    'PRACTICE_COUNT',
    'PRACTICE_DAYS',
    'DISTINCT_SONGS',
    'CONSECUTIVE_DAYS',
    'TOTAL_UPLOADS',
    'RETURN_AFTER_GAP'
}


# ======================================================
# 讀取並驗證任務表單（建立、修改共用）
# 回傳 (欄位 dict, None) 或 (None, 錯誤訊息)
# ======================================================
def read_quest_form():
    data = request.get_json(silent=True) or {}
    form = {
        'quest_name': str(data.get('quest_name', '')).strip(),
        'quest_type': data.get('quest_type'),
        'condition_type': data.get('condition_type'),
        'condition_value': data.get('condition_value'),
        'reward_xp': data.get('reward_xp', 0),
        'reward_coin': data.get('reward_coin', 0),
        'is_repeatable': data.get('is_repeatable', True)
    }

    if form['quest_name'] == '':
        return None, '請輸入任務名稱'
    if form['quest_type'] not in QUEST_TYPES:
        return None, '任務類型不正確'
    if form['condition_type'] not in CONDITION_TYPES:
        return None, '任務條件類型不正確'
    if not isinstance(form['condition_value'], int) or form['condition_value'] <= 0:
        return None, '條件數值請輸入正整數'
    if not isinstance(form['reward_xp'], int) or form['reward_xp'] < 0:
        return None, '獎勵經驗請輸入非負整數'
    if not isinstance(form['reward_coin'], int) or form['reward_coin'] < 0:
        return None, '獎勵金幣請輸入非負整數'
    return form, None


# ======================================================
# 老師查看自己的任務清單
# ======================================================
@quests_bp.get('/api/quests')
def api_list_quests():
    teacher, error = get_login_teacher()
    if error:
        return error

    result = teacher_show_quest(teacher)
    if isinstance(result, str):
        return jsonify({'message': result, 'data': []})
    return jsonify({'data': json_safe(result)})


# ======================================================
# 老師建立任務
# ======================================================
@quests_bp.post('/api/quests')
def api_create_quest():
    teacher, error = get_login_teacher()
    if error:
        return error

    form, message = read_quest_form()
    if message:
        return jsonify({'message': message}), 400

    result = create_quest(teacher, **form)
    if result == '任務新建成功':
        return jsonify({'message': result}), 201
    return jsonify({'message': result}), 500


# ======================================================
# 老師修改任務
# ======================================================
@quests_bp.put('/api/quests/<int:quest_id>')
def api_update_quest(quest_id):
    teacher, error = get_login_teacher()
    if error:
        return error

    form, message = read_quest_form()
    if message:
        return jsonify({'message': message}), 400

    result = update_quest(teacher, quest_id, **form)
    if result == '任務修改成功':
        return jsonify({'message': result})
    if result == '查無此任務':
        return jsonify({'message': result}), 404
    if result == '任務修改失敗':
        return jsonify({'message': result}), 500
    return jsonify({'message': result}), 409


# ======================================================
# 老師啟用／停用任務
# ======================================================
@quests_bp.patch('/api/quests/<int:quest_id>/active')
def api_set_quest_active(quest_id):
    teacher, error = get_login_teacher()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    is_active = data.get('is_active')
    if not isinstance(is_active, bool):
        return jsonify({'message': '請提供 is_active（true／false）'}), 400

    result = set_quest_active(teacher, quest_id, is_active)
    if result == '查無此任務':
        return jsonify({'message': result}), 404
    if result == '任務狀態更新失敗':
        return jsonify({'message': result}), 500
    return jsonify({'message': result})


# ======================================================
# 老師刪除任務（只限從未指派過的任務）
# ======================================================
@quests_bp.delete('/api/quests/<int:quest_id>')
def api_delete_quest(quest_id):
    teacher, error = get_login_teacher()
    if error:
        return error

    result = delete_quest(teacher, quest_id)
    if result == '任務已刪除':
        return jsonify({'message': result})
    if result == '查無此任務':
        return jsonify({'message': result}), 404
    if result == '任務刪除失敗':
        return jsonify({'message': result}), 500
    return jsonify({'message': result}), 409


# ======================================================
# 老師指派任務給學生
# ======================================================
@quests_bp.post('/api/quests/<int:quest_id>/assign')
def api_assign_quest(quest_id):
    teacher, error = get_login_teacher()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    student_id = data.get('student_id')
    if not isinstance(student_id, int):
        return jsonify({'message': '請提供學生編號 student_id'}), 400

    result = assign_quest(teacher, quest_id, student_id)
    if isinstance(result, str):
        if result.startswith('此期間已指派過'):
            return jsonify({'message': result}), 409
        if result == '任務指派失敗':
            return jsonify({'message': result}), 500
        return jsonify({'message': result}), 404

    return jsonify({
        'message': '任務指派成功',
        'period_key': result['period_key'],
        'assigned_at': json_safe(result['assigned_at']),
        'expires_at': json_safe(result['expires_at'])
    }), 201


# ======================================================
# 學生查看自己的任務
# ======================================================
@quests_bp.get('/api/students/<int:student_id>/quests')
def api_student_quests(student_id):
    student, error = get_login_student()
    if error:
        return error
    if student['student_id'] != student_id:
        return jsonify({'message': '只能查看自己的任務'}), 403

    result = student_show_quest(student)
    if isinstance(result, str):
        return jsonify({'message': result, 'data': []})
    return jsonify({'data': json_safe(result)})
