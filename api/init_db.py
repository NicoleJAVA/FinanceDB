from datetime import datetime
from flask import Blueprint
from model.model import Inventory
from db import db

init_db_api = Blueprint('init_db_api', __name__)

@init_db_api.route('/init_db', methods=['POST']) 
def init_db_route():
    print('\n\n初始化 DB\n\n')
    init_db()
    return {"status": "ok"}


def init_db():
    db.create_all()

    if Inventory.query.count() > 0:
        return True

    now = datetime.utcnow().replace(microsecond=0)
    seed_rows = [
        ('A01', '2024-08-01', 100, 100.00, 1.00, 0.00, 99.00, 100, 'A01'),
        ('A02', '2024-07-31', 200, 400.00, 2.00, 0.00, 398.00, 200, 'A02TEst'),
        ('A03', '2024-07-30', 300, 900.00, 3.00, 0.00, 897.00, 300, 'A03 TEST'),
        ('A04', '2024-07-29', 400, 1600.00, 4.00, 0.00, 1596.00, 400, 'A04-test'),
        ('A05', '2024-07-28', 500, 2500.00, 5.00, 0.00, 2495.00, 500, '05 test'),
        ('A06', '2024-07-27', 600, 3600.00, 6.00, 0.00, 3594.00, 600, 'Testing...'),
        ('A07', '2024-07-26', 700, 4900.00, 7.00, 0.00, 4893.00, 700, 'test123'),
        ('A08', '2024-07-25', 800, 6400.00, 8.00, 0.00, 6392.00, 800, 'testtest'),
        ('A09', '2024-07-24', 900, 8100.00, 9.00, 0.00, 8091.00, 900, 'A09'),
        ('A10', '2024-07-23', 1000, 10000.00, 10.00, 0.00, 9990.00, 1000, 'A10'),
    ]

    db.session.add_all([
        Inventory(
            uuid=row_uuid,
            stock_code='2330',
            transaction_type='Buy',
            created_at=now,
            date=datetime.strptime(date_text, '%Y-%m-%d').date(),
            transaction_quantity=quantity,
            available_quantity=quantity,
            transaction_value=transaction_value,
            estimated_fee=estimated_fee,
            estimated_tax=estimated_tax,
            net_amount=net_amount,
            unit_price=unit_price,
            remarks=remarks,
        )
        for (
            row_uuid,
            date_text,
            quantity,
            transaction_value,
            estimated_fee,
            estimated_tax,
            net_amount,
            unit_price,
            remarks,
        ) in seed_rows
    ])
    db.session.commit()
    return True
