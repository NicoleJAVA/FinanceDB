
# import uuid
# from datetime import datetime
# from db import db

# class SellHistory(db.Model):
#     __tablename__ = 'sell_history'

#     transaction_date = db.Column(db.DateTime, nullable=False)  # 成交日期
#     stock_code = db.Column(db.String(50), nullable=False)  # 股票代碼
#     product_name = db.Column(db.String(255))  # 商品名稱
#     unit_price = db.Column(db.Float)  # 成交單價
#     quantity = db.Column(db.Integer)  # 成交股數
#     transaction_value = db.Column(db.Float)  # 成交價金
#     fee = db.Column(db.Float)  # 手續費
#     tax = db.Column(db.Float)  # 交易稅
#     net_amount = db.Column(db.Float)  # 淨收付金額
#     remaining_quantity = db.Column(db.Integer)  # 沖銷剩餘股數
#     profit_loss = db.Column(db.Float)  # 損益試算
#     data_uuid = db.Column(db.String(36), nullable=False, primary_key=True, default=lambda: str(uuid.uuid4()))  # 這次賣出記錄的 UUID
#     # created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 資料創建時間
#     transaction_history_uuids = db.Column(db.JSON, nullable=False)

#     def __init__(self, **kwargs):
#         self.data_uuid = kwargs.get('data_uuid', str(uuid.uuid4()))
#         super().__init__(**kwargs)

#     # def __init__(self, data_uuid, transaction_date, stock_code, product_name, unit_price, quantity, transaction_value,
#     #              fee, tax, net_amount, remaining_quantity, profit_loss, transaction_history_uuids):
#     #     self.transaction_date = transaction_date
#     #     self.stock_code = stock_code
#     #     self.product_name = product_name
#     #     self.unit_price = unit_price
#     #     self.quantity = quantity
#     #     self.transaction_value = transaction_value
#     #     self.fee = fee
#     #     self.tax = tax
#     #     self.net_amount = net_amount
#     #     self.remaining_quantity = remaining_quantity
#     #     self.profit_loss = profit_loss
#     #     self.transaction_history_uuids = transaction_history_uuids
#     #     if data_uuid:
#     #         self.data_uuid = data_uuid
#     #     else:
#     #         self.data_uuid = str(uuid.uuid4())  # 自動生成 UUID

# class Inventory(db.Model):
#     __tablename__ = 'inventory'
    
#     # id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     uuid = db.Column(db.String(36), primary_key=True, nullable=False, unique=True)  
#     stock_code = db.Column(db.String(255), nullable=False)
#     transaction_type = db.Column(db.Enum('Buy', 'Sell', 'Dividend', 'Stock Split'), nullable=False)
#     stock_quantity = db.Column(db.Integer, nullable=False)
#     average_price = db.Column(db.Numeric(10, 2), nullable=False)
#     total_amount = db.Column(db.Numeric(10, 2), nullable=False)
#     cost = db.Column(db.Numeric(10, 2), nullable=False)
#     reference_price = db.Column(db.Numeric(10, 2), nullable=False)
#     market_value = db.Column(db.Numeric(10, 2), nullable=False)
#     estimated_fee = db.Column(db.Numeric(10, 2), nullable=False)
#     estimated_tax = db.Column(db.Numeric(10, 2), nullable=False)
#     reference_profit_loss = db.Column(db.Numeric(10, 2), nullable=False)
#     profit_loss_rate = db.Column(db.Numeric(5, 2), nullable=False)
#     details = db.Column(db.Text)
#     date = db.Column(db.Date)
#     transaction_price = db.Column(db.Numeric(10, 2))
#     transaction_quantity = db.Column(db.Integer)
#     net_amount = db.Column(db.Numeric(10, 2))

#     # 外鍵約束
#     # stocks = db.relationship('Stocks', backref='inventory', foreign_keys=[stock_code])

#     def __init__(self, **kwargs):
#         # 自動生成 UUID，如無 uuid 傳入則生成一個
#         self.uuid = kwargs.get('uuid', str(uuid.uuid4()))
#         super().__init__(**kwargs)


# class TransactionHistory(db.Model):
#     __tablename__ = 'transaction_history'
    
#     # id = db.Column(db.Integer, primary_key=True)
#     uuid = db.Column(db.String(36), primary_key=True, nullable=False, unique=True)  
#     transaction_uuid = db.Column(db.String(36), nullable=False, unique=True)
#     inventory_uuid = db.Column(db.String(36), nullable=False)
#     write_off_quantity = db.Column(db.Integer, nullable=False)
#     stock_code = db.Column(db.String(255), nullable=False)
#     transaction_date = db.Column(db.Date, nullable=False)
#     sell_record_uuid = db.Column(db.String(36), nullable=False)

#     def __init__(self, **kwargs):
#         # 自動生成 UUID，如無 uuid 傳入則生成一個
#         self.uuid = kwargs.get('uuid', str(uuid.uuid4()))
#         super().__init__(**kwargs)