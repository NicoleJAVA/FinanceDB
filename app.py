import uuid
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from sellHistory import api_routes
from db import db

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://localhost:3006"}})

# 設定 SQLAlchemy 資料庫連線
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/stock_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
app.register_blueprint(api_routes)

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
    uuid = db.Column(db.String(36), nullable=False, unique=True)  # 定義 uuid 欄位

    # 外鍵約束
    # stocks = db.relationship('Stocks', backref='inventory', foreign_keys=[stock_code])

# 這裡的 Stocks 是假設存在的股票模型，你需要根據你的實際情況來調整

class SellHistory(db.Model):
    __tablename__ = 'sell_history'

    # id = db.Column(db.Integer, primary_key=True)  # 自增的主鍵
    transaction_date = db.Column(db.DateTime, nullable=False)  # 成交日期
    stock_code = db.Column(db.String(50), nullable=False)  # 股票代碼
    product_name = db.Column(db.String(255))  # 商品名稱
    unit_price = db.Column(db.Float)  # 成交單價
    quantity = db.Column(db.Integer)  # 成交股數
    transaction_value = db.Column(db.Float)  # 成交價金
    fee = db.Column(db.Float)  # 手續費
    tax = db.Column(db.Float)  # 交易稅
    net_amount = db.Column(db.Float)  # 淨收付金額
    remaining_quantity = db.Column(db.Integer)  # 沖銷剩餘股數
    profit_loss = db.Column(db.Float)  # 損益試算
    # inventory_uuids = db.Column(ARRAY(db.String))  # 存放 inventory 的 UUID 陣列
    data_uuid = db.Column(db.String(36), nullable=False, primary_key=True, default=lambda: str(uuid.uuid4()))  # 這次賣出記錄的 UUID
    # created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 資料創建時間
    inventory_uuids = db.Column(db.JSON, nullable=False)

    def __init__(self, data_uuid, transaction_date, stock_code, product_name, unit_price, quantity, transaction_value,
                 fee, tax, net_amount, remaining_quantity, profit_loss, inventory_uuids):
        self.transaction_date = transaction_date
        self.stock_code = stock_code
        self.product_name = product_name
        self.unit_price = unit_price
        self.quantity = quantity
        self.transaction_value = transaction_value
        self.fee = fee
        self.tax = tax
        self.net_amount = net_amount
        self.remaining_quantity = remaining_quantity
        self.profit_loss = profit_loss
        self.inventory_uuids = inventory_uuids
        if data_uuid:
            self.data_uuid = data_uuid
        else:
            self.data_uuid = str(uuid.uuid4())  # 自動生成 UUID

class TransactionHistory(db.Model):
    __tablename__ = 'transaction_history'
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_uuid = db.Column(db.String(36), nullable=False)
    write_off_quantity = db.Column(db.Integer, nullable=False)
    stock_code = db.Column(db.String(255), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    sell_record_uuid = db.Column(db.String(36), nullable=False)

# @app.route('/inventory', methods=['GET']) 
# def get_inventory(): 
#     symbol = request.args.get('stockCode', '2330')  
#     transactions = Inventory.query.filter_by(stock_code=symbol).all()  # 使用 SQLAlchemy 查詢
#     results = [
#         {
#             'id': transaction.id,
#             'stock_code': transaction.stock_code,
#             'transaction_type': transaction.transaction_type,
#             'stock_quantity': transaction.stock_quantity,
#             'average_price': str(transaction.average_price),
#             'total_amount': str(transaction.total_amount),
#             'cost': str(transaction.cost),
#             'reference_price': str(transaction.reference_price),
#             'market_value': str(transaction.market_value),
#             'estimated_fee': str(transaction.estimated_fee),
#             'estimated_tax': str(transaction.estimated_tax),
#             'reference_profit_loss': str(transaction.reference_profit_loss),
#             'profit_loss_rate': str(transaction.profit_loss_rate),
#             'details': transaction.details,
#             'date': transaction.date.isoformat() if transaction.date else None,
#             'transaction_price': str(transaction.transaction_price),
#             'transaction_quantity': transaction.transaction_quantity,
#             'net_amount': str(transaction.net_amount),
#             'uuid': str(transaction.uuid)
#         }
#         for transaction in transactions
#     ]
#     return jsonify(results)

@app.route('/inventory', methods=['GET']) 
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
    # 將 sell_record 及其對應的 inventory_uuids 存入 SellHistory 表格
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
        'inventory_uuids': inventory_uuids,  # 存放 inventory 的 UUID 列表
    }

    # 假設使用一個 ORM 或 SQLAlchemy 來存入數據庫
    db.session.add(SellHistory(**sell_history_entry))
    db.session.commit()

def convert_string_to_number():
    # 取得所有 inventory 資料
    inventories = Inventory.query.all()
    print('\n\n inv ', inventories)
    for inventory in inventories:
        print(inventory.average_price)
        try:
                        
            print('\n\n avg  \n\n', type(inventory.average_price))
            inventory.average_price = float(inventory.average_price)
            inventory.total_amount = float(inventory.total_amount)
            inventory.cost = float(inventory.cost)
            inventory.reference_price = float(inventory.reference_price)
            inventory.market_value = float(inventory.market_value)
            inventory.estimated_fee = float(inventory.estimated_fee)
            inventory.estimated_tax = float(inventory.estimated_tax)
            inventory.reference_profit_loss = float(inventory.reference_profit_loss)
            inventory.profit_loss_rate = float(inventory.profit_loss_rate)
            inventory.transaction_price = float(inventory.transaction_price)
            inventory.net_amount = float(inventory.net_amount)
            # 嘗試將字串轉換為浮點數，並更新到資料庫
            # if isinstance(inventory.average_price, str):
            #     print('\n\n avg  \n\n')
            #     inventory.average_price = float(inventory.average_price)
            # if isinstance(inventory.total_amount, str):
            #     inventory.total_amount = float(inventory.total_amount)
            # if isinstance(inventory.cost, str):
            #     inventory.cost = float(inventory.cost)
            # if isinstance(inventory.reference_price, str):
            #     inventory.reference_price = float(inventory.reference_price)
            # if isinstance(inventory.market_value, str):
            #     inventory.market_value = float(inventory.market_value)
            # if isinstance(inventory.estimated_fee, str):
            #     inventory.estimated_fee = float(inventory.estimated_fee)
            # if isinstance(inventory.estimated_tax, str):
            #     inventory.estimated_tax = float(inventory.estimated_tax)
            # if isinstance(inventory.reference_profit_loss, str):
            #     inventory.reference_profit_loss = float(inventory.reference_profit_loss)
            # if isinstance(inventory.profit_loss_rate, str):
            #     inventory.profit_loss_rate = float(inventory.profit_loss_rate)
            # if isinstance(inventory.transaction_price, str):
            #     inventory.transaction_price = float(inventory.transaction_price)
            # if isinstance(inventory.net_amount, str):
            #     inventory.net_amount = float(inventory.net_amount)

            db.session.add(inventory)  # 標記為已更改
        except ValueError as e:
            print(f"轉換錯誤: {e}，對於資料: {inventory.id}")

    db.session.commit()  # 提交所有更改
    print("convent succ")

if __name__ == '__main__':
    with app.app_context():  # 建立應用程式上下文
        db.create_all()  # 在上下文中創建資料表
        convert_string_to_number()
    app.run(port=5001, debug=True)