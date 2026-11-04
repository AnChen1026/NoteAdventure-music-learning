"""
NoteAdventure｜Flask 進入點（Application Factory）

報告時可以這樣講整條線：

1. 啟動：flask --app backend/app.py run  →  讀取下方的 app = create_app()
2. 前端（Vue：/student 學生、/teacher 老師）用 fetch 打 /api/...
3. 前端打包在 frontend/dist，由本檔一併提供
4. api/*.py 負責收請求、檢查登入（session）、再呼叫 services/
5. services/ 負責商業邏輯與資料庫（你已熟悉，這裡不改）

本檔只做三件事：
- 建立 Flask app、設定 session cookie
- 掛上各功能 Blueprint（api/）
- 提供前端網頁（frontend/dist）與素材路由（material/）
"""

import os

from flask import Flask, jsonify, send_from_directory

from paths import project_path

# 各功能的「路由藍圖」：一個檔案管一類 API
from api.health import health_bp
from api.auth import auth_bp
from api.students import students_bp
from api.quests import quests_bp
from api.practice import practice_bp
from api.shop import shop_bp
from api.pet import pet_bp
from api.dashboard import dashboard_bp
from api.class_board import class_bp

# 前端打包檔與素材都在專案根目錄
FRONTEND_DIST = project_path('frontend', 'dist')
MATERIAL_DIR = project_path('material')


def create_app():
    """建立並設定 Flask 應用程式（工廠函式，方便測試／部署重複建立）。"""
    # 不使用 Flask 預設的 /static；前端檔案由 frontend/dist 提供
    app = Flask(__name__, static_folder=None)

    # ---------- session（登入狀態存在伺服器端 cookie）----------
    # 正式環境請用環境變數設密鑰，不要用預設字串上線
    app.secret_key = os.environ.get(
        'NOTEADVENTURE_SECRET_KEY',
        'noteadventure-dev-secret',
    )
    # HTTPS 上線時設 NOTEADVENTURE_COOKIE_SECURE=1，瀏覽器才只在安全連線送 cookie
    cookie_secure = os.environ.get('NOTEADVENTURE_COOKIE_SECURE', '').lower() in (
        '1', 'true', 'yes',
    )
    app.config['SESSION_COOKIE_SECURE'] = cookie_secure
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # 降低 CSRF 風險的常見設定
    app.config['JSON_AS_ASCII'] = False  # API 回傳中文時不要變成 \uXXXX
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 上傳上限 20MB

    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({'message': '檔案太大，請上傳 20MB 以內的錄音'}), 413

    # ---------- 註冊 API（JSON）----------
    # 註冊後，例如 auth_bp 裡的 @auth_bp.post('/api/teachers/login') 就會生效
    app.register_blueprint(health_bp)      # GET  /api/health
    app.register_blueprint(auth_bp)        # 登入／登出／改密碼／註冊
    app.register_blueprint(students_bp)    # 老師：學生列表／建立／重設密碼
    app.register_blueprint(quests_bp)      # 任務建立／指派／學生查看
    app.register_blueprint(practice_bp)    # 練習上傳（會連動任務進度與獎勵）
    app.register_blueprint(shop_bp)        # 商店／購買／兌換
    app.register_blueprint(pet_bp)         # 寵物狀態
    app.register_blueprint(dashboard_bp)   # 老師首頁摘要
    app.register_blueprint(class_bp)       # 教室：兩廳院節目看板

    # ---------- 前端網頁（Vue 打包後的 frontend/dist）----------
    # /student/...、/teacher/... 都回傳同一個 index.html，由 Vue Router 決定畫面
    # 開發時可改用 Vite（cd frontend && npm run dev），見 docs/啟動說明.md

    # 學生頁面用的圖／音：/assets/material/home.png → material/home.png
    @app.get('/assets/material/<path:filename>')
    def material_asset(filename):
        return send_from_directory(MATERIAL_DIR, filename)

    @app.get('/')
    @app.get('/<path:path>')
    def frontend_page(path=''):
        if path.startswith('api/'):
            return jsonify({'message': 'API 不存在'}), 404
        if not os.path.isfile(os.path.join(FRONTEND_DIST, 'index.html')):
            return (
                '找不到前端打包檔，請先執行：cd frontend && npm install && npm run build',
                503,
                {'Content-Type': 'text/plain; charset=utf-8'},
            )
        # 打包出的 JS／CSS／圖片直接回傳；其餘路徑交給 Vue Router
        if path and os.path.isfile(os.path.join(FRONTEND_DIST, path)):
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, 'index.html')

    return app


# 本機（專案根目錄）：flask --app backend/app.py run --port 5000
# Docker：gunicorn --chdir backend "app:create_app()"
app = create_app()
