import uuid
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://localhost:3006"}})

# 設定 SQLAlchemy 資料庫連線
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/stock_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定義 Inventory 模型
class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stock_code = db.Column(db.String(255), nullable=False)
    transaction_type = db.Column(db.Enum('Buy', 'Sell', 'Dividend', 'Stock Split'), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    average_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=False)
    reference_price = db.Column(db.Numeric(10, 2), nullable=False)
    market_value = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_fee = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_tax = db.Column(db.Numeric(10, 2), nullable=False)
    reference_profit_loss = db.Column(db.Numeric(10, 2), nullable=False)
    profit_loss_rate = db.Column(db.Numeric(5, 2), nullable=False)
    details = db.Column(db.Text)
    date = db.Column(db.Date)
    transaction_price = db.Column(db.Numeric(10, 2))
    transaction_quantity = db.Column(db.Integer)
    net_amount = db.Column(db.Numeric(10, 2))

    # 外鍵約束
    # stocks = db.relationship('Stocks', backref='inventory', foreign_keys=[stock_code])



@app.route('/inventory', methods=['GET']) 
def get_inventory(): 
    symbol = request.args.get('stockCode', '2330')  
    transactions = Inventory.query.filter_by(stock_code=symbol).all()  # 使用 SQLAlchemy 查詢
    results = [
        {
            'id': transaction.id,
            'stock_code': transaction.stock_code,
            'transaction_type': transaction.transaction_type,
            'stock_quantity': transaction.stock_quantity,
            'average_price': str(transaction.average_price),
            'total_amount': str(transaction.total_amount),
            'cost': str(transaction.cost),
            'reference_price': str(transaction.reference_price),
            'market_value': str(transaction.market_value),
            'estimated_fee': str(transaction.estimated_fee),
            'estimated_tax': str(transaction.estimated_tax),
            'reference_profit_loss': str(transaction.reference_profit_loss),
            'profit_loss_rate': str(transaction.profit_loss_rate),
            'details': transaction.details,
            'date': transaction.date.isoformat() if transaction.date else None,
            'transaction_price': str(transaction.transaction_price),
            'transaction_quantity': transaction.transaction_quantity,
            'net_amount': str(transaction.net_amount),
        }
        for transaction in transactions
    ]
    return jsonify(results)

@app.route('/transactions', methods=['POST'])
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

@app.route('/transactions/offset', methods=['POST'])
def offset_transaction():
    data = request.json
    stock_code = data['stockCode']
    inventory = data['inventory']  # 要沖銷的股數，這裡是列表
    # offset_quantities = data['quantities']  # 要沖銷的股數，這裡是列表
    transaction_date = data['transactionDate']  # 沖銷的日期
    # inventory_uuids = data['inventory_uuids']  # 前端傳來的庫存 UUID 列表

    # 查找該股票的最新一筆交易（sell_history 的資料）
    # transaction_record = Transaction.query.filter_by(stock_code=stock_code).order_by(Transaction.transaction_date.desc()).first()

    # if not transaction_record:
        # return jsonify({'message': 'Transaction not found!'}), 404

    # total_offset_quantity = sum(offset_quantities)  # 計算所有沖銷股數的總和
    # if total_offset_quantity > transaction_record.quantity:  # 確保沖銷不超過成交股數
    #     return jsonify({'message': 'Offset quantity exceeds available quantity!'}), 400

    # 更新庫存資料
    inventory_items = Inventory.query.filter_by(stock_code=stock_code).order_by(Inventory.transaction_date).all()

    remaining_quantity_to_offset = total_offset_quantity
    b_uuids = []  # 用來儲存 transaction_history 的 UUID
    sell_history_uuid = uuid.uuid4()  # 生成 sell_history 的 UUID

    for i, inventory in enumerate(inventory_items):
        if inventory.remaining_quantity > 0:
            # 計算這筆沖銷的股數
            offset_quantity = min(inventory.remaining_quantity, remaining_quantity_to_offset)
            inventory.remaining_quantity -= offset_quantity
            remaining_quantity_to_offset -= offset_quantity

            # 創建 transaction_history 紀錄
            transaction_history_record = TransactionHistory(
                id=uuid.uuid4(),
                transaction_date=transaction_date,
                stock_code=stock_code,
                offset_quantity=offset_quantity,
                original_inventory_uuid=inventory_uuids[i],  # 前端傳來的庫存 UUID
                sell_history_uuid=sell_history_uuid  # 連結到 sell_history 的 UUID
            )
            db.session.add(transaction_history_record)
            b_uuids.append(transaction_history_record.id)  # 將 transaction_history 的 UUID 添加到陣列中

            # 如果所有沖銷股數已完成，則跳出循環
            if remaining_quantity_to_offset == 0:
                break

    # 更新 sell_history 紀錄
    sell_history_record = SellHistory(
        id=sell_history_uuid,
        transaction_date=transaction_date,
        stock_code=symbol,
        quantity=transaction_record.quantity,
        remaining_quantity=transaction_record.quantity - total_offset_quantity,
        offset_transaction_uuids=b_uuids  # 將 transaction_history 的 UUID 陣列儲存
    )
    db.session.add(sell_history_record)

    # 提交庫存和歷史紀錄的變更
    db.session.commit()

    return jsonify({'message': 'Offset successful!'}), 200

if __name__ == '__main__':
    app.run(port=5001, debug=True)