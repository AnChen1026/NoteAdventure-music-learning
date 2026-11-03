"""
api/quests.py｜任務模板與指派

- 老師：列表／建立／指派 → quest_service
- 學生：查看自己的指派 → student_show_quest
"""

from flask import Blueprint, request, jsonify
from api.guards import get_login_teacher, get_login_student, json_safe
from services.quest_service import (
    teacher_show_quest,
    student_show_quest,
    create_quest,
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

    data = request.get_json(silent=True) or {}
    quest_name = str(data.get('quest_name', '')).strip()
    quest_type = data.get('quest_type')
    condition_type = data.get('condition_type')
    condition_value = data.get('condition_value')
    reward_xp = data.get('reward_xp', 0)
    reward_coin = data.get('reward_coin', 0)
    is_repeatable = data.get('is_repeatable', True)

    if quest_name == '':
        return jsonify({'message': '請輸入任務名稱'}), 400
    if quest_type not in QUEST_TYPES:
        return jsonify({'message': '任務類型不正確'}), 400
    if condition_type not in CONDITION_TYPES:
        return jsonify({'message': '任務條件類型不正確'}), 400
    if not isinstance(condition_value, int) or condition_value <= 0:
        return jsonify({'message': '條件數值請輸入正整數'}), 400
    if not isinstance(reward_xp, int) or reward_xp < 0:
        return jsonify({'message': '獎勵經驗請輸入非負整數'}), 400
    if not isinstance(reward_coin, int) or reward_coin < 0:
        return jsonify({'message': '獎勵金幣請輸入非負整數'}), 400

    result = create_quest(
        teacher,
        quest_name,
        quest_type,
        condition_type,
        condition_value,
        reward_xp,
        reward_coin,
        is_repeatable
    )
    if result == '任務新建成功':
        return jsonify({'message': result}), 201
    return jsonify({'message': result}), 500


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
