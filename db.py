import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG
from datetime import datetime, timedelta
import hashlib


def get_connection():
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        port=DB_CONFIG['port'],
        charset=DB_CONFIG['charset'],
        cursorclass=DictCursor,
        autocommit=False
    )


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def fetch_all(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def fetch_one(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()
    finally:
        conn.close()


def execute(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def executemany(sql, params_list):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.executemany(sql, params_list)
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def create_database_if_not_exists():
    try:
        temp_config = DB_CONFIG.copy()
        temp_db = temp_config.pop('database')
        conn = pymysql.connect(
            host=temp_config['host'],
            user=temp_config['user'],
            password=temp_config['password'],
            port=temp_config['port'],
            charset=temp_config['charset'],
            cursorclass=DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {temp_db} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.commit()
        conn.close()
        print(f"Database '{temp_db}' ready")
    except Exception as e:
        print(f"Note: Could not create database automatically: {e}")
        print("Please create database manually if it doesn't exist")


def run_migrations():
    create_database_if_not_exists()
    
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(50) PRIMARY KEY,
                    applied_at DATETIME NOT NULL
                )
            """)
            conn.commit()

            cursor.execute("SELECT version FROM schema_migrations")
            applied = {row['version'] for row in cursor.fetchall()}

            migrations = [
                ('001_create_users_clients', MIGRATION_001, None),
                ('002_catalog', MIGRATION_002, None),
                ('003_inventory', MIGRATION_003, None),
                ('004_suppliers_purchase', MIGRATION_004, None),
                ('005_orders_payments', MIGRATION_005, None),
                ('006_custom_requests', MIGRATION_006, None),
                ('007_writeoffs', MIGRATION_007, None),
                ('008_procedure_avg_price', MIGRATION_008, MIGRATION_008_CREATE),
                ('009_function_writeoff_percent', MIGRATION_009, MIGRATION_009_CREATE),
            ]

            for migration_item in migrations:
                if len(migration_item) == 3:
                    version, sql, create_sql = migration_item
                else:
                    version, sql = migration_item
                    create_sql = None
                
                if version not in applied:
                    print(f"Applying migration: {version}")
                    try:
                        if create_sql:
                            try:
                                cursor.execute(sql)
                                conn.commit()
                            except Exception as e:
                                print(f"  Note: {e}")
                            
                            create_sql_clean = create_sql.strip()
                            cursor.execute(create_sql_clean)
                            conn.commit()
                        else:
                            for statement in sql.split(';'):
                                statement = statement.strip()
                                if statement:
                                    cursor.execute(statement)
                        cursor.execute(
                            "INSERT INTO schema_migrations (version, applied_at) VALUES (%s, %s)",
                            (version, datetime.now())
                        )
                        conn.commit()
                        print(f"Migration {version} applied successfully")
                    except Exception as e:
                        print(f"Error applying migration {version}: {e}")
                        conn.rollback()
                        raise

    finally:
        conn.close()


MIGRATION_001 = """
CREATE TABLE IF NOT EXISTS clients (
    client_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('SELLER', 'MANAGER', 'CLIENT') NOT NULL,
    client_id INT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE SET NULL
);
"""

MIGRATION_002 = """
CREATE TABLE IF NOT EXISTS flowers (
    flower_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    variety VARCHAR(100) NOT NULL,
    color VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    shelf_life_days INT NOT NULL,
    is_active TINYINT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS bouquets (
    bouquet_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    occasion VARCHAR(100),
    base_price DECIMAL(10,2) NOT NULL,
    is_active TINYINT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS bouquet_items (
    bouquet_id INT NOT NULL,
    flower_id INT NOT NULL,
    qty INT NOT NULL,
    PRIMARY KEY (bouquet_id, flower_id),
    FOREIGN KEY (bouquet_id) REFERENCES bouquets(bouquet_id) ON DELETE CASCADE,
    FOREIGN KEY (flower_id) REFERENCES flowers(flower_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS packaging (
    packaging_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS accessories (
    accessory_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL
);
"""

MIGRATION_003 = """
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    item_type ENUM('FLOWER', 'BOUQUET', 'PACKAGING', 'ACCESSORY') NOT NULL,
    item_id INT NOT NULL,
    qty INT NOT NULL DEFAULT 0,
    UNIQUE KEY unique_item (item_type, item_id)
);
"""

MIGRATION_004 = """
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS supplier_prices (
    supplier_price_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    item_type ENUM('FLOWER', 'PACKAGING', 'ACCESSORY') NOT NULL,
    item_id INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    UNIQUE KEY unique_supplier_item (supplier_id, item_type, item_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    purchase_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('NEW', 'SENT', 'RECEIVED', 'CANCELLED') NOT NULL DEFAULT 'NEW',
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS purchase_items (
    purchase_item_id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_id INT NOT NULL,
    item_type ENUM('FLOWER', 'PACKAGING', 'ACCESSORY') NOT NULL,
    item_id INT NOT NULL,
    qty INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (purchase_id) REFERENCES purchase_orders(purchase_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS receipts (
    receipt_id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_id INT NULL,
    received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    note TEXT,
    FOREIGN KEY (purchase_id) REFERENCES purchase_orders(purchase_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS receipt_items (
    receipt_item_id INT AUTO_INCREMENT PRIMARY KEY,
    receipt_id INT NOT NULL,
    item_type ENUM('FLOWER', 'PACKAGING', 'ACCESSORY') NOT NULL,
    item_id INT NOT NULL,
    qty INT NOT NULL,
    buy_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id) ON DELETE CASCADE
);
"""

MIGRATION_005 = """
CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    created_by_user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Новый', 'Принят', 'В сборке', 'Готов', 'Выдан', 'Отменен') NOT NULL DEFAULT 'Новый',
    discount_percent DECIMAL(5,2) NOT NULL DEFAULT 0,
    total_sum DECIMAL(10,2) NOT NULL DEFAULT 0,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_type ENUM('FLOWER', 'BOUQUET', 'PACKAGING', 'ACCESSORY') NOT NULL,
    item_id INT NOT NULL,
    qty INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    sum DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT UNIQUE NOT NULL,
    paid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    method ENUM('Наличные', 'Карта') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE RESTRICT
);
"""

MIGRATION_006 = """
CREATE TABLE IF NOT EXISTS custom_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    desired_date DATE NOT NULL,
    wishes TEXT,
    status ENUM('Новая', 'В работе', 'Собрана', 'Отменена') NOT NULL DEFAULT 'Новая',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS custom_request_items (
    request_item_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    flower_id INT NOT NULL,
    qty INT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES custom_requests(request_id) ON DELETE CASCADE,
    FOREIGN KEY (flower_id) REFERENCES flowers(flower_id) ON DELETE RESTRICT
);
"""

MIGRATION_007 = """
CREATE TABLE IF NOT EXISTS write_offs (
    writeoff_id INT AUTO_INCREMENT PRIMARY KEY,
    item_type ENUM('FLOWER') NOT NULL,
    item_id INT NOT NULL,
    qty INT NOT NULL,
    reason ENUM('EXPIRED', 'DAMAGED', 'OTHER') NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

MIGRATION_008 = """DROP PROCEDURE IF EXISTS get_avg_flower_price"""
MIGRATION_008_CREATE = """
CREATE PROCEDURE get_avg_flower_price(
    IN p_name VARCHAR(100),
    IN p_period_type ENUM('MONTH', 'YEAR'),
    IN p_year INT,
    IN p_month INT
)
BEGIN
    DECLARE start_date DATETIME;
    DECLARE end_date DATETIME;
    
    IF p_period_type = 'MONTH' THEN
        SET start_date = DATE(CONCAT(p_year, '-', LPAD(p_month, 2, '0'), '-01'));
        SET end_date = DATE_ADD(start_date, INTERVAL 1 MONTH);
    ELSE
        SET start_date = DATE(CONCAT(p_year, '-01-01'));
        SET end_date = DATE_ADD(start_date, INTERVAL 1 YEAR);
    END IF;
    
    SELECT COALESCE(AVG(ri.buy_price), 0) AS avg_price
    FROM receipt_items ri
    INNER JOIN flowers f ON ri.item_id = f.flower_id AND ri.item_type = 'FLOWER'
    INNER JOIN receipts r ON ri.receipt_id = r.receipt_id
    WHERE f.name = p_name
      AND r.received_at >= start_date
      AND r.received_at < end_date;
END;
"""

MIGRATION_009 = """DROP FUNCTION IF EXISTS get_writeoff_percent"""
MIGRATION_009_CREATE = """
CREATE FUNCTION get_writeoff_percent(p_variety VARCHAR(100))
RETURNS DECIMAL(5,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE writeoff_qty INT DEFAULT 0;
    DECLARE sold_qty INT DEFAULT 0;
    DECLARE total_qty INT DEFAULT 0;
    DECLARE result DECIMAL(5,2) DEFAULT 0;
    
    SELECT COALESCE(SUM(wo.qty), 0) INTO writeoff_qty
    FROM write_offs wo
    INNER JOIN flowers f ON wo.item_id = f.flower_id
    WHERE f.variety = p_variety
      AND wo.created_at >= DATE_SUB(NOW(), INTERVAL 3 MONTH);
    
    SELECT COALESCE(SUM(oi.qty), 0) INTO sold_qty
    FROM order_items oi
    INNER JOIN orders o ON oi.order_id = o.order_id
    INNER JOIN flowers f ON oi.item_id = f.flower_id
    WHERE f.variety = p_variety
      AND oi.item_type = 'FLOWER'
      AND o.status != 'Отменен'
      AND o.created_at >= DATE_SUB(NOW(), INTERVAL 3 MONTH);
    
    SET total_qty = writeoff_qty + sold_qty;
    
    IF total_qty > 0 THEN
        SET result = ROUND((writeoff_qty / total_qty) * 100, 2);
    END IF;
    
    RETURN result;
END;
"""


def seed_data():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as cnt FROM users")
            if cursor.fetchone()['cnt'] > 0:
                print("Database already seeded, skipping...")
                return

            print("Seeding database...")

            clients_data = [
                ('Иванов Иван Иванович', '+7-900-111-22-33', 'ivanov@mail.ru'),
                ('Петрова Мария Сергеевна', '+7-900-222-33-44', 'petrova@mail.ru'),
                ('Сидоров Петр Александрович', '+7-900-333-44-55', 'sidorov@mail.ru'),
            ]
            client_ids = []
            for full_name, phone, email in clients_data:
                cursor.execute(
                    "INSERT INTO clients (full_name, phone, email) VALUES (%s, %s, %s)",
                    (full_name, phone, email)
                )
                client_ids.append(cursor.lastrowid)

            users_data = [
                ('seller', hash_password('seller'), 'SELLER', None),
                ('manager', hash_password('manager'), 'MANAGER', None),
                ('client1', hash_password('client1'), 'CLIENT', client_ids[0]),
                ('client2', hash_password('client2'), 'CLIENT', client_ids[1]),
                ('client3', hash_password('client3'), 'CLIENT', client_ids[2]),
            ]
            user_ids = []
            for username, pwd_hash, role, cid in users_data:
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, client_id) VALUES (%s, %s, %s, %s)",
                    (username, pwd_hash, role, cid)
                )
                user_ids.append(cursor.lastrowid)

            flowers_data = [
                ('Роза', 'Red Naomi', 'Красный', 150.00, 7),
                ('Роза', 'White Naomi', 'Белый', 140.00, 7),
                ('Тюльпан', 'Darwin Hybrid', 'Жёлтый', 80.00, 5),
                ('Хризантема', 'Spider', 'Белый', 100.00, 10),
                ('Гербера', 'Gerbera', 'Оранжевый', 90.00, 8),
            ]
            flower_ids = []
            for name, variety, color, price, shelf_life in flowers_data:
                cursor.execute(
                    "INSERT INTO flowers (name, variety, color, price, shelf_life_days) VALUES (%s, %s, %s, %s, %s)",
                    (name, variety, color, price, shelf_life)
                )
                flower_ids.append(cursor.lastrowid)

            bouquets_data = [
                ('Букет "Любовь"', 'День рождения', 500.00),
                ('Букет "Нежность"', '8 Марта', 600.00),
                ('Букет "Радость"', 'Юбилей', 700.00),
            ]
            bouquet_ids = []
            for name, occasion, base_price in bouquets_data:
                cursor.execute(
                    "INSERT INTO bouquets (name, occasion, base_price) VALUES (%s, %s, %s)",
                    (name, occasion, base_price)
                )
                bouquet_ids.append(cursor.lastrowid)

            bouquet_items_data = [
                (bouquet_ids[0], flower_ids[0], 5),
                (bouquet_ids[0], flower_ids[2], 3),
                (bouquet_ids[1], flower_ids[1], 7),
                (bouquet_ids[2], flower_ids[0], 3),
                (bouquet_ids[2], flower_ids[3], 5),
            ]
            for bid, fid, qty in bouquet_items_data:
                cursor.execute(
                    "INSERT INTO bouquet_items (bouquet_id, flower_id, qty) VALUES (%s, %s, %s)",
                    (bid, fid, qty)
                )

            packaging_data = [
                ('Крафтовая бумага', 50.00),
                ('Плёнка', 30.00),
                ('Коробка подарочная', 150.00),
            ]
            packaging_ids = []
            for name, price in packaging_data:
                cursor.execute(
                    "INSERT INTO packaging (name, price) VALUES (%s, %s)",
                    (name, price)
                )
                packaging_ids.append(cursor.lastrowid)

            accessories_data = [
                ('Лента атласная', 20.00),
                ('Открытка', 30.00),
                ('Ваза стеклянная', 200.00),
            ]
            accessory_ids = []
            for name, price in accessories_data:
                cursor.execute(
                    "INSERT INTO accessories (name, price) VALUES (%s, %s)",
                    (name, price)
                )
                accessory_ids.append(cursor.lastrowid)

            inventory_data = []
            for fid in flower_ids:
                inventory_data.append(('FLOWER', fid, 50))
            for bid in bouquet_ids:
                inventory_data.append(('BOUQUET', bid, 10))
            for pid in packaging_ids:
                inventory_data.append(('PACKAGING', pid, 100))
            for aid in accessory_ids:
                inventory_data.append(('ACCESSORY', aid, 50))

            for item_type, item_id, qty in inventory_data:
                cursor.execute(
                    "INSERT INTO inventory (item_type, item_id, qty) VALUES (%s, %s, %s)",
                    (item_type, item_id, qty)
                )

            suppliers_data = [
                ('ООО "Цветы оптом"', '+7-800-111-11-11', 'opt@flowers.ru'),
                ('ИП Петров', '+7-900-999-88-77', 'petrov@mail.ru'),
                ('Компания "Роза"', '+7-800-222-22-22', 'roza@mail.ru'),
            ]
            supplier_ids = []
            for name, phone, email in suppliers_data:
                cursor.execute(
                    "INSERT INTO suppliers (name, phone, email) VALUES (%s, %s, %s)",
                    (name, phone, email)
                )
                supplier_ids.append(cursor.lastrowid)

            supplier_prices_data = [
                (supplier_ids[0], 'FLOWER', flower_ids[0], 120.00),
                (supplier_ids[0], 'FLOWER', flower_ids[1], 110.00),
                (supplier_ids[0], 'FLOWER', flower_ids[2], 60.00),
                (supplier_ids[1], 'FLOWER', flower_ids[3], 80.00),
                (supplier_ids[1], 'PACKAGING', packaging_ids[0], 40.00),
                (supplier_ids[2], 'FLOWER', flower_ids[4], 70.00),
            ]
            for sid, itype, iid, price in supplier_prices_data:
                cursor.execute(
                    "INSERT INTO supplier_prices (supplier_id, item_type, item_id, price) VALUES (%s, %s, %s, %s)",
                    (sid, itype, iid, price)
                )

            orders_data = [
                (client_ids[0], user_ids[0], 'Принят', 0, 0),
                (client_ids[1], user_ids[0], 'В сборке', 5, 0),
                (client_ids[2], user_ids[0], 'Готов', 10, 0),
            ]
            order_ids = []
            for cid, uid, status, discount, total in orders_data:
                cursor.execute(
                    "INSERT INTO orders (client_id, created_by_user_id, status, discount_percent, total_sum) VALUES (%s, %s, %s, %s, %s)",
                    (cid, uid, status, discount, total)
                )
                order_ids.append(cursor.lastrowid)

            order_items_data = [
                (order_ids[0], 'FLOWER', flower_ids[0], 3, 150.00, 450.00),
                (order_ids[0], 'PACKAGING', packaging_ids[0], 1, 50.00, 50.00),
                (order_ids[1], 'BOUQUET', bouquet_ids[0], 1, 500.00, 500.00),
                (order_ids[2], 'FLOWER', flower_ids[1], 5, 140.00, 700.00),
                (order_ids[2], 'ACCESSORY', accessory_ids[0], 1, 20.00, 20.00),
            ]
            for oid, itype, iid, qty, price, sum_val in order_items_data:
                cursor.execute(
                    "INSERT INTO order_items (order_id, item_type, item_id, qty, price, sum) VALUES (%s, %s, %s, %s, %s, %s)",
                    (oid, itype, iid, qty, price, sum_val)
                )

            for oid in order_ids:
                cursor.execute(
                    "SELECT COALESCE(SUM(sum), 0) as total FROM order_items WHERE order_id = %s",
                    (oid,)
                )
                total = cursor.fetchone()['total']
                cursor.execute(
                    "UPDATE orders SET total_sum = %s WHERE order_id = %s",
                    (total, oid)
                )

            payments_data = [
                (order_ids[0], 'Наличные', 500.00),
                (order_ids[2], 'Карта', 720.00),
            ]
            for oid, method, amount in payments_data:
                cursor.execute(
                    "INSERT INTO payments (order_id, method, amount) VALUES (%s, %s, %s)",
                    (oid, method, amount)
                )

            writeoffs_data = [
                (flower_ids[0], 5, 'EXPIRED', datetime.now() - timedelta(days=30)),
                (flower_ids[1], 3, 'DAMAGED', datetime.now() - timedelta(days=20)),
                (flower_ids[2], 2, 'EXPIRED', datetime.now() - timedelta(days=10)),
                (flower_ids[0], 2, 'OTHER', datetime.now() - timedelta(days=5)),
            ]
            for fid, qty, reason, created_at in writeoffs_data:
                cursor.execute(
                    "INSERT INTO write_offs (item_type, item_id, qty, reason, created_at) VALUES ('FLOWER', %s, %s, %s, %s)",
                    (fid, qty, reason, created_at)
                )

            custom_requests_data = [
                (client_ids[0], datetime.now().date() + timedelta(days=7), 'Хочу яркий букет'),
                (client_ids[1], datetime.now().date() + timedelta(days=14), 'В пастельных тонах'),
                (client_ids[2], datetime.now().date() + timedelta(days=5), 'Большой букет для юбилея'),
            ]
            request_ids = []
            for cid, desired_date, wishes in custom_requests_data:
                cursor.execute(
                    "INSERT INTO custom_requests (client_id, desired_date, wishes, status) VALUES (%s, %s, %s, 'Новая')",
                    (cid, desired_date, wishes)
                )
                request_ids.append(cursor.lastrowid)

            request_items_data = [
                (request_ids[0], flower_ids[0], 7),
                (request_ids[0], flower_ids[2], 5),
                (request_ids[1], flower_ids[1], 10),
                (request_ids[2], flower_ids[0], 15),
                (request_ids[2], flower_ids[3], 10),
            ]
            for rid, fid, qty in request_items_data:
                cursor.execute(
                    "INSERT INTO custom_request_items (request_id, flower_id, qty) VALUES (%s, %s, %s)",
                    (rid, fid, qty)
                )

            conn.commit()
            print("Database seeded successfully!")

    finally:
        conn.close()

