# from flask import Flask, request, jsonify
# import MySQLdb

# app = Flask(__name__)

# # 資料庫連線設定
# db = MySQLdb.connect(
#     host="localhost",
#     user="root",
#     passwd="123456",
#     db="stock_db"
# )

# @app.route('/')
# def home():
#     return "Hello, Flask!"
    
# @app.route('/transactions', methods=['GET'])
# def get_transactions():
#     cursor = db.cursor(MySQLdb.cursors.DictCursor)
#     cursor.execute("SELECT * FROM transactions")
#     transactions = cursor.fetchall()
#     cursor.close()
#     return jsonify(transactions)

# @app.route('/transactions', methods=['POST'])
# def add_transaction():
#     data = request.json
#     cursor = db.cursor()
#     cursor.execute("""
#         INSERT INTO transactions (transaction_date, symbol, product_name, transaction_type, unit_price, quantity, total_amount, fee, tax, net_amount, remaining_quantity, profit_loss)
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """, (data['transaction_date'], data['symbol'], data['product_name'], data['transaction_type'], data['unit_price'], data['quantity'], data['total_amount'], data['fee'], data['tax'], data['net_amount'], data['remaining_quantity'], data['profit_loss']))
#     db.commit()
#     cursor.close()
#     return jsonify({'message': 'Transaction added successfully!'}), 201

# if __name__ == '__main__':
#     app.run(debug=True)
