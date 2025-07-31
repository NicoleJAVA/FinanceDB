import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from model.model import SellHistory, Inventory, TransactionHistory
from db import db

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

    print('\n SELL RECORD', sell_record, '\n');
    trans_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    print('\n 日期 --', trans_datetime, '\n');

    sell_history_entry = {
        'data_uuid': sell_record_uuid,
        'transaction_date': '2024-10-03 08:43:00', # datetime.utcnow() # stday todo stday
        'stock_code': sell_record['stock_code'],
        'product_name': sell_record['product_name'],
        'unit_price': sell_record['unit_price'],
        'quantity': sell_record['quantity'],
        'transaction_value': sell_record.get('transaction_value', 0),  # 假如前端沒傳遞此值
        'fee': sell_record['fee'],
        'tax': sell_record['tax'],
        'net_amount': sell_record.get('net_amount', 0),  # 假如前端沒傳遞此值
        'remaining_quantity': sell_record.get('remaining_quantity', 0),
        'profit_loss': sell_record.get('profit_loss', 0),
        'transaction_history_uuids': transaction_history_uuids,
    }

    db.session.add(SellHistory(**sell_history_entry))
    db.session.commit()




# 我希望
# log_to_history 裡面，每筆歷史都有自己的 uuid

# 然後 log_sell_history 那邊，應該不是要存 inventory_uuids，而是要存 log_to_history 對應的那幾筆 uuid
# ALTER TABLE transaction_history
# ADD COLUMN transaction_uuid CHAR(36) NOT NULL;
# ALTER TABLE sell_history
# RENAME COLUMN inventory_uuids TO transaction_history_uuids;