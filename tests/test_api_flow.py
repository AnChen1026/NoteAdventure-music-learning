"""
完整流程（依 MVP 期中展示流程）：

老師註冊／登入 → 建立學生 → 建立任務 → 指派 → 學生登入改密碼 → 查看任務
→ 上傳練習 → 任務完成發獎（不重複發獎）→ 寵物成長 → 商店購買 → 背包
→ 老師兌換實體商品、查看上傳紀錄與試聽 → 首頁摘要 → 權限隔離 → 登出

測試依檔案順序執行，前一步的結果存在 state 供後面使用。
"""

import io
import wave

import pytest

from conftest import query_one

state = {}


def wav_bytes(seconds):
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(8000)
        wav_file.writeframes(b'\x00\x00' * 8000 * seconds)
    return buffer.getvalue()


@pytest.fixture(scope='module')
def clients(make_client):
    return {
        'teacher_a': make_client(),
        'teacher_b': make_client(),
        'student': make_client(),
        'student_b': make_client(),
        'guest': make_client(),
    }


# ---------------- 老師帳號 ----------------

def test_teacher_register(clients):
    for key, email in (('teacher_a', 'a@test.local'), ('teacher_b', 'b@test.local')):
        response = clients[key].post('/api/teachers/register', json={
            'teacher_name': key, 'email': email, 'password': 'pass-a1', 'confirm_password': 'pass-a1'
        })
        assert response.status_code == 201, response.json

    duplicate = clients['guest'].post('/api/teachers/register', json={
        'teacher_name': 'x', 'email': 'a@test.local', 'password': 'p', 'confirm_password': 'p'
    })
    assert duplicate.status_code == 409

    mismatch = clients['guest'].post('/api/teachers/register', json={
        'teacher_name': 'x', 'email': 'c@test.local', 'password': 'p1', 'confirm_password': 'p2'
    })
    assert mismatch.status_code == 400


def test_teacher_login(clients):
    wrong = clients['guest'].post('/api/teachers/login', json={'email': 'a@test.local', 'password': 'nope'})
    assert wrong.status_code == 401

    for key, email in (('teacher_a', 'a@test.local'), ('teacher_b', 'b@test.local')):
        response = clients[key].post('/api/teachers/login', json={'email': email, 'password': 'pass-a1'})
        assert response.status_code == 200
        assert response.json['role'] == 'teacher'

    me = clients['teacher_a'].get('/api/me')
    assert me.status_code == 200
    assert me.json['user']['email'] == 'a@test.local'


def test_teacher_change_password(clients):
    client = clients['teacher_a']
    wrong = client.post('/api/teachers/change-password', json={
        'old_password': 'bad', 'new_password': 'pass-a2', 'confirm_password': 'pass-a2'
    })
    assert wrong.status_code == 401
    ok = client.post('/api/teachers/change-password', json={
        'old_password': 'pass-a1', 'new_password': 'pass-a2', 'confirm_password': 'pass-a2'
    })
    assert ok.status_code == 200
    relogin = clients['guest'].post('/api/teachers/login', json={'email': 'a@test.local', 'password': 'pass-a2'})
    assert relogin.status_code == 200
    clients['guest'].post('/api/logout')


# ---------------- 學生帳號 ----------------

def test_create_students(clients):
    response = clients['teacher_a'].post('/api/students', json={'student_name': '小明'})
    assert response.status_code == 201
    state['username'] = response.json['username']
    state['temp_password'] = response.json['temp_password']

    response = clients['teacher_b'].post('/api/students', json={'student_name': '小華'})
    assert response.status_code == 201
    state['username_b'] = response.json['username']
    state['temp_password_b'] = response.json['temp_password']

    empty = clients['teacher_a'].post('/api/students', json={'student_name': ''})
    assert empty.status_code == 400

    listing = clients['teacher_a'].get('/api/students')
    assert listing.status_code == 200
    rows = listing.json['data']
    assert [row['帳號'] for row in rows] == [state['username']]  # 老師只看得到自己的學生
    state['student_id'] = rows[0]['序號']
    state['student_id_b'] = clients['teacher_b'].get('/api/students').json['data'][0]['序號']


def test_reset_student_password_scoped(clients):
    other = clients['teacher_b'].post('/api/students/reset-password', json={'username': state['username']})
    assert other.status_code == 404  # 不能重設別位老師的學生

    response = clients['teacher_a'].post('/api/students/reset-password', json={'username': state['username']})
    assert response.status_code == 200
    state['temp_password'] = response.json['temp_password']


def test_student_login_and_change_password(clients):
    client = clients['student']
    response = client.post('/api/students/login', json={
        'username': state['username'], 'password': state['temp_password']
    })
    assert response.status_code == 200
    assert response.json['user']['password_changed'] is False

    mismatch = client.post('/api/students/change-password', json={
        'old_password': state['temp_password'], 'new_password': 'stu-1', 'confirm_password': 'stu-2'
    })
    assert mismatch.status_code == 400
    ok = client.post('/api/students/change-password', json={
        'old_password': state['temp_password'], 'new_password': 'stu-1', 'confirm_password': 'stu-1'
    })
    assert ok.status_code == 200
    assert client.get('/api/me').json['user']['password_changed'] is True

    other = clients['student_b'].post('/api/students/login', json={
        'username': state['username_b'], 'password': state['temp_password_b']
    })
    assert other.status_code == 200


# ---------------- 任務 ----------------

def test_create_quests(clients):
    client = clients['teacher_a']
    quests = [
        ('練習兩次', 'DAILY', 'PRACTICE_COUNT', 2, 120, 30),
        ('兩首不同曲目', 'WEEKLY', 'DISTINCT_SONGS', 2, 30, 10),
        ('隱藏：第一次練習', 'HIDDEN', 'PRACTICE_COUNT', 1, 10, 5),
    ]
    for name, quest_type, condition, value, xp, coin in quests:
        response = client.post('/api/quests', json={
            'quest_name': name, 'quest_type': quest_type, 'condition_type': condition,
            'condition_value': value, 'reward_xp': xp, 'reward_coin': coin, 'is_repeatable': True
        })
        assert response.status_code == 201, response.json

    bad = client.post('/api/quests', json={
        'quest_name': '錯誤', 'quest_type': 'DAILY', 'condition_type': 'PRACTICE_COUNT', 'condition_value': 0
    })
    assert bad.status_code == 400

    listing = client.get('/api/quests').json['data']
    state['quest_ids'] = {row['任務名稱']: row['任務編號'] for row in listing}
    assert len(state['quest_ids']) == 3
    assert clients['teacher_b'].get('/api/quests').json['data'] == []


def test_assign_quests(clients):
    client = clients['teacher_a']
    for name, quest_id in state['quest_ids'].items():
        response = client.post(f'/api/quests/{quest_id}/assign', json={'student_id': state['student_id']})
        assert response.status_code == 201, (name, response.json)
        if name.startswith('隱藏'):
            assert response.json['period_key'] == 'ONCE'
            assert response.json['expires_at'] is None
        else:
            assert response.json['expires_at'] is not None

    first_quest = state['quest_ids']['練習兩次']
    again = client.post(f'/api/quests/{first_quest}/assign', json={'student_id': state['student_id']})
    assert again.status_code == 409  # 同一期間不可重複指派

    other_student = client.post(f'/api/quests/{first_quest}/assign', json={'student_id': state['student_id_b']})
    assert other_student.status_code == 404
    other_teacher = clients['teacher_b'].post(f'/api/quests/{first_quest}/assign', json={'student_id': state['student_id_b']})
    assert other_teacher.status_code == 404



def test_manage_unassigned_quest(clients):
    client = clients['teacher_a']
    quest = {
        'quest_name': '暫時任務', 'quest_type': 'DAILY', 'condition_type': 'PRACTICE_COUNT',
        'condition_value': 1, 'reward_xp': 5, 'reward_coin': 1, 'is_repeatable': True
    }
    assert client.post('/api/quests', json=quest).status_code == 201
    quest_id = next(row['任務編號'] for row in client.get('/api/quests').json['data'] if row['任務名稱'] == '暫時任務')

    # 未指派過：可修改任何欄位（包含類型）
    edited = dict(quest, quest_name='暫時任務改', quest_type='WEEKLY', condition_type='DISTINCT_SONGS', reward_xp=8)
    assert client.put(f'/api/quests/{quest_id}', json=edited).status_code == 200
    row = next(row for row in client.get('/api/quests').json['data'] if row['任務編號'] == quest_id)
    assert (row['任務名稱'], row['任務類型'], row['任務條件類型'], row['獎勵經驗'], row['指派次數']) == \
        ('暫時任務改', 'WEEKLY', 'DISTINCT_SONGS', 8, 0)
    assert client.put(f'/api/quests/{quest_id}', json=dict(edited, quest_name='')).status_code == 400

    # 別的老師不能改、不能停用、不能刪除
    other = clients['teacher_b']
    assert other.put(f'/api/quests/{quest_id}', json=edited).status_code == 404
    assert other.patch(f'/api/quests/{quest_id}/active', json={'is_active': False}).status_code == 404
    assert other.delete(f'/api/quests/{quest_id}').status_code == 404

    # 停用後不可指派，啟用後可以
    assert client.patch(f'/api/quests/{quest_id}/active', json={'is_active': 'no'}).status_code == 400
    assert client.patch(f'/api/quests/{quest_id}/active', json={'is_active': False}).status_code == 200
    assert client.post(f'/api/quests/{quest_id}/assign', json={'student_id': state['student_id']}).status_code == 404
    assert client.patch(f'/api/quests/{quest_id}/active', json={'is_active': True}).status_code == 200

    # 從未指派過才能刪除
    assert client.delete(f'/api/quests/{quest_id}').status_code == 200
    assert client.delete(f'/api/quests/{quest_id}').status_code == 404
    assert query_one('SELECT COUNT(*) AS n FROM quest_list WHERE quest_id = %s', (quest_id,))['n'] == 0


def test_manage_assigned_quest(clients):
    client = clients['teacher_a']
    quest_id = state['quest_ids']['練習兩次']
    row = next(row for row in client.get('/api/quests').json['data'] if row['任務編號'] == quest_id)
    assert row['指派次數'] == 1
    current = {
        'quest_name': row['任務名稱'], 'quest_type': row['任務類型'], 'condition_type': row['任務條件類型'],
        'condition_value': row['任務條件數值'], 'reward_xp': row['獎勵經驗'], 'reward_coin': row['獎勵金幣'],
        'is_repeatable': bool(row['是否為重複任務'])
    }

    # 已指派過：不可改類型、不可刪除；同樣內容存檔仍成功
    assert client.put(f'/api/quests/{quest_id}', json=dict(current, quest_type='WEEKLY')).status_code == 409
    assert client.put(f'/api/quests/{quest_id}', json=dict(current, condition_type='DISTINCT_SONGS')).status_code == 409
    assert client.put(f'/api/quests/{quest_id}', json=current).status_code == 200
    assert client.delete(f'/api/quests/{quest_id}').status_code == 409

def test_student_sees_quests(clients):
    response = clients['student'].get(f"/api/students/{state['student_id']}/quests")
    assert response.status_code == 200
    names = {row['quest_name'] for row in response.json['data']}
    assert names == {'練習兩次', '兩首不同曲目'}  # 隱藏任務完成前不顯示

    forbidden = clients['student_b'].get(f"/api/students/{state['student_id']}/quests")
    assert forbidden.status_code == 403


# ---------------- 練習上傳與獎勵 ----------------

def upload(client, song, data, filename, duration=None):
    form = {'song_name': song, 'audio': (io.BytesIO(data), filename)}
    if duration is not None:
        form['audio_duration'] = str(duration)
    return client.post(
        f"/api/students/{state['student_id']}/practice-uploads",
        data=form,
        content_type='multipart/form-data'
    )


def test_upload_validation(clients):
    client = clients['student']
    assert upload(client, '', b'x', 'a.webm', 5).status_code == 400
    assert upload(client, '小星星', b'x', 'a.webm').status_code == 400  # 非 wav 要帶秒數
    other = clients['student_b'].post(
        f"/api/students/{state['student_id']}/practice-uploads",
        data={'song_name': 'x', 'audio_duration': '3', 'audio': (io.BytesIO(b'x'), 'a.webm')},
        content_type='multipart/form-data'
    )
    assert other.status_code == 403


def test_upload_progress_and_rewards(clients):
    client = clients['student']

    first = upload(client, '小星星', b'fake-webm-audio', 'practice.webm', 30)
    assert first.status_code == 201, first.json
    assert [r['quest_name'] for r in first.json['rewards']] == ['隱藏：第一次練習']

    second = upload(client, '小蜜蜂', wav_bytes(2), 'practice.wav')
    assert second.status_code == 201, second.json
    assert second.json['audio_duration'] == 2  # wav 自動計算秒數
    assert {r['quest_name'] for r in second.json['rewards']} == {'練習兩次', '兩首不同曲目'}

    third = upload(client, '小星星', b'fake-webm-audio', 'practice.webm', 20)
    assert third.status_code == 201
    assert third.json['rewards'] == []  # 已完成的任務不重複發獎

    assert third.json['total_xp'] == 160
    assert third.json['total_coin'] == 45

    xp_rows = query_one('SELECT COUNT(*) AS n, SUM(xp_amount) AS total FROM xp_source WHERE student_id = %s', (state['student_id'],))
    assert (xp_rows['n'], int(xp_rows['total'])) == (3, 160)


def test_quests_after_completion(clients):
    rows = clients['student'].get(f"/api/students/{state['student_id']}/quests").json['data']
    status = {row['quest_name']: row['quest_status'] for row in rows}
    assert status == {'練習兩次': 'COMPLETED', '兩首不同曲目': 'COMPLETED', '隱藏：第一次練習': 'COMPLETED'}


def test_pet_grows(clients):
    response = clients['student'].get(f"/api/students/{state['student_id']}/pet")
    assert response.status_code == 200
    pet = response.json['data']
    assert pet['stage_order'] == 2  # 160 XP → 幼體
    assert pet['xp_to_next'] == 500 - 160


# ---------------- 商店 ----------------

def test_create_shop_items(clients):
    client = clients['teacher_a']
    items = [
        {'item_name': '貼紙', 'item_type': 'VIRTUAL', 'price': 10, 'stock': None, 'description': '虛擬貼紙'},
        {'item_name': '鉛筆', 'item_type': 'PHYSICAL', 'price': 15, 'stock': 2, 'description': None},
        {'item_name': '昂貴獎品', 'item_type': 'VIRTUAL', 'price': 1000, 'stock': None, 'description': ''},
    ]
    for item in items:
        response = client.post('/api/shop-items', json=item)
        assert response.status_code == 201, response.json

    bad = client.post('/api/shop-items', json={'item_name': 'x', 'item_type': 'VIRTUAL', 'price': -1})
    assert bad.status_code == 400

    rows = client.get('/api/shop-items').json['data']
    state['items'] = {row['item_name']: row['item_id'] for row in rows}
    assert len(state['items']) == 3


def test_student_shop_and_purchase(clients):
    client = clients['student']
    listing = client.get(f"/api/students/{state['student_id']}/shop-items")
    assert listing.status_code == 200
    assert {row['item_name'] for row in listing.json['data']} == set(state['items'])

    too_expensive = client.post(f"/api/shop-items/{state['items']['昂貴獎品']}/purchase")
    assert too_expensive.status_code == 400

    pencil = client.post(f"/api/shop-items/{state['items']['鉛筆']}/purchase")
    assert pencil.status_code == 200, pencil.json
    sticker = client.post(f"/api/shop-items/{state['items']['貼紙']}/purchase")
    assert sticker.status_code == 200
    assert sticker.json['total_coin'] == 45 - 15 - 10


def test_limited_stock_stays_on_shelf_until_sold_out(clients):
    # 庫存 2 買走 1 個後，應剩 1 個且仍上架
    row = query_one('SELECT stock, is_active FROM shop_item WHERE item_id = %s', (state['items']['鉛筆'],))
    assert row['stock'] == 1
    assert row['is_active'] == 1, '庫存還剩 1 個卻被自動下架'


def test_backpack(clients):
    response = clients['student'].get(f"/api/students/{state['student_id']}/purchases")
    assert response.status_code == 200
    status = {row['item_name']: row['status'] for row in response.json['data']}
    assert status == {'鉛筆': 'PURCHASED', '貼紙': 'OWNED'}

    forbidden = clients['student_b'].get(f"/api/students/{state['student_id']}/purchases")
    assert forbidden.status_code == 403


def test_redeem_physical_item(clients):
    pending = clients['teacher_a'].get('/api/purchases/pending').json['data']
    assert [row['item_name'] for row in pending] == ['鉛筆']
    purchase_id = pending[0]['purchase_id']

    assert clients['teacher_b'].patch(f'/api/purchases/{purchase_id}/redeem').status_code != 200
    response = clients['teacher_a'].patch(f'/api/purchases/{purchase_id}/redeem')
    assert response.status_code == 200
    assert clients['teacher_a'].patch(f'/api/purchases/{purchase_id}/redeem').status_code != 200
    assert clients['teacher_a'].get('/api/purchases/pending').json['data'] == []


def test_last_item_sold_out_goes_off_shelf(clients):
    # 庫存只剩 1 個時，買完應歸零並自動下架
    clients['teacher_a'].post('/api/shop-items', json={
        'item_name': '最後一個', 'item_type': 'VIRTUAL', 'price': 1, 'stock': 1, 'description': None
    })
    item_id = [row['item_id'] for row in clients['teacher_a'].get('/api/shop-items').json['data']
               if row['item_name'] == '最後一個'][0]
    response = clients['student'].post(f'/api/shop-items/{item_id}/purchase')
    assert response.status_code == 200
    assert response.json['auto_deactivated'] is True

    row = query_one('SELECT stock, is_active FROM shop_item WHERE item_id = %s', (item_id,))
    assert (row['stock'], row['is_active']) == (0, 0)
    again = clients['student'].post(f'/api/shop-items/{item_id}/purchase')
    assert again.status_code == 404


# ---------------- 老師查看 ----------------

def test_teacher_uploads_and_audio(clients):
    client = clients['teacher_a']
    rows = client.get('/api/practice-uploads').json['data']
    assert len(rows) == 3
    filtered = client.get('/api/practice-uploads', query_string={'student_id': state['student_id']}).json['data']
    assert len(filtered) == 3

    for row in rows:
        audio = client.get(f"/api/practice-uploads/{row['upload_id']}/audio")
        assert audio.status_code == 200, row
        assert audio.mimetype.startswith('audio/')

    other = clients['teacher_b'].get(f"/api/practice-uploads/{rows[0]['upload_id']}/audio")
    assert other.status_code == 404
    assert clients['teacher_b'].get('/api/practice-uploads').json['data'] == []


def test_teacher_dashboard(clients):
    response = clients['teacher_a'].get('/api/dashboard')
    assert response.status_code == 200
    summary = response.json['data']['summary']
    assert summary['student_count'] == 1
    assert summary['active_quest_count'] == 3
    assert summary['upload_count_7d'] == 3
    assert summary['pending_redeem_count'] == 0


# ---------------- 權限與登出 ----------------

@pytest.mark.parametrize('method,path', [
    ('get', '/api/students'),
    ('get', '/api/quests'),
    ('put', '/api/quests/1'),
    ('patch', '/api/quests/1/active'),
    ('delete', '/api/quests/1'),
    ('get', '/api/shop-items'),
    ('get', '/api/purchases/pending'),
    ('get', '/api/practice-uploads'),
    ('get', '/api/dashboard'),
])
def test_teacher_endpoints_need_teacher(clients, method, path):
    assert getattr(clients['guest'], method)(path).status_code == 401
    assert getattr(clients['student'], method)(path).status_code == 401


def test_class_board(clients):
    # 需要連外網取得兩廳院資料；沒網路時應回 502 與提示訊息，而不是 500
    response = clients['student'].get('/api/class/ntch-programs')
    assert response.status_code in (200, 502)
    assert 'data' in response.json


def test_logout(clients):
    for key in ('teacher_a', 'student'):
        assert clients[key].post('/api/logout').status_code == 200
        assert clients[key].get('/api/me').status_code == 401
