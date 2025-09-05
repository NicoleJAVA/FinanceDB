import uuid
from datetime import datetime
from db import db
from sqlalchemy.dialects.postgresql import NUMERIC


class SellHistory(db.Model):
    __tablename__ = 'sell_history'

    data_uuid = db.Column(db.String(36), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    transaction_date = db.Column(db.DateTime, nullable=False)  
    stock_code = db.Column(db.String(50), nullable=False)  
    product_name = db.Column(db.String(255))  
    unit_price = db.Column(db.Float)  
    quantity = db.Column(db.Integer)  
    transaction_value = db.Column(db.Float)  
    fee = db.Column(db.Float)  
    tax = db.Column(db.Float)  
    net_amount = db.Column(db.Float)  
    remaining_quantity = db.Column(db.Integer)  
    profit_loss = db.Column(db.Float)  
    transaction_history_uuids = db.Column(db.JSON, nullable=False)

    def __init__(self, **kwargs):
        self.data_uuid = kwargs.get('data_uuid', str(uuid.uuid4()))
        super().__init__(**kwargs)


class Inventory(db.Model):
    __tablename__ = 'inventory'

    #inventory 新增欄位 SOP 4
    
    uuid = db.Column(db.String(36), primary_key=True, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))  
    stock_code = db.Column(db.String(255), nullable=False)
    transaction_type = db.Column(db.Enum('Buy', 'Sell', 'Dividend', 'Stock Split', name='transaction_type_enum'), nullable=False)
    
    # 交易相關欄位
    date = db.Column(db.Date, nullable=False)  # 成交日期
    transaction_quantity = db.Column(db.Integer, nullable=False)  # 成交股數
    transaction_value = db.Column(db.Numeric(10, 2), nullable=False)  # 成交價金 (原 total_amount)
    estimated_fee = db.Column(db.Numeric(10, 2), nullable=False)  # 手續費
    estimated_tax = db.Column(db.Numeric(10, 2), nullable=False)  # 交易稅
    net_amount = db.Column(db.Numeric(10, 2), nullable=False)  # 淨收付金額
    unit_price = db.Column(db.Integer, nullable=False, default=lambda: 666 if uuid.uuid4().int % 2 == 0 else 777)  # 666 or 777 隨機
    remarks = db.Column(db.String(255), nullable=False)

    def __init__(self, **kwargs):
        self.uuid = kwargs.get('uuid', str(uuid.uuid4()))
        super().__init__(**kwargs)


class TransactionHistory(db.Model):
    __tablename__ = 'transaction_history'
    
    uuid = db.Column(db.String(36), primary_key=True, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    transaction_uuid = db.Column(db.String(36), nullable=False, unique=True)
    inventory_uuid = db.Column(db.String(36), nullable=False)
    write_off_quantity = db.Column(db.Integer, nullable=False)
    stock_code = db.Column(db.String(255), nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False)
    sell_record_uuid = db.Column(db.String(36), nullable=False)
        # === 新增的 B_before / B_after 欄位 ===
    quantity_before    = db.Column(db.Integer)
    unit_price_before  = db.Column(NUMERIC(18, 4))
    net_amount_before  = db.Column(NUMERIC(18, 2))

    remaining_quantity = db.Column(db.Integer)
    amortized_cost     = db.Column(NUMERIC(18, 2))
    amortized_income   = db.Column(NUMERIC(18, 2))
    profit_loss        = db.Column(NUMERIC(18, 2))
    profit_loss_2      = db.Column(NUMERIC(18, 2))

    def __init__(self, **kwargs):
        self.uuid = kwargs.get('uuid', str(uuid.uuid4()))
        super().__init__(**kwargs)
