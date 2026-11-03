"""
老師端 Streamlit：實際啟動一個 Flask 伺服器（測試資料庫），
用 Streamlit AppTest 跑 streamlit_app.py：登入 → 逐頁切換 → 建立學生／任務／商品。
"""

import os
import threading

import pytest
from werkzeug.serving import make_server

from conftest import ROOT

AppTest = pytest.importorskip('streamlit.testing.v1').AppTest

PAGES = [
    '首頁', '學生列表', '建立學生', '重設學生密碼', '任務清單', '新增任務',
    '指派任務', '上傳紀錄', '商品清單', '新增商品', '待兌換商品', '修改密碼',
]


@pytest.fixture(scope='module')
def api_server(app):
    server = make_server('127.0.0.1', 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    old = os.environ.get('NOTEADVENTURE_API_BASE_URL')
    os.environ['NOTEADVENTURE_API_BASE_URL'] = f'http://127.0.0.1:{server.server_port}'
    yield server
    server.shutdown()
    if old is None:
        os.environ.pop('NOTEADVENTURE_API_BASE_URL', None)
    else:
        os.environ['NOTEADVENTURE_API_BASE_URL'] = old


@pytest.fixture(scope='module')
def teacher_app(api_server, make_client):
    make_client().post('/api/teachers/register', json={
        'teacher_name': 'UI 老師', 'email': 'ui@test.local', 'password': 'ui-pass', 'confirm_password': 'ui-pass'
    })
    at = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=30)
    at.run()
    assert not at.exception
    return at


def errors(at):
    return [e.value for e in at.error] + [str(e.value) for e in at.exception]


def submit(at, label):
    button = next(b for b in at.button if b.label == label)
    button.click().run()


def test_login(teacher_app):
    at = teacher_app
    at.text_input[0].input('ui@test.local')
    at.text_input[1].input('ui-pass')
    submit(at, '登入')
    assert not errors(at), errors(at)
    assert at.sidebar.radio, '登入後應出現側邊選單'


@pytest.mark.parametrize('page', PAGES)
def test_every_page_renders(teacher_app, page):
    at = teacher_app
    at.sidebar.radio[0].set_value(page).run()
    assert not errors(at), (page, errors(at))


def test_create_student_quest_item(teacher_app):
    at = teacher_app

    at.sidebar.radio[0].set_value('建立學生').run()
    at.text_input[0].input('UI 學生')
    submit(at, '建立')
    assert not errors(at), errors(at)
    assert any('帳號' in c.value for c in at.code)

    at.sidebar.radio[0].set_value('新增任務').run()
    at.text_input[0].input('UI 任務')
    submit(at, '建立任務')
    assert not errors(at), errors(at)

    at.sidebar.radio[0].set_value('指派任務').run()
    submit(at, '確認指派')
    assert not errors(at), errors(at)

    at.sidebar.radio[0].set_value('新增商品').run()
    at.text_input[0].input('UI 商品')
    submit(at, '建立商品')
    assert not errors(at), errors(at)

    at.sidebar.radio[0].set_value('學生列表').run()
    assert at.dataframe, '學生列表應有資料'
