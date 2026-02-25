from flask import Blueprint, request, jsonify
from model.model import Inventory
from db import db
import uuid
from datetime import datetime

buy_api = Blueprint('buy_api', __name__)

@buy_api.route('/buy', methods=['POST'])
def buy_transaction():
    data = request.get_json(silent=True) or {}
    try:
        required = ['stock_code', 'date', 'transaction_quantity', 'transaction_value', 'estimated_fee', 'estimated_tax', 'net_amount', 'unit_price']
        missing = [k for k in required if k not in data]
        if missing:
            return jsonify({
                'status': 'error',
                'message': f"missing fields: {', '.join(missing)}"
            }), 400

        new_uuid = str(uuid.uuid4())
        new_transaction = Inventory(
            uuid=new_uuid,
            stock_code=data['stock_code'],
            transaction_type='Buy',
            created_at=datetime.utcnow().replace(microsecond=0),
            date=datetime.strptime(data['date'], '%Y-%m-%d'),
            transaction_quantity=int(data['transaction_quantity']),
            available_quantity=int(data['transaction_quantity']),
            transaction_value=float(data['transaction_value']),
            estimated_fee=float(data['estimated_fee']),
            estimated_tax=float(data['estimated_tax']),
            net_amount=float(data['net_amount']),
            unit_price=int(float(data['unit_price'])),
            remarks=data.get('remarks', '')
        )

        db.session.add(new_transaction)
        db.session.commit()

        saved_data = Inventory.query.filter_by(uuid=new_uuid).first()
        result = {
            'uuid': saved_data.uuid,
            'stock_code': saved_data.stock_code,
            'created_at': saved_data.created_at,
            'transaction_type': saved_data.transaction_type,
            'date': saved_data.date.isoformat(),
            'transaction_quantity': saved_data.transaction_quantity,
            'transaction_value': float(saved_data.transaction_value),
            'estimated_fee': float(saved_data.estimated_fee),
            'estimated_tax': float(saved_data.estimated_tax),
            'net_amount': float(saved_data.net_amount),
            'unit_price': saved_data.unit_price,
            'remarks': saved_data.remarks
        }

        return jsonify({
            'status': 'success',
            'message': 'Buy transaction inserted successfully.',
            'data': result
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
