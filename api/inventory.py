from flask import Blueprint, jsonify, request
from model.model import SellHistory, Inventory, TransactionHistory

inventory_api = Blueprint('inventory_api', __name__)

@inventory_api.route('/inventory', methods=['GET']) 
def get_inventory():
    symbol = request.args.get('stockCode', '2330')  
    transactions = Inventory.query.all()  # 使用 SQLAlchemy 查詢
    # transactions = Inventory.query.filter_by(stock_code=symbol).all()  # 使用 SQLAlchemy 查詢
    print(f"Requesting data for stock code: {symbol}")  # 查看 symbol 是否正確
    print(f"Requesting transactions -- ----{transactions}")  # 查看 symbol 是否正確

    results = [
        {
            'stock_code': transaction.stock_code,
            'unit_price': transaction.unit_price,
            'transaction_type': transaction.transaction_type,
            'transaction_value': transaction.transaction_value,
            'estimated_fee': transaction.estimated_fee,
            'estimated_tax': transaction.estimated_tax,
            'date': transaction.date.isoformat() if transaction.date else None,
            'transaction_quantity': transaction.transaction_quantity,
            'net_amount': transaction.net_amount,
            'uuid': transaction.uuid  # 不需要轉換為字串
        }
        for transaction in transactions
    ]
    print('\n\n 庫存 \n', results, '\n\n')
    return jsonify(results)


