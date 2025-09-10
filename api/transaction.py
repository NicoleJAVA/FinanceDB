import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from model.model import SellHistory, Inventory, TransactionHistory
from db import db
from decimal import Decimal
import json

transaction_api = Blueprint('transaction_api', __name__)


@transaction_api.route('/transactions', methods=['POST'])
def add_transaction():
    data = request.json
    transaction_uuid = str(uuid.uuid4())
    cursor = db.session()
    #inventory 新增欄位 SOP 1
    new_transaction = Inventory(
        id=transaction_uuid,
        stock_code=data['stock_code'],
        transaction_type=data['transaction_type'],
        unit_price=data['unit_price'],
        transaction_value=data['transaction_value'],
        estimated_fee=data['estimated_fee'],
        estimated_tax=data['estimated_tax'],
        date=data['date'],
        transaction_quantity=data.get('transaction_quantity'),
        net_amount=data.get('net_amount'),
        remarks=data.get('remarks'),
    )
    
    db.session.add(new_transaction)
    db.session.commit()
    return jsonify({'message': 'Transaction added successfully!'}), 201

@transaction_api.route('/transactions/offset', methods=['POST'])
def batch_write_off():
    data = request.get_json(silent=True) or {}
    a_table = data.get('aTable') or {}

    def pick(*keys, default=None):
        for k in keys:
            if k in data: return data[k]
        for k in keys:
            if k in a_table: return a_table[k]
        return default

    stock_code = pick('stockCode', 'stock_code')
    transaction_date = pick('transactionDate', 'transaction_date') or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    unit_price = pick('unitPrice', 'unit_price')
    transaction_quantity = pick('transactionQuantity', 'transaction_quantity')
    estimated_fee = pick('estimatedFee', 'estimated_fee', 'fee')
    estimated_tax = pick('estimatedTax', 'estimated_tax', 'tax')
    net_amount = pick('netAmount', 'net_amount')
    transaction_value = pick('transactionValue', 'transaction_value')

    inventory_list = data.get('inventory') or data.get('inventory_list') or []
    sell_record = a_table or {}

    if not stock_code or transaction_quantity is None or net_amount is None:
        return jsonify({'error': 'missing fields'}), 400

    # 這筆賣出單的 UUID
    sell_record_uuid = str(uuid.uuid4())

    transaction_history_uuids = []
    for item in inventory_list:
        write_off_qty = int(item.get('writeOffQuantity') or item.get('write_off_quantity') or 0)
        if write_off_qty <= 0:
            continue

        # 這筆沖銷交易的 UUID
        th_uuid = log_to_history(
            sell_record_uuid=sell_record_uuid,
            stock_code=stock_code,
            transaction_date=transaction_date,
            item=item
        )
        if th_uuid:
            transaction_history_uuids.append(str(th_uuid))

    # 寫入 sell_history（含 snapshot_json）
    log_sell_history(sell_record, sell_record_uuid, transaction_history_uuids)

    return jsonify({'status': 'ok', 'sell_record_uuid': sell_record_uuid}), 200



def perform_write_off(uuid, write_off_quantity, stock_code, transaction_date):
    inventory_item = db.session.query(Inventory).filter_by(uuid=uuid).first()

    if inventory_item:
        # if write_off_quantity > inventory_item.available_quantity:
        #     raise ValueError(f"Write-off quantity {write_off_quantity} exceeds available quantity {inventory_item.available_quantity}")

        if write_off_quantity > inventory_item.transaction_quantity:
            message = "Write-off quantity is larger than inventory quantity!"
            # raise ValueError(message)
            return [False, message]
        
        inventory_item.transaction_quantity -= write_off_quantity

        db.session.commit()
        return [True, "success"]
    else:
        message = "Inventory item not found"
        # raise ValueError(message)
        return [False, message]
        

def log_to_history(*, sell_record_uuid, stock_code, item, transaction_date=None):
    """把單筆沖銷寫進 TransactionHistory（含 before/after 欄位）"""
    th_uuid = str(uuid.uuid4())
    tx_date = transaction_date or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    def g(*keys, default=None):
        for k in keys:
            if k in item:
                return item[k]
        return default

    new_row = TransactionHistory(
        transaction_uuid=th_uuid,
        sell_record_uuid=sell_record_uuid,
        inventory_uuid=g('uuid', 'inventory_uuid'),
        stock_code=stock_code,
        transaction_date=tx_date,               # 用呼叫端給的日期

        transaction_type='sell',

        write_off_quantity=g('writeOffQuantity', 'write_off_quantity', default=0),

        # ---- B_before ----
        quantity_before=g('transaction_quantity_before', 'quantity_before'),
        unit_price_before=g('unit_price_before', 'unit_price'),
        net_amount_before=g('net_amount_before', 'net_amount'),

        # ---- B_after ----
        remaining_quantity=g('remaining_quantity'),
        amortized_cost=g('amortized_cost'),
        amortized_income=g('amortized_income'),
        profit_loss=g('profit_loss'),
        profit_loss_2=g('profit_loss_2'),
    )

    db.session.add(new_row)
    db.session.commit()
    return th_uuid



# def log_to_history(sell_record_uuid, stock_code, item):
#     """
#     item 來自前端 inventory 的單列，已包含 before/after 所需欄位
#     """
#     th_uuid = str(uuid.uuid4())

#     # 兼容 key 命名（前端若有 camelCase / snake_case 都吃）
#     def g(*keys, default=None):
#         for k in keys:
#             if k in item:
#                 return item[k]
#         return default

#     new_row = TransactionHistory(
#         transaction_uuid=th_uuid,
#         sell_record_uuid=sell_record_uuid,
#         inventory_uuid=g('uuid', 'inventory_uuid'),
#         stock_code=stock_code,

#         write_off_quantity=g('writeOffQuantity', 'write_off_quantity', default=0),

#         # ---- B_before ----
#         quantity_before   = g('transaction_quantity_before', 'quantity_before'),
#         unit_price_before = g('unit_price_before', 'unit_price'),
#         net_amount_before = g('net_amount_before', 'net_amount'),

#         # ---- B_after ----
#         remaining_quantity = g('remaining_quantity'),
#         amortized_cost     = g('amortized_cost'),
#         amortized_income   = g('amortized_income'),
#         profit_loss        = g('profit_loss'),
#         profit_loss_2      = g('profit_loss_2'),
#     )

#     db.session.add(new_row)
#     db.session.flush()   # 取得 pk/uuid 時可用；無需求也可直接 commit
#     db.session.commit()
#     return th_uuid


def log_sell_history(sell_record, sell_record_uuid, transaction_history_uuids):
    trans_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    sell_history_entry = {
        'data_uuid': sell_record_uuid,
        'transaction_date': sell_record.get('transaction_date', trans_datetime),
        'stock_code': sell_record['stock_code'],
        'product_name': sell_record['product_name'],
        'unit_price': sell_record['unit_price'],
        'quantity': sell_record['transaction_quantity'],
        'transaction_value': sell_record.get('transaction_value', 0),
        'fee': sell_record.get('estimated_fee', 0),
        'tax': sell_record.get('estimated_tax', 0),
        'net_amount': sell_record.get('net_amount', 0),
        'profit_loss': sell_record.get('profit_loss', 0),
        'transaction_history_uuids': ",".join(transaction_history_uuids),
    }

    db.session.add(SellHistory(**sell_history_entry))
    db.session.commit()


# ok. ver. old.
# def log_sell_history(sell_record, sell_record_uuid, transaction_history_uuids):
#     print('\n\n\n SELL RECORD', sell_record, '\n')
#     trans_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
#     print('\n 日期 --', trans_datetime, '\n')

#     # A 表主欄位（必須記錄，列表第一眼看到）
#     qty = sell_record.get('transaction_quantity', 0)
#     fee = sell_record.get('estimated_fee', sell_record.get('fee', 0))
#     tax = sell_record.get('estimated_tax', sell_record.get('tax', 0))

#     # 取得 B after / B before / totals（前端預覽頁面送來的備份快照）
#     b_after = sell_record.get('b_after') or sell_record.get('b_items') or []
#     b_before = sell_record.get('b_before') or []
#     b_totals = sell_record.get('b_totals') or {}

#     # A 的損益（若前端有就用前端；否則用 B after 的「損益試算二」總和或 profit_loss 總和兜出來）
#     if 'profit_loss' in sell_record:
#         a_profit_loss = sell_record['profit_loss']
#     else:
#         pl2_sum = sum([
#             (r.get('profit_loss_2') or (r.get('amortized_cost', 0) + r.get('amortized_income', 0)))
#             for r in b_after
#         ])
#         pl_sum = sum([r.get('profit_loss', 0) for r in b_after])
#         a_profit_loss = pl2_sum if pl2_sum else pl_sum

#     # transaction_history_uuids 安全處理（過濾 None 並轉字串）
#     safe_uuids = [str(u) for u in (transaction_history_uuids or []) if u]

#     sell_history_entry = {
#         'data_uuid': sell_record_uuid,
#         'transaction_date': sell_record.get('transaction_date', trans_datetime),
#         'stock_code': sell_record['stock_code'],
#         'product_name': sell_record['product_name'],
#         'unit_price': sell_record['unit_price'],
#         'quantity': qty,
#         'transaction_value': sell_record.get('transaction_value', 0),
#         'fee': fee,
#         'tax': tax,
#         'net_amount': sell_record.get('net_amount', 0),
#         'remaining_quantity': sell_record.get('remaining_quantity', 0),
#         'profit_loss': a_profit_loss,
#         'transaction_history_uuids': ",".join(safe_uuids),
#     }

#     # ====== 備份快照（詳細頁才會看）======
#     snapshot = {
#         "A": {
#             "transaction_date": sell_history_entry['transaction_date'],
#             "stock_code": sell_history_entry['stock_code'],
#             "product_name": sell_history_entry['product_name'],
#             "unit_price": sell_history_entry['unit_price'],
#             "transaction_quantity": qty,
#             "transaction_value": sell_history_entry['transaction_value'],
#             "estimated_fee": fee,
#             "estimated_tax": tax,
#             "net_amount": sell_history_entry['net_amount'],
#             "profit_loss": a_profit_loss,
#         },
#         "B_before": b_before,
#         "B_after": b_after,
#         "totals": b_totals,
#         "calc_meta": {
#             "rounding_mode": "HALF_UP",
#             "allocation_basis": sell_record.get("allocation_basis")
#         }
#     }

#     try:
#         # 只有在模型有 snapshot_json 欄位時才塞，避免未知欄位報錯
#         if hasattr(SellHistory, 'snapshot_json'):
#             sell_history_entry['snapshot_json'] = json.dumps(snapshot, ensure_ascii=False)
#     except Exception as e:
#         print('[snapshot_json] skip:', e)

#     db.session.add(SellHistory(**sell_history_entry))
#     db.session.commit()


@transaction_api.route('/transactionHistory/by-sell', methods=['GET'])
def transaction_history_by_sell():
    sell_uuid = request.args.get('sell_record_uuid')
    if not sell_uuid:
        return jsonify([])

    rows = (TransactionHistory.query
            .filter_by(sell_record_uuid=sell_uuid)
            .order_by(TransactionHistory.transaction_date.asc())
            .all())

    out = []
    for r in rows:
        out.append({
            'inventory_uuid': r.inventory_uuid,
            'sell_record_uuid': r.sell_record_uuid,
            'stock_code': r.stock_code,
            'transaction_date': r.transaction_date.strftime('%Y-%m-%d %H:%M:%S') if r.transaction_date else None,
            'transaction_uuid': getattr(r, 'transaction_uuid', getattr(r, 'id', None)),

            # before
            'quantity_before': r.quantity_before,
            'unit_price_before': r.unit_price_before,
            'net_amount_before': r.net_amount_before,

            # after
            'remaining_quantity': r.remaining_quantity,
            'amortized_cost': r.amortized_cost,
            'amortized_income': r.amortized_income,
            'profit_loss': r.profit_loss,
            'profit_loss_2': r.profit_loss_2,

            # write-off
            'write_off_quantity': r.write_off_quantity,
        })
    return jsonify(out)

# @transaction_api.route('/transactions/preview-offset', methods=['POST'])
# def preview_write_off():
#     data = request.json
#     inventory_list = data.get('inventory', [])
#     a_table = data.get('aTable', {})

#     from decimal import Decimal, ROUND_HALF_UP

#     def rhup(x):  # JS/Excel 的四捨五入（5 進位）
#         return int(Decimal(x).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

#     # A 表（賣出單）數值（Decimal）
#     a_net_amt    = Decimal(a_table.get('net_amount', 0))
#     a_qty        = Decimal(a_table.get('transaction_quantity', 1))  # avoid /0
#     a_unit_price = Decimal(a_table.get('unit_price', 0))
#     a_fee        = Decimal(a_table.get('estimated_fee', 0))
#     a_tax        = Decimal(a_table.get('estimated_tax', 0))

#     result = []

#     for item in inventory_list:
#         write_off_quantity = int(item.get('writeOffQuantity', 0) or 0)
#         if write_off_quantity <= 0:
#             continue

#         inv = Inventory.query.filter_by(uuid=item['uuid']).first()
#         if not inv:
#             continue

#         inv_qty     = Decimal(inv.transaction_quantity or 0)   # Excel：庫存原始股數當分母
#         write_qty   = Decimal(write_off_quantity)
#         inv_net_amt = Decimal(inv.net_amount or 0)

#         # 成本 / 收入：先算比例，按列 ROUND_HALF_UP
#         amortized_cost   = rhup(inv_net_amt * (write_qty / inv_qty))
#         amortized_income = rhup(a_net_amt   * (write_qty / a_qty))

#         # === 兩種費稅分攤基礎 ===
#         # 若前端（編輯畫面）有把庫存自己的 fee/tax 傳來（對齊 Excel）
#         inv_fee = item.get('fee', None)
#         inv_tax = item.get('tax', None)
#         if inv_fee is not None or inv_tax is not None:
#             # 「庫存基礎」：費稅分母用 inv_qty（和很多 Excel 表一致）
#             fee_base = Decimal(inv_fee or 0)
#             tax_base = Decimal(inv_tax or 0)
#             fee_share = rhup(fee_base * (write_qty / inv_qty))
#             tax_share = rhup(tax_base * (write_qty / inv_qty))
#         else:
#             # 「賣出單基礎」：沿用你原本作法（分母 a_qty）
#             fee_share = rhup(a_fee * (write_qty / a_qty))
#             tax_share = rhup(a_tax * (write_qty / a_qty))

#         # 損益：先算毛額，再扣掉分攤後的費稅；全部採 ROUND_HALF_UP
#         gross_diff  = rhup(write_qty * (a_unit_price - Decimal(inv.unit_price)))
#         profit_loss = gross_diff - (fee_share + tax_share)

#         result.append({
#             'uuid': inv.uuid,
#             'remaining_quantity': int(inv.transaction_quantity) - int(write_off_quantity),
#             'amortized_cost': amortized_cost,
#             'amortized_income': amortized_income,
#             'profit_loss': profit_loss,
#         })

#     return jsonify(result), 200

# def preview_write_off():
    # data = request.json
    # inventory_list = data.get('inventory', [])
    # a_table = data.get('aTable', {})

    # result = []

    # for item in inventory_list:
    #     write_off_quantity = item.get('writeOffQuantity', 0)
    #     if write_off_quantity <= 0:
    #         continue

    #     inventory_item = Inventory.query.filter_by(uuid=item['uuid']).first()

    #     if not inventory_item:
    #         continue

    #     inv_qty = Decimal(inventory_item.transaction_quantity)
    #     write_qty = Decimal(write_off_quantity)
    #     net_amt = Decimal(inventory_item.net_amount)

    #     amortized_cost = round(net_amt * (write_qty / inv_qty))

    #     a_net_amt = Decimal(a_table.get('net_amount', 0))
    #     a_qty = Decimal(a_table.get('transaction_quantity', 1))  # avoid division by 0
    #     a_unit_price = Decimal(a_table.get('unit_price', 0))
    #     a_fee = Decimal(a_table.get('estimated_fee', 0))
    #     a_tax = Decimal(a_table.get('estimated_tax', 0))

    #     amortized_income = round(a_net_amt * (write_qty / a_qty))

    #     profit_loss = round(
    #         write_qty * (a_unit_price - Decimal(inventory_item.unit_price)) -
    #         (a_fee + a_tax) * (write_qty / a_qty)
    #     )

    #     result.append({
    #         'uuid': inventory_item.uuid,
    #         'remaining_quantity': int(inventory_item.transaction_quantity) - int(write_off_quantity),
    #         'amortized_cost': int(amortized_cost),
    #         'amortized_income': int(amortized_income),
    #         'profit_loss': int(profit_loss),
    #     })

    # return jsonify(result), 200


# 我希望
# log_to_history 裡面，每筆歷史都有自己的 uuid

# 然後 log_sell_history 那邊，應該不是要存 inventory_uuids，而是要存 log_to_history 對應的那幾筆 uuid
# ALTER TABLE transaction_history
# ADD COLUMN transaction_uuid CHAR(36) NOT NULL;
# ALTER TABLE sell_history
# RENAME COLUMN inventory_uuids TO transaction_history_uuids;