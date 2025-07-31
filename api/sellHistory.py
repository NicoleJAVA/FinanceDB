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
