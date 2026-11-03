"""
api/dashboard.py｜首頁摘要數字

- 老師 Streamlit「首頁」→ GET /api/dashboard → get_teacher_dashboard
"""

from flask import Blueprint, jsonify
from api.guards import get_login_teacher, json_safe
from services.dashboard_service import get_teacher_dashboard

dashboard_bp = Blueprint('dashboard', __name__)


# ======================================================
# 老師首頁 Dashboard
# ======================================================
@dashboard_bp.get('/api/dashboard')
def api_teacher_dashboard():
    teacher, error = get_login_teacher()
    if error:
        return error

    data = get_teacher_dashboard(teacher)
    return jsonify({'data': json_safe(data)})
