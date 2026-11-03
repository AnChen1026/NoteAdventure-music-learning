"""
前端網頁（Vue 打包檔 frontend/dist）：各路徑都回傳 index.html、打包的 JS／CSS 與素材都能載入。
需要先執行：cd frontend && npm run build
"""

import re

import pytest

from conftest import ROOT

DIST_INDEX = ROOT / 'frontend' / 'dist' / 'index.html'

pytestmark = pytest.mark.skipif(
    not DIST_INDEX.is_file(),
    reason='找不到 frontend/dist，請先執行 cd frontend && npm run build'
)

FRONTEND_ROUTES = [
    '/', '/student', '/student/app', '/student/login', '/student/home', '/student/practice',
    '/student/shop', '/student/quests', '/student/pet', '/student/class',
    '/student/backpack', '/student/settings',
    '/teacher', '/teacher/login', '/teacher/dashboard', '/teacher/students', '/teacher/quests/assign', '/teacher/quests/1/edit',
    '/teacher/uploads', '/teacher/redeem',
]

MATERIALS = [
    '/assets/material/login.JPG', '/assets/material/home.png', '/assets/material/practice.png',
    '/assets/material/shop.png', '/assets/material/quest.png', '/assets/material/class.png',
    '/assets/material/backpack.JPG', '/assets/material/settings.JPG', '/assets/material/map_btn.png',
    '/assets/material/pet_stage1.png', '/assets/material/pet_stage2-4.png',
    '/assets/material/pet/pet_id_no1.png', '/assets/material/pet/pet_id_no4.png',
    '/assets/material/bgm/bgm.mp3',
]


@pytest.mark.parametrize('path', FRONTEND_ROUTES)
def test_frontend_routes_return_index(make_client, path):
    response = make_client().get(path)
    assert response.status_code == 200
    assert 'text/html' in response.content_type
    assert b'<div id="app">' in response.data


def test_bundled_assets(make_client):
    client = make_client()
    html = client.get('/student').get_data(as_text=True)
    assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', html)
    assert assets, 'index.html 應引用打包後的 JS／CSS'
    for asset in assets:
        response = client.get(asset)
        assert response.status_code == 200, asset
        assert 'text/html' not in response.content_type, asset


@pytest.mark.parametrize('path', MATERIALS)
def test_material(make_client, path):
    response = make_client().get(path)
    assert response.status_code == 200, path
    assert len(response.data) > 0


def test_unknown_api_is_json_404(make_client):
    response = make_client().get('/api/not-exist')
    assert response.status_code == 404
    assert response.is_json


def test_health(make_client):
    response = make_client().get('/api/health')
    assert response.status_code == 200
