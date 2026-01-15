import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from model.model import SellHistory, Inventory, SellDetailHistory
from db import db
from decimal import Decimal
import json

transaction_api = Blueprint('transaction_api', __name__)

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


    transactionDate = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # print('data[transaction_date]', data['transaction_date'])
    print('a_table[transaction_date]', a_table['transaction_date'])

    stock_code = pick('stockCode', 'stock_code')
    # transaction_date = pick('transactionDate', 'transaction_date') or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') # todo dele
    transaction_date = transactionDate
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


    print('\n\n\n\n', 'Log to History')
    # 這筆賣出單的 UUID
    sell_record_uuid = str(uuid.uuid4())

    sell_detail_history_uuids = []
    for item in inventory_list:
        print('\n ---------------- \n', item)

        write_off_qty = int(item.get('writeOffQuantity') or item.get('write_off_quantity') or 0)
        if write_off_qty <= 0:
            continue

        # 這筆沖銷交易的 UUID
        th_uuid = log_to_sell_detail_history(
            sell_record_uuid=sell_record_uuid,
            stock_code=stock_code,
            transaction_date=transaction_date,
            item=item
        )
        if th_uuid:
            sell_detail_history_uuids.append(str(th_uuid))

    # 寫入 sell_history（含 snapshot_json）
    log_sell_history(sell_record, sell_record_uuid, sell_detail_history_uuids, transactionDate)

    return jsonify({'status': 'ok', 'sell_record_uuid': sell_record_uuid}), 200


# todo dele
# def perform_write_off(uuid, write_off_quantity, stock_code, transaction_date):
#     inventory_item = db.session.query(Inventory).filter_by(uuid=uuid).first()

#     if inventory_item:
#         # if write_off_quantity > inventory_item.available_quantity:
#         #     raise ValueError(f"Write-off quantity {write_off_quantity} exceeds available quantity {inventory_item.available_quantity}")

#         if write_off_quantity > inventory_item.transaction_quantity:
#             message = "Write-off quantity is larger than inventory quantity!"
#             # raise ValueError(message)
#             return [False, message]
        
#         inventory_item.available_quantity -= write_off_quantity

#         db.session.commit()
#         return [True, "success"]
#     else:
#         message = "Inventory item not found"
#         # raise ValueError(message)
#         return [False, message]
        


# 建議（但不是強制）
# 如果你未來不再需要 transaction_uuid 這個欄位，其實可以：
# 留 uuid 當唯一識別
# transaction_uuid 之後移除
# ➡️ 目前先不改也能正常跑
def log_to_sell_detail_history(*, sell_record_uuid, stock_code, item, transaction_date=None):
    """把單筆沖銷寫進 SellDetailHistory（含 before/after 欄位）"""
    th_uuid = str(uuid.uuid4())
    # tx_date = transaction_date or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    tx_date = transaction_date or datetime.utcnow()
    print('\n', 'transaction_date:',  transaction_date,  'tx_date:',  tx_date)

    def g(*keys, default=None):
        for k in keys:
            if k in item:
                return item[k]
        return default

    inventory = db.session.query(Inventory).filter_by(
        uuid=g('uuid', 'inventory_uuid')
    ).first()

    if not inventory:
        raise ValueError('Inventory not found')

    quantity_before = inventory.available_quantity if inventory else None
    write_off_qty = g('writeOffQuantity', 'write_off_quantity', default=0)
    remaining_quantity = quantity_before - write_off_qty
        
    new_row = SellDetailHistory(
        uuid=th_uuid,
        transaction_uuid=th_uuid,
        sell_record_uuid=sell_record_uuid,
        inventory_uuid=g('uuid', 'inventory_uuid'),
        stock_code=stock_code,
        transaction_date=tx_date,               # 用呼叫端給的日期
        created_at=datetime.utcnow(),

        transaction_type='sell',

        write_off_quantity=g('writeOffQuantity', 'write_off_quantity', default=0),

        # ---- B_before ----
        # quantity_before=g('transaction_quantity_before', 'quantity_before'),
        quantity_before=quantity_before,
        unit_price_before=g('unit_price_before', 'unit_price'),
        net_amount_before=g('net_amount_before', 'net_amount'),

        # ---- B_after ----
        remaining_quantity=remaining_quantity,
        amortized_cost=g('amortized_cost'),
        amortized_income=g('amortized_income'),
        profit_loss=g('profit_loss'),
        profit_loss_2=g('profit_loss_2'),
    )


    inventory.available_quantity = remaining_quantity

    db.session.add(new_row)
    db.session.commit()
    return th_uuid


def log_sell_history(sell_record, sell_record_uuid, sell_detail_history_uuids, transactionDate):
    trans_datetime = transactionDate

    sell_history_entry = {
        'data_uuid': sell_record_uuid,
        'created_at': datetime.utcnow(),
        'transaction_date': transactionDate,
        'stock_code': sell_record['stock_code'],
        'product_name': sell_record['product_name'],
        'unit_price': sell_record['unit_price'],
        'transaction_quantity': sell_record['transaction_quantity'],
        'transaction_value': sell_record.get('transaction_value', 0),
        'fee': sell_record.get('estimated_fee', 0),
        'tax': sell_record.get('estimated_tax', 0),
        'net_amount': sell_record.get('net_amount', 0),
        'profit_loss': sell_record.get('profit_loss', 0),
        'sell_detail_history_uuids': sell_detail_history_uuids,
    }

    db.session.add(SellHistory(**sell_history_entry))
    db.session.commit()


# 如果你「想要」在 selldetail 顯示備註
# 要在 /transactionHistory/by-sell
# JOIN inventory 用 inventory_uuid 把 Inventory.remarks 帶出來
@transaction_api.route('/transactionHistory/by-sell', methods=['GET'])
def get_transaction_history_by_sell():
    sell_record_uuid = request.args.get('sell_record_uuid')
    if not sell_record_uuid:
        return jsonify({'error': 'missing sell_record_uuid'}), 400

    rows = (
        db.session.query(
            SellDetailHistory.uuid.label('transaction_uuid'),
            SellDetailHistory.sell_record_uuid,
            SellDetailHistory.inventory_uuid,
            SellDetailHistory.created_at,
            SellDetailHistory.write_off_quantity,
            SellDetailHistory.transaction_date,

            SellDetailHistory.quantity_before,
            SellDetailHistory.unit_price_before,
            SellDetailHistory.net_amount_before,

            SellDetailHistory.remaining_quantity,
            SellDetailHistory.amortized_cost,
            SellDetailHistory.amortized_income,
            SellDetailHistory.profit_loss,
            SellDetailHistory.profit_loss_2,

            Inventory.remarks.label('inventory_remarks')
        )
        .join(Inventory, Inventory.uuid == SellDetailHistory.inventory_uuid)
        .filter(SellDetailHistory.sell_record_uuid == sell_record_uuid)
        .order_by(SellDetailHistory.transaction_date.asc())
        .all()
    )

    return jsonify([
    {
        'transaction_uuid': r.transaction_uuid,
        'sell_record_uuid': r.sell_record_uuid,
        'inventory_uuid': r.inventory_uuid,
        'created_at': r.created_at,
        'write_off_quantity': r.write_off_quantity,
        'transaction_date': r.transaction_date,

        'quantity_before': r.quantity_before,
        'unit_price_before': float(r.unit_price_before) if r.unit_price_before is not None else None,
        'net_amount_before': float(r.net_amount_before) if r.net_amount_before is not None else None,

        'remaining_quantity': r.remaining_quantity,
        'amortized_cost': float(r.amortized_cost) if r.amortized_cost is not None else None,
        'amortized_income': float(r.amortized_income) if r.amortized_income is not None else None,
        'profit_loss': float(r.profit_loss) if r.profit_loss is not None else None,
        'profit_loss_2': float(r.profit_loss_2) if r.profit_loss_2 is not None else None,

        'remarks': r.inventory_remarks or ''
    }
    for r in rows
    ])


# 我希望
# log_to_sell_detail_history 裡面，每筆歷史都有自己的 uuid

# 然後 log_sell_history 那邊，應該不是要存 inventory_uuids，而是要存 log_to_sell_detail_history 對應的那幾筆 uuid
# ALTER TABLE transaction_history
# ADD COLUMN transaction_uuid CHAR(36) NOT NULL;
# ALTER TABLE sell_history
# RENAME COLUMN inventory_uuids TO transaction_history_uuids;