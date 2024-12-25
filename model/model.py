import uuid
from datetime import datetime
from db import db

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
    
    uuid = db.Column(db.String(36), primary_key=True, nullable=False, unique=True, default=lambda: str(uuid.uuid4()))  
    stock_code = db.Column(db.String(255), nullable=False)
    # transaction_type = db.Column(db.Enum('Buy', 'Sell', 'Dividend', 'Stock Split'), nullable=False)
    transaction_type = db.Column(db.Enum('Buy', 'Sell', 'Dividend', 'Stock Split', name='transaction_type_enum'), nullable=False)
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
    transaction_date = db.Column(db.Date, nullable=False)
    sell_record_uuid = db.Column(db.String(36), nullable=False)

    def __init__(self, **kwargs):
        self.uuid = kwargs.get('uuid', str(uuid.uuid4()))
        super().__init__(**kwargs)
