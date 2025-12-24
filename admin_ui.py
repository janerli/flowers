from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QTableWidget, QTableWidgetItem,
                             QPushButton, QLineEdit, QComboBox, QLabel,
                             QMessageBox, QDialog, QFormLayout, QSpinBox,
                             QDoubleSpinBox, QTextEdit)
from PyQt6.QtCore import Qt
import db
from datetime import datetime


def get_item_type_ru(item_type):
    types_map = {
        'FLOWER': 'Цветок',
        'BOUQUET': 'Букет',
        'PACKAGING': 'Упаковка',
        'ACCESSORY': 'Аксессуар'
    }
    return types_map.get(item_type, item_type)


def get_item_type_en(item_type_ru):
    types_map = {
        'Цветок': 'FLOWER',
        'Букет': 'BOUQUET',
        'Упаковка': 'PACKAGING',
        'Аксессуар': 'ACCESSORY'
    }
    return types_map.get(item_type_ru, item_type_ru)


class SellerWindow(QMainWindow):
    
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.current_order_items = []
        self.init_ui()
        self.load_catalog()
        self.load_clients()
        self.load_orders()
        self.load_clients_for_order()
        self.load_available_items()
    
    def init_ui(self):
        self.setWindowTitle(f'Продавец-флорист - {self.user["username"]}')
        self.setGeometry(100, 100, 1200, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        tabs = QTabWidget()
        tabs.addTab(self.create_catalog_tab(), 'Каталог')
        tabs.addTab(self.create_clients_tab(), 'Клиенты')
        tabs.addTab(self.create_order_tab(), 'Оформление заказа')
        tabs.addTab(self.create_payment_tab(), 'Оплата')
        
        layout.addWidget(tabs)
    
    def create_catalog_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel('Название:'))
        self.filter_name = QLineEdit()
        filter_layout.addWidget(self.filter_name)
        
        filter_layout.addWidget(QLabel('Цвет:'))
        self.filter_color = QLineEdit()
        filter_layout.addWidget(self.filter_color)
        
        filter_layout.addWidget(QLabel('Цена от:'))
        self.filter_price_from = QDoubleSpinBox()
        self.filter_price_from.setMaximum(999999)
        filter_layout.addWidget(self.filter_price_from)
        
        filter_layout.addWidget(QLabel('до:'))
        self.filter_price_to = QDoubleSpinBox()
        self.filter_price_to.setMaximum(999999)
        filter_layout.addWidget(self.filter_price_to)
        
        filter_layout.addWidget(QLabel('Повод:'))
        self.filter_occasion = QLineEdit()
        filter_layout.addWidget(self.filter_occasion)
        
        btn_filter = QPushButton('Фильтровать')
        btn_filter.clicked.connect(self.apply_catalog_filter)
        filter_layout.addWidget(btn_filter)
        
        btn_show_all = QPushButton('Показать все')
        btn_show_all.clicked.connect(self.load_catalog)
        filter_layout.addWidget(btn_show_all)
        
        layout.addLayout(filter_layout)
        
        self.catalog_table = QTableWidget()
        self.catalog_table.setColumnCount(7)
        self.catalog_table.setHorizontalHeaderLabels([
            'Тип', 'ID', 'Название', 'Цвет/Повод', 'Цена', 'Остаток', 'Действие'
        ])
        layout.addWidget(self.catalog_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_clients_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel('ФИО:'))
        self.client_name = QLineEdit()
        form_layout.addWidget(self.client_name)
        
        form_layout.addWidget(QLabel('Телефон:'))
        self.client_phone = QLineEdit()
        form_layout.addWidget(self.client_phone)
        
        form_layout.addWidget(QLabel('Email:'))
        self.client_email = QLineEdit()
        form_layout.addWidget(self.client_email)
        
        btn_add = QPushButton('Добавить клиента')
        btn_add.clicked.connect(self.add_client)
        form_layout.addWidget(btn_add)
        
        layout.addLayout(form_layout)
        
        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(4)
        self.clients_table.setHorizontalHeaderLabels(['ID', 'ФИО', 'Телефон', 'Email'])
        layout.addWidget(self.clients_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_order_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        client_layout = QHBoxLayout()
        client_layout.addWidget(QLabel('Клиент:'))
        self.order_client = QComboBox()
        self.order_client.setEditable(True)
        self.order_client.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        client_layout.addWidget(self.order_client)
        
        btn_refresh_clients = QPushButton('Обновить список')
        btn_refresh_clients.clicked.connect(self.load_clients_for_order)
        client_layout.addWidget(btn_refresh_clients)
        
        layout.addLayout(client_layout)
        
        # Доступные товары
        layout.addWidget(QLabel('Доступные товары:'))
        self.available_items_table = QTableWidget()
        self.available_items_table.setColumnCount(5)
        self.available_items_table.setHorizontalHeaderLabels(['Тип', 'ID', 'Название', 'Цена', 'Остаток'])
        self.available_items_table.cellDoubleClicked.connect(self.add_to_cart)
        layout.addWidget(self.available_items_table)
        
        btn_add_to_cart = QPushButton('Добавить в заказ')
        btn_add_to_cart.clicked.connect(self.add_to_cart)
        layout.addWidget(btn_add_to_cart)
        
        # Корзина
        layout.addWidget(QLabel('Корзина:'))
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(['Тип', 'ID', 'Название', 'Цена', 'Кол-во', 'Сумма'])
        layout.addWidget(self.cart_table)
        
        # Управление корзиной
        cart_buttons = QHBoxLayout()
        btn_remove = QPushButton('Удалить из корзины')
        btn_remove.clicked.connect(self.remove_from_cart)
        cart_buttons.addWidget(btn_remove)
        
        btn_clear = QPushButton('Очистить корзину')
        btn_clear.clicked.connect(self.clear_cart)
        cart_buttons.addWidget(btn_clear)
        
        layout.addLayout(cart_buttons)
        
        # Скидка и итог
        discount_layout = QHBoxLayout()
        discount_layout.addWidget(QLabel('Скидка (%):'))
        self.order_discount = QDoubleSpinBox()
        self.order_discount.setMaximum(100)
        self.order_discount.valueChanged.connect(self.recalculate_order_total)
        discount_layout.addWidget(self.order_discount)
        
        self.order_total_label = QLabel('Итого: 0.00 ₽')
        font = self.order_total_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.order_total_label.setFont(font)
        discount_layout.addWidget(self.order_total_label)
        
        layout.addLayout(discount_layout)
        
        # Кнопки заказа
        order_buttons = QHBoxLayout()
        btn_create = QPushButton('Создать заказ')
        btn_create.clicked.connect(self.create_order)
        order_buttons.addWidget(btn_create)
        
        btn_modify = QPushButton('Изменить заказ')
        btn_modify.clicked.connect(self.modify_order_dialog)
        order_buttons.addWidget(btn_modify)
        
        btn_cancel = QPushButton('Отменить заказ')
        btn_cancel.clicked.connect(self.cancel_order_dialog)
        order_buttons.addWidget(btn_cancel)
        
        layout.addLayout(order_buttons)
        
        widget.setLayout(layout)
        return widget
    
    def create_payment_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Список заказов для оплаты
        layout.addWidget(QLabel('Заказы для оплаты:'))
        self.payment_orders_table = QTableWidget()
        self.payment_orders_table.setColumnCount(5)
        self.payment_orders_table.setHorizontalHeaderLabels(['ID', 'Клиент', 'Статус', 'Сумма', 'Оплачен'])
        layout.addWidget(self.payment_orders_table)
        
        # Форма оплаты
        payment_layout = QHBoxLayout()
        payment_layout.addWidget(QLabel('Способ оплаты:'))
        self.payment_method = QComboBox()
        self.payment_method.addItems(['Наличные', 'Карта'])
        payment_layout.addWidget(self.payment_method)
        
        btn_pay = QPushButton('Оплатить')
        btn_pay.clicked.connect(self.process_payment)
        payment_layout.addWidget(btn_pay)
        
        layout.addLayout(payment_layout)
        
        widget.setLayout(layout)
        return widget
    
    def load_catalog(self):
        self.filter_name.clear()
        self.filter_color.clear()
        self.filter_price_from.setValue(0)
        self.filter_price_to.setValue(0)
        self.filter_occasion.clear()
        self.apply_catalog_filter()
    
    def apply_catalog_filter(self):
        name = self.filter_name.text().strip()
        color = self.filter_color.text().strip()
        price_from = self.filter_price_from.value()
        price_to = self.filter_price_to.value()
        occasion = self.filter_occasion.text().strip()
        
        # Собираем данные
        items = []
        
        # Цветы
        sql = "SELECT f.*, COALESCE(i.qty, 0) as stock FROM flowers f LEFT JOIN inventory i ON i.item_type='FLOWER' AND i.item_id=f.flower_id WHERE f.is_active=1"
        params = []
        if name:
            sql += " AND f.name LIKE %s"
            params.append(f'%{name}%')
        if color:
            sql += " AND f.color LIKE %s"
            params.append(f'%{color}%')
        if price_from > 0:
            sql += " AND f.price >= %s"
            params.append(price_from)
        if price_to > 0:
            sql += " AND f.price <= %s"
            params.append(price_to)
        
        flowers = db.fetch_all(sql, tuple(params) if params else None)
        for f in flowers:
            items.append(('FLOWER', f['flower_id'], f['name'], f['color'], f['price'], f['stock']))
        
        # Букеты
        sql = "SELECT b.*, COALESCE(i.qty, 0) as stock FROM bouquets b LEFT JOIN inventory i ON i.item_type='BOUQUET' AND i.item_id=b.bouquet_id WHERE b.is_active=1"
        params = []
        if name:
            sql += " AND b.name LIKE %s"
            params.append(f'%{name}%')
        if occasion:
            sql += " AND b.occasion LIKE %s"
            params.append(f'%{occasion}%')
        if price_from > 0:
            sql += " AND b.base_price >= %s"
            params.append(price_from)
        if price_to > 0:
            sql += " AND b.base_price <= %s"
            params.append(price_to)
        
        bouquets = db.fetch_all(sql, tuple(params) if params else None)
        for b in bouquets:
            items.append(('BOUQUET', b['bouquet_id'], b['name'], b['occasion'] or '', b['base_price'], b['stock']))
        
        # Заполняем таблицу
        self.catalog_table.setRowCount(len(items))
        for i, (item_type, item_id, name, attr, price, stock) in enumerate(items):
            self.catalog_table.setItem(i, 0, QTableWidgetItem(get_item_type_ru(item_type)))
            self.catalog_table.setItem(i, 1, QTableWidgetItem(str(item_id)))
            self.catalog_table.setItem(i, 2, QTableWidgetItem(name))
            self.catalog_table.setItem(i, 3, QTableWidgetItem(attr))
            self.catalog_table.setItem(i, 4, QTableWidgetItem(f'{price:.2f}'))
            self.catalog_table.setItem(i, 5, QTableWidgetItem(str(stock)))
            btn = QPushButton('Добавить')
            btn.clicked.connect(lambda checked, t=item_type, id=item_id: self.add_to_cart_from_catalog(t, id))
            self.catalog_table.setCellWidget(i, 6, btn)
        
        self.catalog_table.resizeColumnsToContents()
    
    def add_to_cart_from_catalog(self, item_type, item_id):
        if item_type == 'FLOWER':
            item = db.fetch_one("SELECT * FROM flowers WHERE flower_id = %s", (item_id,))
            name = item['name']
            price = item['price']
        elif item_type == 'BOUQUET':
            item = db.fetch_one("SELECT * FROM bouquets WHERE bouquet_id = %s", (item_id,))
            name = item['name']
            price = item['base_price']
        else:
            return
        self.current_order_items.append({
            'item_type': item_type,
            'item_id': item_id,
            'name': name,
            'price': float(price),
            'qty': 1
        })
        self.update_cart_table()
        self.recalculate_order_total()
    
    def load_clients(self):
        clients = db.fetch_all("SELECT * FROM clients ORDER BY client_id")
        self.clients_table.setRowCount(len(clients))
        for i, client in enumerate(clients):
            self.clients_table.setItem(i, 0, QTableWidgetItem(str(client['client_id'])))
            self.clients_table.setItem(i, 1, QTableWidgetItem(client['full_name']))
            self.clients_table.setItem(i, 2, QTableWidgetItem(client['phone']))
            self.clients_table.setItem(i, 3, QTableWidgetItem(client['email'] or ''))
        self.clients_table.resizeColumnsToContents()
    
    def add_client(self):
        name = self.client_name.text().strip()
        phone = self.client_phone.text().strip()
        email = self.client_email.text().strip()
        
        if not name or not phone:
            QMessageBox.warning(self, 'Ошибка', 'Заполните ФИО и телефон')
            return
        
        try:
            # Создаём клиента
            client_id = db.execute(
                "INSERT INTO clients (full_name, phone, email) VALUES (%s, %s, %s)",
                (name, phone, email if email else None)
            )
            
            username = ''.join(filter(str.isdigit, phone))
            if not username:
                username = f'client{client_id}'
            
            existing_user = db.fetch_one("SELECT * FROM users WHERE username = %s", (username,))
            if existing_user:
                username = f'client{client_id}'
            
            password = phone.replace('-', '').replace('+', '').replace(' ', '')
            if len(password) < 4:
                password = f'client{client_id}'
            
            password_hash = db.hash_password(password)
            
            db.execute(
                "INSERT INTO users (username, password_hash, role, client_id) VALUES (%s, %s, %s, %s)",
                (username, password_hash, 'CLIENT', client_id)
            )
            
            QMessageBox.information(
                self, 
                'Успех', 
                f'Клиент добавлен!\nЛогин: {username}\nПароль: {password}\n\nСообщите эти данные клиенту для входа в систему.'
            )
            self.client_name.clear()
            self.client_phone.clear()
            self.client_email.clear()
            self.load_clients()
            self.load_clients_for_order()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при добавлении клиента: {str(e)}')
    
    def load_clients_for_order(self):
        clients = db.fetch_all("SELECT client_id, full_name, phone FROM clients ORDER BY full_name")
        self.order_client.clear()
        for client in clients:
            self.order_client.addItem(f"{client['full_name']} ({client['phone']})", client['client_id'])
    
    def load_available_items(self):
        """Загружает доступные товары для заказа"""
        items = []
        
        # Цветы
        flowers = db.fetch_all("""
            SELECT f.*, COALESCE(i.qty, 0) as stock 
            FROM flowers f 
            LEFT JOIN inventory i ON i.item_type='FLOWER' AND i.item_id=f.flower_id 
            WHERE f.is_active=1 AND COALESCE(i.qty, 0) > 0
        """)
        for f in flowers:
            items.append(('FLOWER', f['flower_id'], f['name'], f['price'], f['stock']))
        
        # Букеты
        bouquets = db.fetch_all("""
            SELECT b.*, COALESCE(i.qty, 0) as stock 
            FROM bouquets b 
            LEFT JOIN inventory i ON i.item_type='BOUQUET' AND i.item_id=b.bouquet_id 
            WHERE b.is_active=1 AND COALESCE(i.qty, 0) > 0
        """)
        for b in bouquets:
            items.append(('BOUQUET', b['bouquet_id'], b['name'], b['base_price'], b['stock']))
        
        # Упаковка
        packaging = db.fetch_all("""
            SELECT p.*, COALESCE(i.qty, 0) as stock 
            FROM packaging p 
            LEFT JOIN inventory i ON i.item_type='PACKAGING' AND i.item_id=p.packaging_id 
            WHERE COALESCE(i.qty, 0) > 0
        """)
        for p in packaging:
            items.append(('PACKAGING', p['packaging_id'], p['name'], p['price'], p['stock']))
        
        # Аксессуары
        accessories = db.fetch_all("""
            SELECT a.*, COALESCE(i.qty, 0) as stock 
            FROM accessories a 
            LEFT JOIN inventory i ON i.item_type='ACCESSORY' AND i.item_id=a.accessory_id 
            WHERE COALESCE(i.qty, 0) > 0
        """)
        for a in accessories:
            items.append(('ACCESSORY', a['accessory_id'], a['name'], a['price'], a['stock']))
        
        self.available_items_table.setRowCount(len(items))
        for i, (item_type, item_id, name, price, stock) in enumerate(items):
            # Сохраняем английское значение в userData для удобства
            type_item = QTableWidgetItem(get_item_type_ru(item_type))
            type_item.setData(Qt.ItemDataRole.UserRole, item_type)  # Сохраняем оригинальное значение
            self.available_items_table.setItem(i, 0, type_item)
            self.available_items_table.setItem(i, 1, QTableWidgetItem(str(item_id)))
            self.available_items_table.setItem(i, 2, QTableWidgetItem(name))
            self.available_items_table.setItem(i, 3, QTableWidgetItem(f'{price:.2f}'))
            self.available_items_table.setItem(i, 4, QTableWidgetItem(str(stock)))
        
        self.available_items_table.resizeColumnsToContents()
    
    def add_to_cart(self):
        """Добавляет выбранный товар в корзину"""
        row = self.available_items_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите товар')
            return
        
        # Получаем оригинальное английское значение из userData
        type_item = self.available_items_table.item(row, 0)
        item_type = type_item.data(Qt.ItemDataRole.UserRole) or get_item_type_en(type_item.text())
        item_id = int(self.available_items_table.item(row, 1).text())
        name = self.available_items_table.item(row, 2).text()
        price = float(self.available_items_table.item(row, 3).text())
        
        # Проверяем, есть ли уже в корзине
        for item in self.current_order_items:
            if item['item_type'] == item_type and item['item_id'] == item_id:
                item['qty'] += 1
                self.update_cart_table()
                self.recalculate_order_total()
                return
        
        # Добавляем новый
        self.current_order_items.append({
            'item_type': item_type,  # Сохраняем английское значение
            'item_id': item_id,
            'name': name,
            'price': price,
            'qty': 1
        })
        self.update_cart_table()
        self.recalculate_order_total()
    
    def remove_from_cart(self):
        """Удаляет выбранный товар из корзины"""
        row = self.cart_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите товар для удаления')
            return
        
        self.current_order_items.pop(row)
        self.update_cart_table()
        self.recalculate_order_total()
    
    def clear_cart(self):
        """Очищает корзину"""
        self.current_order_items.clear()
        self.update_cart_table()
        self.recalculate_order_total()
    
    def update_cart_table(self):
        """Обновляет таблицу корзины"""
        self.cart_table.setRowCount(len(self.current_order_items))
        for i, item in enumerate(self.current_order_items):
            self.cart_table.setItem(i, 0, QTableWidgetItem(get_item_type_ru(item['item_type'])))
            self.cart_table.setItem(i, 1, QTableWidgetItem(str(item['item_id'])))
            self.cart_table.setItem(i, 2, QTableWidgetItem(item['name']))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"{item['price']:.2f}"))
            
            # Количество с возможностью редактирования
            qty_item = QTableWidgetItem(str(item['qty']))
            self.cart_table.setItem(i, 4, qty_item)
            
            sum_val = item['price'] * item['qty']
            self.cart_table.setItem(i, 5, QTableWidgetItem(f"{sum_val:.2f}"))
        
        self.cart_table.resizeColumnsToContents()
    
    def recalculate_order_total(self):
        """Пересчитывает итоговую сумму заказа"""
        total = sum(item['price'] * item['qty'] for item in self.current_order_items)
        discount = self.order_discount.value()
        total_with_discount = total * (1 - discount / 100)
        self.order_total_label.setText(f'Итого: {total_with_discount:.2f} ₽')
    
    def create_order(self):
        """Создаёт новый заказ"""
        if not self.current_order_items:
            QMessageBox.warning(self, 'Ошибка', 'Корзина пуста')
            return
        
        client_idx = self.order_client.currentIndex()
        if client_idx < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите клиента')
            return
        
        client_id = self.order_client.currentData()
        
        try:
            # Создаём заказ
            discount = self.order_discount.value()
            total = sum(item['price'] * item['qty'] for item in self.current_order_items)
            total_with_discount = total * (1 - discount / 100)
            
            order_id = db.execute(
                """INSERT INTO orders (client_id, created_by_user_id, status, discount_percent, total_sum) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (client_id, self.user['user_id'], 'Новый', discount, total_with_discount)
            )
            
            # Добавляем позиции
            for item in self.current_order_items:
                sum_val = item['price'] * item['qty']
                db.execute(
                    """INSERT INTO order_items (order_id, item_type, item_id, qty, price, sum) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (order_id, item['item_type'], item['item_id'], item['qty'], item['price'], sum_val)
                )
                
                # Уменьшаем остатки
                db.execute(
                    """UPDATE inventory SET qty = qty - %s 
                       WHERE item_type = %s AND item_id = %s""",
                    (item['qty'], item['item_type'], item['item_id'])
                )
            
            QMessageBox.information(self, 'Успех', f'Заказ #{order_id} создан')
            self.current_order_items.clear()
            self.update_cart_table()
            self.recalculate_order_total()
            self.load_orders()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при создании заказа: {str(e)}')
    
    def modify_order_dialog(self):
        """Диалог изменения заказа"""
        orders = db.fetch_all("""
            SELECT o.*, c.full_name 
            FROM orders o 
            JOIN clients c ON o.client_id = c.client_id 
            WHERE o.status != 'Отменен' AND o.status != 'Выдан'
            ORDER BY o.order_id DESC
        """)
        
        if not orders:
            QMessageBox.information(self, 'Информация', 'Нет заказов для изменения')
            return
        
        # Простой выбор через диалог
        dialog = QDialog(self)
        dialog.setWindowTitle('Выбор заказа')
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel('Выберите заказ:'))
        order_combo = QComboBox()
        for order in orders:
            order_combo.addItem(f"Заказ #{order['order_id']} - {order['full_name']} ({order['status']})", order['order_id'])
        layout.addWidget(order_combo)
        
        btn_ok = QPushButton('Изменить')
        btn_cancel = QPushButton('Отмена')
        
        def on_ok():
            order_id = order_combo.currentData()
            dialog.accept()
            self.modify_order(order_id)
        
        btn_ok.clicked.connect(on_ok)
        btn_cancel.clicked.connect(dialog.reject)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pass  # Уже обработано в on_ok
    
    def modify_order(self, order_id):
        """Изменяет заказ"""
        # Загружаем текущие позиции
        items = db.fetch_all("""
            SELECT oi.*, 
                   CASE oi.item_type
                       WHEN 'FLOWER' THEN (SELECT name FROM flowers WHERE flower_id = oi.item_id)
                       WHEN 'BOUQUET' THEN (SELECT name FROM bouquets WHERE bouquet_id = oi.item_id)
                       WHEN 'PACKAGING' THEN (SELECT name FROM packaging WHERE packaging_id = oi.item_id)
                       WHEN 'ACCESSORY' THEN (SELECT name FROM accessories WHERE accessory_id = oi.item_id)
                   END as item_name
            FROM order_items oi 
            WHERE oi.order_id = %s
        """, (order_id,))
        
        # Простое редактирование через диалог
        dialog = QDialog(self)
        dialog.setWindowTitle(f'Изменение заказа #{order_id}')
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel('Позиции заказа (можно изменить количество):'))
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['Тип', 'Название', 'Цена', 'Кол-во', 'Сумма'])
        table.setRowCount(len(items))
        
        for i, item in enumerate(items):
            table.setItem(i, 0, QTableWidgetItem(get_item_type_ru(item['item_type'])))
            table.setItem(i, 1, QTableWidgetItem(item['item_name']))
            table.setItem(i, 2, QTableWidgetItem(f"{item['price']:.2f}"))
            qty_item = QTableWidgetItem(str(item['qty']))
            table.setItem(i, 3, qty_item)
            table.setItem(i, 4, QTableWidgetItem(f"{item['sum']:.2f}"))
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        layout.addWidget(QLabel('Скидка (%):'))
        discount_spin = QDoubleSpinBox()
        discount_spin.setMaximum(100)
        order = db.fetch_one("SELECT discount_percent FROM orders WHERE order_id = %s", (order_id,))
        if order:
            discount_spin.setValue(float(order['discount_percent']))
        layout.addWidget(discount_spin)
        
        btn_apply = QPushButton('Применить')
        btn_cancel = QPushButton('Отмена')
        
        def on_apply():
            # Обновляем количества
            for i in range(table.rowCount()):
                old_qty = items[i]['qty']
                new_qty = int(table.item(i, 3).text())
                
                if new_qty != old_qty:
                    # Обновляем позицию
                    new_sum = float(items[i]['price']) * new_qty
                    db.execute(
                        "UPDATE order_items SET qty = %s, sum = %s WHERE order_item_id = %s",
                        (new_qty, new_sum, items[i]['order_item_id'])
                    )
                    
                    # Корректируем остатки
                    diff = new_qty - old_qty
                    db.execute(
                        "UPDATE inventory SET qty = qty - %s WHERE item_type = %s AND item_id = %s",
                        (diff, items[i]['item_type'], items[i]['item_id'])
                    )
            
            # Пересчитываем сумму заказа
            total = sum(float(table.item(i, 4).text()) for i in range(table.rowCount()))
            discount = discount_spin.value()
            total_with_discount = total * (1 - discount / 100)
            
            db.execute(
                "UPDATE orders SET discount_percent = %s, total_sum = %s WHERE order_id = %s",
                (discount, total_with_discount, order_id)
            )
            
            QMessageBox.information(dialog, 'Успех', 'Заказ изменён')
            dialog.accept()
            self.load_orders()
        
        btn_apply.clicked.connect(on_apply)
        btn_cancel.clicked.connect(dialog.reject)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_apply)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def cancel_order_dialog(self):
        """Диалог отмены заказа"""
        orders = db.fetch_all("""
            SELECT o.*, c.full_name 
            FROM orders o 
            JOIN clients c ON o.client_id = c.client_id 
            WHERE o.status != 'Отменен' AND o.status != 'Выдан'
            ORDER BY o.order_id DESC
        """)
        
        if not orders:
            QMessageBox.information(self, 'Информация', 'Нет заказов для отмены')
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle('Отмена заказа')
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel('Выберите заказ для отмены:'))
        order_combo = QComboBox()
        for order in orders:
            order_combo.addItem(f"Заказ #{order['order_id']} - {order['full_name']}", order['order_id'])
        layout.addWidget(order_combo)
        
        btn_ok = QPushButton('Отменить заказ')
        btn_cancel = QPushButton('Отмена')
        
        def on_ok():
            order_id = order_combo.currentData()
            try:
                # Возвращаем товары на склад
                items = db.fetch_all("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
                for item in items:
                    db.execute(
                        "UPDATE inventory SET qty = qty + %s WHERE item_type = %s AND item_id = %s",
                        (item['qty'], item['item_type'], item['item_id'])
                    )
                
                # Отменяем заказ
                db.execute("UPDATE orders SET status = 'Отменен' WHERE order_id = %s", (order_id,))
                QMessageBox.information(dialog, 'Успех', 'Заказ отменён')
                dialog.accept()
                self.load_orders()
            except Exception as e:
                QMessageBox.critical(dialog, 'Ошибка', f'Ошибка: {str(e)}')
        
        btn_ok.clicked.connect(on_ok)
        btn_cancel.clicked.connect(dialog.reject)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def load_orders(self):
        """Загружает заказы для оплаты"""
        orders = db.fetch_all("""
            SELECT o.*, c.full_name,
                   (SELECT COUNT(*) FROM payments p WHERE p.order_id = o.order_id) > 0 as is_paid
            FROM orders o 
            JOIN clients c ON o.client_id = c.client_id 
            WHERE o.status IN ('Принят', 'В сборке', 'Готов')
            ORDER BY o.order_id DESC
        """)
        
        self.payment_orders_table.setRowCount(len(orders))
        for i, order in enumerate(orders):
            self.payment_orders_table.setItem(i, 0, QTableWidgetItem(str(order['order_id'])))
            self.payment_orders_table.setItem(i, 1, QTableWidgetItem(order['full_name']))
            self.payment_orders_table.setItem(i, 2, QTableWidgetItem(order['status']))
            self.payment_orders_table.setItem(i, 3, QTableWidgetItem(f"{order['total_sum']:.2f}"))
            self.payment_orders_table.setItem(i, 4, QTableWidgetItem('Да' if order['is_paid'] else 'Нет'))
        
        self.payment_orders_table.resizeColumnsToContents()
    
    def process_payment(self):
        """Обрабатывает оплату"""
        row = self.payment_orders_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите заказ')
            return
        
        order_id = int(self.payment_orders_table.item(row, 0).text())
        
        # Проверяем, не оплачен ли уже
        payment = db.fetch_one("SELECT * FROM payments WHERE order_id = %s", (order_id,))
        if payment:
            QMessageBox.warning(self, 'Ошибка', 'Заказ уже оплачен')
            return
        
        order = db.fetch_one("SELECT * FROM orders WHERE order_id = %s", (order_id,))
        if not order:
            QMessageBox.warning(self, 'Ошибка', 'Заказ не найден')
            return
        
        method = self.payment_method.currentText()
        
        try:
            db.execute(
                "INSERT INTO payments (order_id, method, amount) VALUES (%s, %s, %s)",
                (order_id, method, order['total_sum'])
            )
            
            # Обновляем статус заказа
            db.execute("UPDATE orders SET status = 'Выдан' WHERE order_id = %s", (order_id,))
            
            QMessageBox.information(self, 'Успех', 'Оплата принята')
            self.load_orders()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при оплате: {str(e)}')

