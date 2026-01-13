
from flask import Flask, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.dialects.postgresql import ARRAY
from api.inventory import inventory_api
from api.transaction import transaction_api
from api.buy import buy_api
# from api.history import history_api
from api.sellHistory import sell_history_api
from api.init_db import init_db_api, init_db
from model.model import SellHistory, Inventory, SellDetailHistory
from db import db

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "https://localhost:3006"}})
CORS(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/stock_db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://admin:123456@localhost/stock_db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://admin:123456@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
 
app.register_blueprint(inventory_api)
app.register_blueprint(transaction_api)
# app.register_blueprint(history_api)
app.register_blueprint(sell_history_api)
app.register_blueprint(buy_api)
app.register_blueprint(init_db_api)



def convert_string_to_number():
    
    # 取得所有 inventory 資料
    inventories = Inventory.query.all()
    print('\n\n inv ', inventories)
    for inventory in inventories:
        
        try:
                        
            inventory.transaction_value = float(inventory.transaction_value)
            inventory.estimated_fee = float(inventory.estimated_fee)
            inventory.estimated_tax = float(inventory.estimated_tax)
            inventory.unit_price = float(inventory.unit_price)
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



# if __name__ == '__main__':
#     with app.app_context():  # 建立應用程式上下文
#         db.create_all()  # 在上下文中創建資料表
#         convert_string_to_number()
#     app.run(port=7007, debug=True)


if __name__ == '__main__':
    with app.app_context():
        init_db()
        db.create_all()
        # convert_string_to_number()
    app.run(port=7007, debug=True)