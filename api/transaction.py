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
    new_transaction = Inventory(
        id=transaction_uuid,
        stock_code=data['stock_code'],
        transaction_type=data['transaction_type'],
        stock_quantity=data['stock_quantity'],
        average_price=data['average_price'],
        total_amount=data['total_amount'],
        cost=data['cost'],
        reference_price=data['reference_price'],
        market_value=data['market_value'],
        estimated_fee=data['estimated_fee'],
        estimated_tax=data['estimated_tax'],
        reference_profit_loss=data['reference_profit_loss'],
        profit_loss_rate=data['profit_loss_rate'],
        details=data.get('details'),
        date=data['date'],
        transaction_price=data.get('transaction_price'),
        transaction_quantity=data.get('transaction_quantity'),
        net_amount=data.get('net_amount')
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

    inventory_uuids = [item['uuid'] for item in inventory]

    for item in inventory:
        inventory_uuid = item['uuid']
        write_off_quantity = item['writeOffQuantity']
        print('\n\n ]write_off_quantity ', type(write_off_quantity), '\n\n')
        print('\n 日期: ', transaction_date, '\n');
        perform_write_off(inventory_uuid, write_off_quantity, stock_code, transaction_date)
        log_to_history(inventory_uuid, write_off_quantity, stock_code, transaction_date, sell_record_uuid)

    log_sell_history(sell_record, sell_record_uuid, inventory_uuids)

    return jsonify({'status': 'success'}), 200

def perform_write_off(uuid, write_off_quantity, stock_code, transaction_date):
    inventory_item = db.session.query(Inventory).filter_by(uuid=uuid).first()

    if inventory_item:
        # if write_off_quantity > inventory_item.available_quantity:
        #     raise ValueError(f"Write-off quantity {write_off_quantity} exceeds available quantity {inventory_item.available_quantity}")
        print('\n\n 沖掉 ', type(inventory_item.transaction_quantity), '\n\n')
        inventory_item.transaction_quantity -= write_off_quantity

        db.session.commit()
    else:
        raise ValueError("Inventory item not found")

def log_to_history(inventory_uuid, write_off_quantity, stock_code, transaction_date, sell_record_uuid):
    new_transaction_record = TransactionHistory(
        inventory_uuid=inventory_uuid,
        write_off_quantity=write_off_quantity,
        stock_code=stock_code,
        transaction_date=transaction_date,
        sell_record_uuid=sell_record_uuid
    )
    
    db.session.add(new_transaction_record)


def log_sell_history(sell_record, sell_record_uuid, inventory_uuids):

    print('\n SELL RECORD', sell_record, '\n');
    trans_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    print('\n 日期 --', trans_datetime, '\n');

    sell_history_entry = {
        'data_uuid': sell_record_uuid,
        'transaction_date': '2024-10-03 08:43:00', # datetime.utcnow()
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
        'inventory_uuids': inventory_uuids,
    }

    db.session.add(SellHistory(**sell_history_entry))
    db.session.commit()

