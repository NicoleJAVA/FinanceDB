import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request
from model.model import SellHistory, Inventory, TransactionHistory
from db import db

sell_history_api = Blueprint('sell_history_api', __name__)


@sell_history_api.route('/sellHistory/all', methods=['GET'])
def get_all_sell_history():
    # 查詢所有 SellHistory 資料
    history_rows = SellHistory.query.all()
    results = []

    for history in history_rows:
        # 查詢 TransactionHistory 資料，根據 SellHistory 的 data_uuid 找出對應的 transaction_history
        transaction_history_rows = TransactionHistory.query.filter_by(sell_record_uuid=history.data_uuid).all()

        # 取得所有 transaction_history 中的 inventory_uuid
        inventory_uuids = [th.inventory_uuid for th in transaction_history_rows]

        # 查詢對應的 Inventory 資料
        detail_data = Inventory.query.filter(Inventory.uuid.in_(inventory_uuids)).all()
        
        # 將 Inventory 資料轉換為 dict 並組成 array
        detail_data_list = [
            {
                #inventory 新增欄位 SOP 2
                "uuid": inventory.uuid,
                "stock_code": inventory.stock_code,
                "transaction_type": inventory.transaction_type,
                "stock_quantity": inventory.stock_quantity,
                "average_price": float(inventory.average_price),
                "total_amount": float(inventory.total_amount),
                "cost": float(inventory.cost),
                "reference_price": float(inventory.reference_price),
                "market_value": float(inventory.market_value),
                "estimated_fee": float(inventory.estimated_fee),
                "estimated_tax": float(inventory.estimated_tax),
                "reference_profit_loss": float(inventory.reference_profit_loss),
                "profit_loss_rate": float(inventory.profit_loss_rate),
                "details": inventory.details,
                "date": inventory.date.isoformat() if inventory.date else None,
                # "transaction_price": float(inventory.transaction_price) if inventory.transaction_price else None,
                "transaction_quantity": inventory.transaction_quantity,
                "net_amount": float(inventory.net_amount) if inventory.net_amount else None,
                "remarks": inventory.remarks
            }
            for inventory in detail_data
        ]

        # 組合 SellHistory 資料和對應的 detailData
        results.append({
            "uuid": history.data_uuid,
            "transaction_date": history.transaction_date.isoformat(),
            "stock_code": history.stock_code,
            "product_name": history.product_name,
            "unit_price": history.unit_price,
            "quantity": history.quantity,
            "transaction_value": history.transaction_value,
            "fee": history.fee,
            "tax": history.tax,
            "net_amount": history.net_amount,
            "remaining_quantity": history.remaining_quantity,
            "profit_loss": history.profit_loss,
            "transaction_history_uuids": history.transaction_history_uuids,
            "detailData": detail_data_list
        })

    print('\n\n\n\n', "SELL HISTORY ", results, '\n\n\n\n')
    return jsonify(results)

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
        'transaction_history_uuids': ",".join(preview_th_uuids),
    }), 200


#  todo dele
# @sell_history_api.route('/sellHistory/all', methods=['GET'])
# def get_all_sell_history():
#     # 查詢所有 SellHistory 資料
#     history_rows = SellHistory.query.all()
#     results = []

#     for history in history_rows:
#         # 查詢對應的 Inventory 資料
#         detail_data = Inventory.query.filter_by(stock_code=history.stock_code).all()
        
#         # 將 Inventory 資料轉換為 dict 並組成 array
#         detail_data_list = [
#             {
#                 "uuid": inventory.uuid,
#                 "stock_code": inventory.stock_code,
#                 "transaction_type": inventory.transaction_type,
#                 "stock_quantity": inventory.stock_quantity,
#                 "average_price": float(inventory.average_price),
#                 "total_amount": float(inventory.total_amount),
#                 "cost": float(inventory.cost),
#                 "reference_price": float(inventory.reference_price),
#                 "market_value": float(inventory.market_value),
#                 "estimated_fee": float(inventory.estimated_fee),
#                 "estimated_tax": float(inventory.estimated_tax),
#                 "reference_profit_loss": float(inventory.reference_profit_loss),
#                 "profit_loss_rate": float(inventory.profit_loss_rate),
#                 "details": inventory.details,
#                 "date": inventory.date.isoformat() if inventory.date else None,
#                 "transaction_price": float(inventory.transaction_price) if inventory.transaction_price else None,
#                 "transaction_quantity": inventory.transaction_quantity,
#                 "net_amount": float(inventory.net_amount) if inventory.net_amount else None
#             }
#             for inventory in detail_data
#         ]

#         # 組合 SellHistory 資料和對應的 detailData
#         results.append({
#             "data_uuid": history.data_uuid,
#             "transaction_date": history.transaction_date.isoformat(),
#             "stock_code": history.stock_code,
#             "product_name": history.product_name,
#             "unit_price": history.unit_price,
#             "quantity": history.quantity,
#             "transaction_value": history.transaction_value,
#             "fee": history.fee,
#             "tax": history.tax,
#             "net_amount": history.net_amount,
#             "remaining_quantity": history.remaining_quantity,
#             "profit_loss": history.profit_loss,
#             "transaction_history_uuids": history.transaction_history_uuids,
#             "detailData": detail_data_list
#         })

#     print('\n\n\n\n', "SELL HISTORY ", results, '\n\n\n\n')
#     return jsonify(results)
