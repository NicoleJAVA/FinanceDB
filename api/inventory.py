from flask import Blueprint, jsonify, request
from model.model import SellHistory, Inventory, SellDetailHistory

inventory_api = Blueprint('inventory_api', __name__)

@inventory_api.route('/inventory', methods=['GET']) 
def get_inventory():
    symbol = request.args.get('stockCode', '2330')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    offset = (page - 1) * limit

    query = Inventory.query.filter_by(stock_code=symbol)
    total_count = query.count()
    transactions = query.offset(offset).limit(limit).all()

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
            'uuid': transaction.uuid,  # 不需要轉換為字串
            'remarks': transaction.remarks #inventory 新增欄位 SOP 3
        }
        for transaction in transactions
    ]
    print('\n\n 庫存 \n', results, '\n\n')
    
    return jsonify({
        "data": results,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count
        }
    })


