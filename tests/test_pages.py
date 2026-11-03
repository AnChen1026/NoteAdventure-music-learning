"""
學生網頁：一頁版殼、各內頁、CSS／JS 與素材都要能正常回應。
"""

import pytest

STUDENT_PAGES = [
    '/student', '/student/app', '/student/login', '/student/home', '/student/practice',
    '/student/shop', '/student/quests', '/student/pet', '/student/class',
    '/student/backpack', '/student/settings',
]

STATIC_FILES = [
    '/static/web/student_spa.js', '/static/web/student_spa.css',
    '/static/web/student_bgm.js', '/static/web/student_viewport.js',
    '/static/web/page_transition.js', '/static/web/student_practice.js',
]

MATERIALS = [
    '/assets/material/login.JPG', '/assets/material/home.png', '/assets/material/practice.png',
    '/assets/material/shop.png', '/assets/material/quest.png', '/assets/material/class.png',
    '/assets/material/backpack.JPG', '/assets/material/settings.JPG', '/assets/material/map_btn.png',
    '/assets/material/pet_stage1.png', '/assets/material/pet_stage2-4.png',
    '/assets/material/pet/pet_id_no1.png', '/assets/material/pet/pet_id_no4.png',
    '/assets/material/bgm/bgm.mp3',
]


@pytest.mark.parametrize('path', STUDENT_PAGES)
def test_student_pages(make_client, path):
    response = make_client().get(path)
    assert response.status_code == 200
    assert 'text/html' in response.content_type


@pytest.mark.parametrize('path', STATIC_FILES + MATERIALS)
def test_static_and_material(make_client, path):
    response = make_client().get(path)
    assert response.status_code == 200, path
    assert len(response.data) > 0


def test_health(make_client):
    response = make_client().get('/api/health')
    assert response.status_code == 200
