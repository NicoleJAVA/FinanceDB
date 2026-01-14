import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from model.model import SellHistory, Inventory, SellDetailHistory
from db import db

sell_history_api = Blueprint('sell_history_api', __name__)


@sell_history_api.route('/sellHistory/all', methods=['GET'])
def sell_history_all():
    rows = db.session.query(SellHistory).order_by(SellHistory.transaction_date.desc()).all()
    items = []
    for r in rows:
        items.append({
            'data_uuid': getattr(r, 'data_uuid', None),
            'created_at': getattr(r, 'created_at', ''),
            'transaction_date': getattr(r, 'transaction_date', ''),
            'stock_code': getattr(r, 'stock_code', ''),
            'product_name': getattr(r, 'product_name', ''),
            'unit_price': getattr(r, 'unit_price', 0),
            'quantity': getattr(r, 'quantity', 0),
            'transaction_value': getattr(r, 'transaction_value', 0),
            'fee': getattr(r, 'fee', 0),
            'tax': getattr(r, 'tax', 0),
            'net_amount': getattr(r, 'net_amount', 0),
            'profit_loss': getattr(r, 'profit_loss', 0),
            'sell_detail_history_uuids': str(getattr(r, 'sell_detail_history_uuids', '') or ''), # 逗號字串
        })
    return jsonify(items), 200



# 取得「單筆」 SellHistory
@sell_history_api.route('/sellHistory/one', methods=['GET'])
def get_sell_history_one():
    data_uuid = request.args.get('data_uuid')
    if not data_uuid:
        return jsonify({'error': 'data_uuid is required'}), 400

    row = db.session.query(SellHistory).filter_by(data_uuid=data_uuid).first()
    if not row:
        return jsonify({'error': 'not found'}), 404

    sh = {
        'data_uuid': getattr(row, 'data_uuid', None),
        'transaction_date': getattr(row, 'transaction_date', ''),
        'created_at': getattr(row, 'created_at', ''),
        'stock_code': getattr(row, 'stock_code', ''),
        'product_name': getattr(row, 'product_name', ''),
        'unit_price': getattr(row, 'unit_price', 0),
        'quantity': getattr(row, 'quantity', 0),
        'transaction_value': getattr(row, 'transaction_value', 0),
        'fee': getattr(row, 'fee', 0),
        'tax': getattr(row, 'tax', 0),
        'net_amount': getattr(row, 'net_amount', 0),
        'remaining_quantity': getattr(row, 'remaining_quantity', 0),
        'profit_loss': getattr(row, 'profit_loss', 0),
        'sell_detail_history_uuids': getattr(row, 'sell_detail_history_uuids', ''),
        'remarks': getattr(row, 'remarks', ''),
    }

    snap = None
    if hasattr(row, 'snapshot_json') and getattr(row, 'snapshot_json', None):
        snap = row.snapshot_json

    resp = {'sell_history_entry': sh}
    if snap:
        resp['snapshot_json'] = snap

    return jsonify(resp), 200


@sell_history_api.route('/sellHistory/preview-sell-history', methods=['POST'])
def preview_sell_history():
    from decimal import Decimal, ROUND_HALF_UP
    import uuid
    from datetime import datetime

    def rhup(x):  # Round Half Up -> int
        return int(Decimal(x).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    data = request.json or {}
    sell_record    = data.get('sellRecord', {}) or {}
    inventory_list = data.get('inventory', []) or []

    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    a_entry = {
        'transaction_date': sell_record.get('transaction_date', now_str),
        'stock_code':       sell_record.get('stock_code'),
        'product_name':     sell_record.get('product_name'),
        'unit_price':       sell_record.get('unit_price'),
        'quantity':         sell_record.get('transaction_quantity', 0),
        'transaction_value':sell_record.get('transaction_value', 0),
        'fee':              sell_record.get('estimated_fee', 0),
        'tax':              sell_record.get('estimated_tax', 0),
        'net_amount':       sell_record.get('net_amount', 0),
        'remaining_quantity': sell_record.get('remaining_quantity', 0),
        'profit_loss':        sell_record.get('profit_loss', 0),
    }

    # A 表數值（供 B 明細計算）
    a_net_amt    = Decimal(a_entry['net_amount'] or 0)
    a_qty        = Decimal(a_entry['quantity'] or 1)
    a_unit_price = Decimal(a_entry['unit_price'] or 0)
    a_fee        = Decimal(a_entry['fee'] or 0)
    a_tax        = Decimal(a_entry['tax'] or 0)

    b_items = []
    tot_cost = tot_income = tot_pl = 0

    for it in inventory_list:
        write_off_quantity = int(it.get('writeOffQuantity', 0) or 0)
        if write_off_quantity <= 0:
            continue
        inv = Inventory.query.filter_by(uuid=it['uuid']).first()
        if not inv:
            continue

        inv_qty     = Decimal(inv.transaction_quantity or 0)  # Excel 分母
        write_qty   = Decimal(write_off_quantity)
        inv_net_amt = Decimal(inv.net_amount or 0)

        amortized_cost   = rhup(inv_net_amt * (write_qty / inv_qty))
        amortized_income = rhup(a_net_amt   * (write_qty / a_qty))
        fee_share = rhup(a_fee * (write_qty / a_qty))
        tax_share = rhup(a_tax * (write_qty / a_qty))
        profit_loss = rhup(write_qty * (a_unit_price - Decimal(inv.unit_price))) - (fee_share + tax_share)

        row = {
            'uuid':               inv.uuid,
            'remaining_quantity': int(inv.transaction_quantity) - int(write_off_quantity),
            'amortized_cost':     amortized_cost,
            'amortized_income':   amortized_income,
            'profit_loss':        profit_loss,
        }
        b_items.append(row)
        tot_cost   += amortized_cost
        tot_income += amortized_income
        tot_pl     += profit_loss

    b_totals = {
        'total_amortized_cost':   tot_cost,
        'total_amortized_income': tot_income,
        'total_profit_loss':      tot_pl,
        'count':                  len(b_items),
    }

    preview_th_uuids = [str(uuid.uuid4()) for _ in b_items]

    return jsonify({
        '_preview': True,
        'sell_history_entry': a_entry,
        'b_items': b_items,
        'b_totals': b_totals,
        'sell_detail_history_uuids': ",".join(preview_th_uuids),
    }), 200


