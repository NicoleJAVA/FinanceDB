from flask import Blueprint, jsonify, request
from model.model import SellHistory, Inventory, TransactionHistory

inventory_api = Blueprint('inventory_api', __name__)

@inventory_api.route('/inventory', methods=['GET']) 
def get_inventory():
    symbol = request.args.get('stockCode', '2330')  
    transactions = Inventory.query.filter_by(stock_code=symbol).all()  # 使用 SQLAlchemy 查詢
    print('\n\n 123 ', type(transactions[0].average_price))
    results = [
        {
            'id': transaction.id,
            'stock_code': transaction.stock_code,
            'transaction_type': transaction.transaction_type,
            'stock_quantity': transaction.stock_quantity,
            'average_price': transaction.average_price,  # 不需要轉換為字串
            'total_amount': transaction.total_amount,
            'cost': transaction.cost,
            'reference_price': transaction.reference_price,
            'market_value': transaction.market_value,
            'estimated_fee': transaction.estimated_fee,
            'estimated_tax': transaction.estimated_tax,
            'reference_profit_loss': transaction.reference_profit_loss,
            'profit_loss_rate': transaction.profit_loss_rate,
            'details': transaction.details,
            'date': transaction.date.isoformat() if transaction.date else None,
            'transaction_price': transaction.transaction_price,
            'transaction_quantity': transaction.transaction_quantity,
            'net_amount': transaction.net_amount,
            'uuid': transaction.uuid  # 不需要轉換為字串
        }
        for transaction in transactions
    ]
    return jsonify(results)


