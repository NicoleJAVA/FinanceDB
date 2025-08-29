import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from model.model import SellHistory, Inventory, TransactionHistory
from db import db
from decimal import Decimal

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
    data = request.json
    stock_code = data['stockCode']
    inventory = data['inventory']
    transaction_date = data['transactionDate']
    sell_record = data['sellRecord']

    sell_record_uuid = str(uuid.uuid4())  # 轉換為字串格式方便存儲

    # inventory_uuids = [item['uuid'] for item in inventory]
    transaction_history_uuids = []  # 用來儲存每筆歷史記錄的 UUID

    for item in inventory:
        inventory_uuid = item['uuid']
        write_off_quantity = item['writeOffQuantity']
        print('\n\n ]write_off_quantity ', type(write_off_quantity), '\n\n')
        print('\n 日期: ', transaction_date, '\n');
        [write_off_success, message] = perform_write_off(inventory_uuid, write_off_quantity, stock_code, transaction_date)
        if not write_off_success:
            return jsonify({'status': 'error', 'message': message}), 400
        history_uuid = log_to_history(inventory_uuid, write_off_quantity, stock_code, transaction_date, sell_record_uuid)
        transaction_history_uuids.append(history_uuid)

    log_sell_history(sell_record, sell_record_uuid, transaction_history_uuids)

    return jsonify({'status': 'success'}), 200

def perform_write_off(uuid, write_off_quantity, stock_code, transaction_date):
    inventory_item = db.session.query(Inventory).filter_by(uuid=uuid).first()

    if inventory_item:
        # if write_off_quantity > inventory_item.available_quantity:
        #     raise ValueError(f"Write-off quantity {write_off_quantity} exceeds available quantity {inventory_item.available_quantity}")
        print('\n\n 沖掉 ', type(inventory_item.transaction_quantity), '\n\n')
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
        

def log_to_history(inventory_uuid, write_off_quantity, stock_code, transaction_date, sell_record_uuid):
    trans_uuid = str(uuid.uuid4()) 
    new_transaction_record = TransactionHistory(
        inventory_uuid=inventory_uuid,
        write_off_quantity=write_off_quantity,
        stock_code=stock_code,
        transaction_date=transaction_date,
        sell_record_uuid=sell_record_uuid,
        transaction_uuid=trans_uuid
    )
    
    db.session.add(new_transaction_record)


def log_sell_history(sell_record, sell_record_uuid, transaction_history_uuids):
    print('\n\n\n SELL RECORD', sell_record, '\n')
    trans_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    print('\n 日期 --', trans_datetime, '\n')

    sell_history_entry = {
        'data_uuid': sell_record_uuid,
        # 改：若前端有傳 transaction_date 就用它；否則用現在時間字串
        'transaction_date': sell_record.get('transaction_date', trans_datetime),
        'stock_code': sell_record['stock_code'],
        'product_name': sell_record['product_name'],
        'unit_price': sell_record['unit_price'],
        'quantity': sell_record.get('transaction_quantity', 0),
        'transaction_value': sell_record.get('transaction_value', 0),
        'fee': sell_record.get('estimated_fee', 0),
        'tax': sell_record.get('estimated_tax', 0),

        'net_amount': sell_record.get('net_amount', 0),
        'remaining_quantity': sell_record.get('remaining_quantity', 0),
        'profit_loss': sell_record.get('profit_loss', 0),

        # 存成逗號字串（和 get_all 用法相容）
        'transaction_history_uuids': ",".join(transaction_history_uuids),
    }

    db.session.add(SellHistory(**sell_history_entry))
    db.session.commit()


@transaction_api.route('/transactions/preview-offset', methods=['POST'])
def preview_write_off():
    data = request.json
    inventory_list = data.get('inventory', [])
    a_table = data.get('aTable', {})

    from decimal import Decimal, ROUND_HALF_UP

    def rhup(x):  # JS/Excel 的四捨五入（5 進位）
        return int(Decimal(x).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    # A 表（賣出單）數值（Decimal）
    a_net_amt    = Decimal(a_table.get('net_amount', 0))
    a_qty        = Decimal(a_table.get('transaction_quantity', 1))  # avoid /0
    a_unit_price = Decimal(a_table.get('unit_price', 0))
    a_fee        = Decimal(a_table.get('estimated_fee', 0))
    a_tax        = Decimal(a_table.get('estimated_tax', 0))

    result = []

    for item in inventory_list:
        write_off_quantity = int(item.get('writeOffQuantity', 0) or 0)
        if write_off_quantity <= 0:
            continue

        inv = Inventory.query.filter_by(uuid=item['uuid']).first()
        if not inv:
            continue

        inv_qty     = Decimal(inv.transaction_quantity or 0)   # Excel：庫存原始股數當分母
        write_qty   = Decimal(write_off_quantity)
        inv_net_amt = Decimal(inv.net_amount or 0)

        # 成本 / 收入：先算比例，按列 ROUND_HALF_UP
        amortized_cost   = rhup(inv_net_amt * (write_qty / inv_qty))
        amortized_income = rhup(a_net_amt   * (write_qty / a_qty))

        # === 兩種費稅分攤基礎 ===
        # 若前端（編輯畫面）有把庫存自己的 fee/tax 傳來（對齊 Excel）
        inv_fee = item.get('fee', None)
        inv_tax = item.get('tax', None)
        if inv_fee is not None or inv_tax is not None:
            # 「庫存基礎」：費稅分母用 inv_qty（和很多 Excel 表一致）
            fee_base = Decimal(inv_fee or 0)
            tax_base = Decimal(inv_tax or 0)
            fee_share = rhup(fee_base * (write_qty / inv_qty))
            tax_share = rhup(tax_base * (write_qty / inv_qty))
        else:
            # 「賣出單基礎」：沿用你原本作法（分母 a_qty）
            fee_share = rhup(a_fee * (write_qty / a_qty))
            tax_share = rhup(a_tax * (write_qty / a_qty))

        # 損益：先算毛額，再扣掉分攤後的費稅；全部採 ROUND_HALF_UP
        gross_diff  = rhup(write_qty * (a_unit_price - Decimal(inv.unit_price)))
        profit_loss = gross_diff - (fee_share + tax_share)

        result.append({
            'uuid': inv.uuid,
            'remaining_quantity': int(inv.transaction_quantity) - int(write_off_quantity),
            'amortized_cost': amortized_cost,
            'amortized_income': amortized_income,
            'profit_loss': profit_loss,
        })

    return jsonify(result), 200

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