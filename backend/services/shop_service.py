from db import SqlUtils

db = SqlUtils()

# ======================================================
# 老師查看自己建立的商品
# ======================================================
def teacher_show_shop_item(teacher):
    sql = """
    SELECT item_id, item_name, item_type, price, stock, description, is_active
    FROM shop_item
    WHERE teacher_id = %s
    ORDER BY item_id;
    """
    result = db.query_all(sql, (teacher['teacher_id'],))
    if result:
        return result
    return '無商品資料'


# ======================================================
# 學生查看老師上架的商品
# ======================================================
def student_show_shop_item(student):
    # 只顯示自己老師上架、還有庫存的商品
    sql = """
    SELECT item_id, item_name, item_type, price, stock, description
    FROM shop_item
    WHERE teacher_id = %s
    AND is_active = TRUE
    AND (stock IS NULL OR stock > 0)
    ORDER BY item_id;
    """
    result = db.query_all(sql, (student['teacher_id'],))
    if result:
        return result
    return '目前沒有可購買的商品'


# ======================================================
# 學生購買商品
# ======================================================
def purchase_item(student, item_id):
    # 只能買自己老師上架的商品
    sql = """
    SELECT item_id, item_name, item_type, price, stock
    FROM shop_item
    WHERE item_id = %s
    AND teacher_id = %s
    AND is_active = TRUE;
    """
    item = db.query_one(sql, (item_id, student['teacher_id']))
    if not item:
        return '查無此商品'
    if item['stock'] is not None and item['stock'] <= 0:
        return '商品已售完'

    # 金幣以資料庫目前數值為準
    sql = """
    SELECT total_coin
    FROM student
    WHERE student_id = %s;
    """
    total_coin = db.query_one(sql, (student['student_id'],))['total_coin']
    if total_coin < item['price']:
        return f"金幣不足，還需要 {item['price'] - total_coin} 金幣"

    # 虛擬商品購買後直接持有，實體商品要等老師兌換
    if item['item_type'] == 'VIRTUAL':
        status = 'OWNED'
    else:
        status = 'PURCHASED'

    coin_sql = """
    UPDATE student
    SET total_coin = total_coin - %s
    WHERE student_id = %s
    AND total_coin >= %s;
    """
    transaction_sql = """
    INSERT INTO coin_transaction (
    student_id,
    source_type,
    amount
    )
    VALUES (%s, 'SHOP_PURCHASE', %s)
    """
    purchase_sql = """
    INSERT INTO purchase_record (
    student_id,
    item_id,
    price,
    status
    )
    VALUES (%s, %s, %s, %s)
    """
    sql_list = [
        (coin_sql, (item['price'], student['student_id'], item['price'])),
        (transaction_sql, (student['student_id'], -item['price'])),
        (purchase_sql, (student['student_id'], item['item_id'], item['price'], status))
    ]

    # 不限量商品不需要扣庫存；有限庫存扣到 0 時自動下架
    if item['stock'] is not None:
        stock_sql = """
        UPDATE shop_item
        SET is_active = CASE WHEN stock <= 1 THEN FALSE ELSE is_active END,
            stock = stock - 1
        WHERE item_id = %s
        AND stock > 0;
        """
        sql_list.append((stock_sql, (item['item_id'],)))

    # 扣金幣、金幣異動、購買紀錄與庫存寫在同一個 transaction
    if db.execute_transaction(sql_list):
        # stock 為購買前數量；買前是 1 代表這次買完後歸零並已下架
        auto_deactivated = item['stock'] is not None and item['stock'] <= 1
        if status == 'PURCHASED':
            message = f"購買成功 {item['item_name']}，請找老師兌換"
        else:
            message = f"購買成功 {item['item_name']}"
        if auto_deactivated:
            message += '（庫存已售完，商品已自動下架）'
        return message
    return '購買失敗'


# ======================================================
# 學生查看我的背包（購買／持有紀錄）
# ======================================================
def student_show_backpack(student):
    sql = """
    SELECT
        p.purchase_id,
        i.item_name,
        i.item_type,
        i.description,
        p.price,
        p.status,
        p.created_at
    FROM purchase_record p
    JOIN shop_item i ON i.item_id = p.item_id
    WHERE p.student_id = %s
    ORDER BY p.created_at DESC;
    """
    result = db.query_all(sql, (student['student_id'],))
    if result:
        return result
    return '背包是空的'


# ======================================================
# 老師查看待兌換的實體商品
# ======================================================
def teacher_show_pending_purchase(teacher):
    # PURCHASED 表示已購買但還沒拿到實體商品
    sql = """
    SELECT p.purchase_id, s.student_name, i.item_name, p.price, p.created_at
    FROM purchase_record p
    JOIN student s ON s.student_id = p.student_id
    JOIN shop_item i ON i.item_id = p.item_id
    WHERE s.teacher_id = %s
    AND p.status = 'PURCHASED'
    ORDER BY p.created_at;
    """
    result = db.query_all(sql, (teacher['teacher_id'],))
    if result:
        return result
    return '沒有待兌換的商品'


# ======================================================
# 老師標記實體商品已兌換
# ======================================================
def redeem_purchase(teacher, purchase_id):
    # 只能處理自己學生、且還沒兌換的紀錄
    sql = """
    SELECT p.purchase_id, s.student_name, i.item_name
    FROM purchase_record p
    JOIN student s ON s.student_id = p.student_id
    JOIN shop_item i ON i.item_id = p.item_id
    WHERE p.purchase_id = %s
    AND s.teacher_id = %s
    AND p.status = 'PURCHASED';
    """
    purchase = db.query_one(sql, (purchase_id, teacher['teacher_id']))
    if not purchase:
        return '查無待兌換紀錄'

    sql = """
    UPDATE purchase_record
    SET status = 'REDEEMED'
    WHERE purchase_id = %s
    AND status = 'PURCHASED';
    """
    rowcount = db.execute(sql, (purchase_id,))
    if rowcount > 0:
        return f"{purchase['student_name']} 的 {purchase['item_name']} 已完成兌換"
    return '兌換失敗'


# ======================================================
# 老師建立商品（stock 為 None 表示不限量）
# ======================================================
def create_shop_item(teacher, item_name, item_type, price, stock, description):
    rowcount = db.execute(
        """
        INSERT INTO shop_item (
        teacher_id,
        item_name,
        item_type,
        price,
        stock,
        description
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            teacher['teacher_id'],
            item_name,
            item_type,
            price,
            stock,
            description
        )
    )
    if rowcount > 0:
        return '商品新增成功'
    return '商品新增失敗'
