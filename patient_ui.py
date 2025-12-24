"""
Интерфейс клиента (CLIENT)
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QTableWidget, QTableWidgetItem,
                             QPushButton, QComboBox, QLabel, QMessageBox,
                             QLineEdit, QTextEdit, QDateEdit, QSpinBox,
                             QDoubleSpinBox)
from PyQt6.QtCore import Qt, QDate
import db
from datetime import datetime, timedelta


def get_item_type_ru(item_type):
    """Переводит тип товара на русский"""
    types_map = {
        'FLOWER': 'Цветок',
        'BOUQUET': 'Букет',
        'PACKAGING': 'Упаковка',
        'ACCESSORY': 'Аксессуар'
    }
    return types_map.get(item_type, item_type)


class ClientWindow(QMainWindow):
    """Главное окно клиента"""
    
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.client_id = user.get('client_id')
        self.current_request_items = []
        self.init_ui()
        self.load_catalog()
        self.load_orders()
        self.load_requests()
    
    def init_ui(self):
        self.setWindowTitle(f'Клиент - {self.user["username"]}')
        self.setGeometry(100, 100, 1200, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Вкладки
        tabs = QTabWidget()
        tabs.addTab(self.create_catalog_tab(), 'Каталог')
        tabs.addTab(self.create_request_tab(), 'Заявка на букет')
        tabs.addTab(self.create_orders_tab(), 'Мои заказы')
        
        layout.addWidget(tabs)
    
    def create_catalog_tab(self):
        """Вкладка каталога с фильтрацией"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Фильтры
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel('Тип:'))
        self.catalog_type_filter = QComboBox()
        self.catalog_type_filter.addItems(['Все', 'Цветы', 'Букеты'])
        self.catalog_type_filter.currentTextChanged.connect(self.apply_catalog_filter)
        filter_layout.addWidget(self.catalog_type_filter)
        
        filter_layout.addWidget(QLabel('Цена от:'))
        self.catalog_price_from = QDoubleSpinBox()
        self.catalog_price_from.setMaximum(999999)
        filter_layout.addWidget(self.catalog_price_from)
        
        filter_layout.addWidget(QLabel('до:'))
        self.catalog_price_to = QDoubleSpinBox()
        self.catalog_price_to.setMaximum(999999)
        filter_layout.addWidget(self.catalog_price_to)
        
        btn_filter = QPushButton('Фильтровать')
        btn_filter.clicked.connect(self.apply_catalog_filter)
        filter_layout.addWidget(btn_filter)
        
        btn_show_all = QPushButton('Показать все')
        btn_show_all.clicked.connect(self.load_catalog)
        filter_layout.addWidget(btn_show_all)
        
        layout.addLayout(filter_layout)
        
        # Таблица каталога
        self.catalog_table = QTableWidget()
        self.catalog_table.setColumnCount(5)
        self.catalog_table.setHorizontalHeaderLabels(['Тип', 'ID', 'Название', 'Цена', 'Остаток'])
        layout.addWidget(self.catalog_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_request_tab(self):
        """Вкладка заявки на индивидуальный букет"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Доступные цветы
        layout.addWidget(QLabel('Доступные цветы:'))
        self.request_flowers_table = QTableWidget()
        self.request_flowers_table.setColumnCount(4)
        self.request_flowers_table.setHorizontalHeaderLabels(['ID', 'Название', 'Сорт', 'Цвет'])
        self.request_flowers_table.cellDoubleClicked.connect(self.add_to_request)
        layout.addWidget(self.request_flowers_table)
        
        btn_add = QPushButton('Добавить цветок')
        btn_add.clicked.connect(self.add_to_request)
        layout.addWidget(btn_add)
        
        # Выбранные цветы
        layout.addWidget(QLabel('Выбранные цветы:'))
        self.request_cart_table = QTableWidget()
        self.request_cart_table.setColumnCount(4)
        self.request_cart_table.setHorizontalHeaderLabels(['ID', 'Название', 'Сорт', 'Кол-во'])
        layout.addWidget(self.request_cart_table)
        
        btn_remove = QPushButton('Удалить из заявки')
        btn_remove.clicked.connect(self.remove_from_request)
        layout.addWidget(btn_remove)
        
        # Форма заявки
        form_layout = QVBoxLayout()
        
        wishes_layout = QHBoxLayout()
        wishes_layout.addWidget(QLabel('Пожелания к оформлению:'))
        self.request_wishes = QTextEdit()
        self.request_wishes.setMaximumHeight(100)
        wishes_layout.addWidget(self.request_wishes)
        form_layout.addLayout(wishes_layout)
        
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel('Желаемая дата получения:'))
        self.request_date = QDateEdit()
        self.request_date.setDate(QDate.currentDate().addDays(7))
        self.request_date.setCalendarPopup(True)
        date_layout.addWidget(self.request_date)
        form_layout.addLayout(date_layout)
        
        layout.addLayout(form_layout)
        
        btn_submit = QPushButton('Отправить заявку')
        btn_submit.clicked.connect(self.submit_request)
        layout.addWidget(btn_submit)
        
        widget.setLayout(layout)
        return widget
    
    def create_orders_tab(self):
        """Вкладка моих заказов"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Список заказов
        layout.addWidget(QLabel('Мои заказы:'))
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(['ID', 'Дата', 'Статус', 'Сумма', 'Оплачен'])
        self.orders_table.cellClicked.connect(self.load_order_details)
        layout.addWidget(self.orders_table)
        
        # Детали заказа
        layout.addWidget(QLabel('Детали заказа:'))
        self.order_details_table = QTableWidget()
        self.order_details_table.setColumnCount(5)
        self.order_details_table.setHorizontalHeaderLabels(['Тип', 'Название', 'Цена', 'Кол-во', 'Сумма'])
        layout.addWidget(self.order_details_table)
        
        # Оплата
        payment_layout = QHBoxLayout()
        payment_layout.addWidget(QLabel('Способ оплаты:'))
        self.payment_method = QComboBox()
        self.payment_method.addItems(['Наличные', 'Карта'])
        payment_layout.addWidget(self.payment_method)
        
        btn_pay = QPushButton('Оплатить заказ')
        btn_pay.clicked.connect(self.pay_order)
        payment_layout.addWidget(btn_pay)
        
        layout.addLayout(payment_layout)
        
        widget.setLayout(layout)
        return widget
    
    def load_catalog(self):
        """Загружает каталог без фильтров"""
        self.catalog_type_filter.setCurrentIndex(0)
        self.catalog_price_from.setValue(0)
        self.catalog_price_to.setValue(0)
        self.apply_catalog_filter()
    
    def apply_catalog_filter(self):
        """Применяет фильтры к каталогу"""
        type_filter = self.catalog_type_filter.currentText()
        price_from = self.catalog_price_from.value()
        price_to = self.catalog_price_to.value()
        
        items = []
        
        # Цветы
        if type_filter in ['Все', 'Цветы']:
            sql = """
                SELECT f.*, COALESCE(i.qty, 0) as stock 
                FROM flowers f 
                LEFT JOIN inventory i ON i.item_type='FLOWER' AND i.item_id=f.flower_id 
                WHERE f.is_active=1
            """
            params = []
            if price_from > 0:
                sql += " AND f.price >= %s"
                params.append(price_from)
            if price_to > 0:
                sql += " AND f.price <= %s"
                params.append(price_to)
            
            flowers = db.fetch_all(sql, tuple(params) if params else None)
            for f in flowers:
                items.append(('FLOWER', f['flower_id'], f['name'], f['price'], f['stock']))
        
        # Букеты
        if type_filter in ['Все', 'Букеты']:
            sql = """
                SELECT b.*, COALESCE(i.qty, 0) as stock 
                FROM bouquets b 
                LEFT JOIN inventory i ON i.item_type='BOUQUET' AND i.item_id=b.bouquet_id 
                WHERE b.is_active=1
            """
            params = []
            if price_from > 0:
                sql += " AND b.base_price >= %s"
                params.append(price_from)
            if price_to > 0:
                sql += " AND b.base_price <= %s"
                params.append(price_to)
            
            bouquets = db.fetch_all(sql, tuple(params) if params else None)
            for b in bouquets:
                items.append(('BOUQUET', b['bouquet_id'], b['name'], b['base_price'], b['stock']))
        
        # Заполняем таблицу
        self.catalog_table.setRowCount(len(items))
        for i, (item_type, item_id, name, price, stock) in enumerate(items):
            self.catalog_table.setItem(i, 0, QTableWidgetItem(get_item_type_ru(item_type)))
            self.catalog_table.setItem(i, 1, QTableWidgetItem(str(item_id)))
            self.catalog_table.setItem(i, 2, QTableWidgetItem(name))
            self.catalog_table.setItem(i, 3, QTableWidgetItem(f'{price:.2f}'))
            self.catalog_table.setItem(i, 4, QTableWidgetItem(str(stock)))
        
        self.catalog_table.resizeColumnsToContents()
    
    def load_request_flowers(self):
        """Загружает цветы для заявки"""
        flowers = db.fetch_all("""
            SELECT f.*, COALESCE(i.qty, 0) as stock 
            FROM flowers f 
            LEFT JOIN inventory i ON i.item_type='FLOWER' AND i.item_id=f.flower_id 
            WHERE f.is_active=1 AND COALESCE(i.qty, 0) > 0
            ORDER BY f.name, f.variety
        """)
        
        self.request_flowers_table.setRowCount(len(flowers))
        for i, flower in enumerate(flowers):
            self.request_flowers_table.setItem(i, 0, QTableWidgetItem(str(flower['flower_id'])))
            self.request_flowers_table.setItem(i, 1, QTableWidgetItem(flower['name']))
            self.request_flowers_table.setItem(i, 2, QTableWidgetItem(flower['variety']))
            self.request_flowers_table.setItem(i, 3, QTableWidgetItem(flower['color']))
        self.request_flowers_table.resizeColumnsToContents()
    
    def add_to_request(self):
        """Добавляет цветок в заявку"""
        row = self.request_flowers_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите цветок')
            return
        
        flower_id = int(self.request_flowers_table.item(row, 0).text())
        name = self.request_flowers_table.item(row, 1).text()
        variety = self.request_flowers_table.item(row, 2).text()
        
        # Проверяем, есть ли уже
        for item in self.current_request_items:
            if item['flower_id'] == flower_id:
                item['qty'] += 1
                self.update_request_cart()
                return
        
        # Добавляем новый
        self.current_request_items.append({
            'flower_id': flower_id,
            'name': name,
            'variety': variety,
            'qty': 1
        })
        self.update_request_cart()
    
    def remove_from_request(self):
        """Удаляет цветок из заявки"""
        row = self.request_cart_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите цветок')
            return
        
        self.current_request_items.pop(row)
        self.update_request_cart()
    
    def update_request_cart(self):
        """Обновляет таблицу выбранных цветов"""
        self.request_cart_table.setRowCount(len(self.current_request_items))
        for i, item in enumerate(self.current_request_items):
            self.request_cart_table.setItem(i, 0, QTableWidgetItem(str(item['flower_id'])))
            self.request_cart_table.setItem(i, 1, QTableWidgetItem(item['name']))
            self.request_cart_table.setItem(i, 2, QTableWidgetItem(item['variety']))
            qty_item = QTableWidgetItem(str(item['qty']))
            self.request_cart_table.setItem(i, 3, qty_item)
        self.request_cart_table.resizeColumnsToContents()
    
    def submit_request(self):
        """Отправляет заявку на индивидуальный букет"""
        if not self.current_request_items:
            QMessageBox.warning(self, 'Ошибка', 'Выберите хотя бы один цветок')
            return
        
        if not self.client_id:
            QMessageBox.warning(self, 'Ошибка', 'Клиент не найден')
            return
        
        desired_date = self.request_date.date().toPyDate()
        wishes = self.request_wishes.toPlainText().strip()
        
        try:
            # Создаём заявку
            request_id = db.execute(
                "INSERT INTO custom_requests (client_id, desired_date, wishes, status) VALUES (%s, %s, %s, 'Новая')",
                (self.client_id, desired_date, wishes if wishes else None)
            )
            
            # Добавляем позиции
            for item in self.current_request_items:
                db.execute(
                    "INSERT INTO custom_request_items (request_id, flower_id, qty) VALUES (%s, %s, %s)",
                    (request_id, item['flower_id'], item['qty'])
                )
            
            QMessageBox.information(self, 'Успех', f'Заявка #{request_id} отправлена')
            self.current_request_items.clear()
            self.update_request_cart()
            self.request_wishes.clear()
            self.load_requests()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при отправке заявки: {str(e)}')
    
    def load_orders(self):
        """Загружает заказы клиента"""
        if not self.client_id:
            return
        
        orders = db.fetch_all("""
            SELECT o.*, 
                   (SELECT COUNT(*) FROM payments p WHERE p.order_id = o.order_id) > 0 as is_paid
            FROM orders o 
            WHERE o.client_id = %s
            ORDER BY o.order_id DESC
        """, (self.client_id,))
        
        self.orders_table.setRowCount(len(orders))
        for i, order in enumerate(orders):
            self.orders_table.setItem(i, 0, QTableWidgetItem(str(order['order_id'])))
            self.orders_table.setItem(i, 1, QTableWidgetItem(str(order['created_at'])))
            self.orders_table.setItem(i, 2, QTableWidgetItem(order['status']))
            self.orders_table.setItem(i, 3, QTableWidgetItem(f"{order['total_sum']:.2f}"))
            self.orders_table.setItem(i, 4, QTableWidgetItem('Да' if order['is_paid'] else 'Нет'))
        self.orders_table.resizeColumnsToContents()
    
    def load_order_details(self, row, col):
        """Загружает детали выбранного заказа"""
        if row < 0:
            return
        
        order_id = int(self.orders_table.item(row, 0).text())
        
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
        
        self.order_details_table.setRowCount(len(items))
        for i, item in enumerate(items):
            self.order_details_table.setItem(i, 0, QTableWidgetItem(get_item_type_ru(item['item_type'])))
            self.order_details_table.setItem(i, 1, QTableWidgetItem(item['item_name']))
            self.order_details_table.setItem(i, 2, QTableWidgetItem(f"{item['price']:.2f}"))
            self.order_details_table.setItem(i, 3, QTableWidgetItem(str(item['qty'])))
            self.order_details_table.setItem(i, 4, QTableWidgetItem(f"{item['sum']:.2f}"))
        self.order_details_table.resizeColumnsToContents()
        
        # Сохраняем выбранный заказ для оплаты
        self.selected_order_id = order_id
    
    def pay_order(self):
        """Оплачивает заказ"""
        if not hasattr(self, 'selected_order_id'):
            QMessageBox.warning(self, 'Ошибка', 'Выберите заказ')
            return
        
        order_id = self.selected_order_id
        
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
            
            QMessageBox.information(self, 'Успех', 'Оплата принята')
            self.load_orders()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при оплате: {str(e)}')
    
    def load_requests(self):
        """Загружает заявки клиента (для информации)"""
        # Можно добавить таблицу заявок, но по ТЗ не обязательно
        # Загружаем цветы для заявки при открытии вкладки
        if hasattr(self, 'request_flowers_table'):
            self.load_request_flowers()

