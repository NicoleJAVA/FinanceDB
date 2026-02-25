# init_db.py
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from flask import Blueprint, jsonify, request



# 在 navicat 裡查看現在的帳號
# SELECT current_user;


init_db_api = Blueprint('init_db_api', __name__)

DB_NAME = "stock_db"
DB_USER = "admin"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_PORT = "5432"

@init_db_api.route('/init_db', methods=['POST']) 
def init_db_route():
    print('\n\n初始化 DB\n\n')
    init_db()
    return {"status": "ok"}

# @app.route('/init_db', methods=['POST']) todo dele
# def init_db_route():
#     init_db()
#     return {"status": "ok"}


def init_db():
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
    exists = cur.fetchone()

    if not exists:
        cur.execute(f"CREATE DATABASE {DB_NAME} WITH OWNER = {DB_USER};")
        print("✔ 已建立資料庫 stock_db")

    cur.close()
    conn.close()

    try:
        conn2 = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    except psycopg2.OperationalError:
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE {DB_NAME} WITH OWNER = {DB_USER};")
        cur.close()
        conn.close()

        conn2 = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

    conn2.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur2 = conn2.cursor()

    cur2.execute("""
        SELECT tablename FROM pg_tables WHERE schemaname='public';
    """)
    existing_tables = {r[0] for r in cur2.fetchall()}

    # enum
    cur2.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'transaction_type_enum'
        ) THEN
            CREATE TYPE transaction_type_enum AS ENUM ('Buy', 'Sell', 'Dividend', 'Stock Split');
        END IF;
    END$$;
    """)

    # inventory
    if "inventory" not in existing_tables:
        cur2.execute("""
            CREATE TABLE inventory (
                uuid CHAR(36) PRIMARY KEY NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT NOW(),
                stock_code VARCHAR(255) NOT NULL,
                transaction_type transaction_type_enum NOT NULL,
                date DATE NOT NULL,
                transaction_quantity INTEGER NOT NULL,
                available_quantity INTEGER NOT NULL,
                transaction_value NUMERIC(10,2) NOT NULL,
                estimated_fee NUMERIC(10,2) NOT NULL,
                estimated_tax NUMERIC(10,2) NOT NULL,
                net_amount NUMERIC(10,2) NOT NULL,
                unit_price INTEGER NOT NULL,
                remarks TEXT
            );
        """)
    else:
        # 已存在時補上 remarks 欄位（如果沒有）
        cur2.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'inventory';
        """)
        cols = {r[0] for r in cur2.fetchall()}
        if "remarks" not in cols:
            cur2.execute("ALTER TABLE inventory ADD COLUMN remarks TEXT;")

    # SellHistory 欄位設定 step. 2
    # sell_history
    if "sell_history" not in existing_tables:
        cur2.execute("""
            CREATE TABLE sell_history (
                data_uuid CHAR(36) PRIMARY KEY NOT NULL,
                created_at TIMESTAMP NOT NULL,
                transaction_date TIMESTAMP NOT NULL,
                stock_code VARCHAR(50) NOT NULL,
                product_name VARCHAR(255),
                unit_price FLOAT8,
                transaction_quantity INTEGER,
                transaction_value FLOAT8,
                fee FLOAT8,
                tax FLOAT8,
                net_amount FLOAT8,
                remaining_quantity INTEGER,
                profit_loss FLOAT8,
                sell_detail_history_uuids JSON NOT NULL
                remarks TEXT
            );
        """)
   # SellHistory 欄位設定 step. 3
    else:
        cur2.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'sell_history';
        """)
        cols = {r[0] for r in cur2.fetchall()}
        if "remarks" not in cols:
            cur2.execute("ALTER TABLE sell_history ADD COLUMN remarks TEXT;")

    # sell_detail_history
    if "sell_detail_history" not in existing_tables:
        cur2.execute("""
            CREATE TABLE sell_detail_history (
                uuid CHAR(36) PRIMARY KEY NOT NULL UNIQUE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                transaction_uuid CHAR(36) NOT NULL UNIQUE,
                inventory_uuid CHAR(36) NOT NULL,
                write_off_quantity INTEGER NOT NULL,
                stock_code VARCHAR(255) NOT NULL,
                transaction_date TIMESTAMP NOT NULL,
                sell_record_uuid CHAR(36) NOT NULL,

                quantity_before INTEGER,
                unit_price_before NUMERIC(18,4),
                net_amount_before NUMERIC(18,2),

                remaining_quantity INTEGER,
                amortized_cost NUMERIC(18,2),
                amortized_income NUMERIC(18,2),
                profit_loss NUMERIC(18,2),
                profit_loss_2 NUMERIC(18,2),

                transaction_type VARCHAR(20)
            );
        """)

    cur2.execute("SELECT COUNT(*) FROM inventory;")
    count = cur2.fetchone()[0]

    if count == 0:
        cur2.execute("""
        INSERT INTO inventory (
            uuid, stock_code, transaction_type, date, transaction_quantity, available_quantity,
            transaction_value, estimated_fee, estimated_tax, net_amount,
            unit_price, remarks
        ) VALUES
        ('A01', '2330', 'Buy', '2024-08-01', 100, 100, 100.00, 1.00, 0.00, 99.00, 100, 'A01'),
        ('A02', '2330', 'Buy', '2024-07-31', 200, 200, 400.00, 2.00, 0.00, 398.00, 200, 'A02TEst'),
        ('A03', '2330', 'Buy', '2024-07-30', 300, 300, 900.00, 3.00, 0.00, 897.00, 300, 'A03 TEST'),
        ('A04', '2330', 'Buy', '2024-07-29', 400, 400, 1600.00, 4.00, 0.00, 1596.00, 400, 'A04-test'),
        ('A05', '2330', 'Buy', '2024-07-28', 500, 500, 2500.00, 5.00, 0.00, 2495.00, 500, '05 test'),
        ('A06', '2330', 'Buy', '2024-07-27', 600, 600, 3600.00, 6.00, 0.00, 3594.00, 600, 'Testing...'),
        ('A07', '2330', 'Buy', '2024-07-26', 700, 700, 4900.00, 7.00, 0.00, 4893.00, 700, 'test123'),
        ('A08', '2330', 'Buy', '2024-07-25', 800, 800, 6400.00, 8.00, 0.00, 6392.00, 800, 'testtest'),
        ('A09', '2330', 'Buy', '2024-07-24', 900, 900, 8100.00, 9.00, 0.00, 8091.00, 900, 'A09'),
        ('A10', '2330', 'Buy', '2024-07-23', 1000, 1000, 10000.00, 10.00, 0.00, 9990.00, 1000, 'A10');
        """)

    cur2.close()
    conn2.close()
    return True
