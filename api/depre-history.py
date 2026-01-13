import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from model.model import SellHistory, Inventory, SellDetailHistory
from db import db

history_api = Blueprint('history_api', __name__)


@history_api.route('/history/all', methods=['get'])
def get_all_history():

    historyRows = SellDetailHistory.query.all()  # 使用 SQLAlchemy 查詢
    results = []

    for history in historyRows:
        # 查詢 Inventory 表中對應的成交單價
        inventory_data = Inventory.query.filter_by(uuid=history.inventory_uuid).first()
        inventory_price = inventory_data.transaction_price if inventory_data else None
        
        # 查詢 SellHistory 表中對應的成交單價
        sell_data = SellHistory.query.filter_by(data_uuid=history.sell_record_uuid).first()
        sell_price = sell_data.unit_price if sell_data else None

        # 整合結果
        results.append({
            'uuid': history.uuid,
            'transaction_uuid': history.transaction_uuid,
            'sell_record_uuid': history.sell_record_uuid,
            'inventory_uuid': history.inventory_uuid,
            'write_off_quantity': history.write_off_quantity,
            'stock_code': history.stock_code,
            'transaction_date': history.transaction_date,
            'sell_record_uuid': history.sell_record_uuid,
            'inventory_price': inventory_price,  # 加入的成交單價
            'sell_price': sell_price,            # 加入的成交單價
        })

        print('\n\n\n\nHISTORY: ', results, '\n\n\n\n')

    return jsonify(results)














