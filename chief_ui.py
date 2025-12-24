
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QTableWidget, QTableWidgetItem,
                             QPushButton, QComboBox, QLabel, QMessageBox,
                             QDialog, QFormLayout, QSpinBox, QDoubleSpinBox,
                             QLineEdit, QTextEdit)
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


def get_purchase_status_ru(status):
    status_map = {
        'NEW': 'Новая',
        'SENT': 'Отправлена',
        'RECEIVED': 'Получена',
        'CANCELLED': 'Отменена'
    }
    return status_map.get(status, status)


def get_purchase_status_en(status_ru):
    status_map = {
        'Новая': 'NEW',
        'Отправлена': 'SENT',
        'Получена': 'RECEIVED',
        'Отменена': 'CANCELLED'
    }
    return status_map.get(status_ru, status_ru)


def get_writeoff_reason_ru(reason):
    """Переводит причину списания на русский"""
    reason_map = {
        'EXPIRED': 'Истёк срок',
        'DAMAGED': 'Повреждён',
        'OTHER': 'Прочее'
    }
    return reason_map.get(reason, reason)


def get_writeoff_reason_en(reason_ru):
    """Переводит русскую причину списания обратно в английский"""
    reason_map = {
        'Истёк срок': 'EXPIRED',
        'Повреждён': 'DAMAGED',
        'Прочее': 'OTHER'
    }
    return reason_map.get(reason_ru, reason_ru)


def get_period_type_ru(period_type):
    """Переводит тип периода на русский"""
    period_map = {
        'MONTH': 'Месяц',
        'YEAR': 'Год'
    }
    return period_map.get(period_type, period_type)


def get_period_type_en(period_type_ru):
    """Переводит русский тип периода обратно в английский"""
    period_map = {
        'Месяц': 'MONTH',
        'Год': 'YEAR'
    }
    return period_map.get(period_type_ru, period_type_ru)


class ManagerWindow(QMainWindow):
    """Главное окно менеджера по закупкам"""
    
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.current_purchase_items = []
        self.init_ui()
        self.load_suppliers()
        self.load_purchases()
        self.load_receipts()
        self.load_writeoffs()
    
    def init_ui(self):
        self.setWindowTitle(f'Менеджер по закупкам - {self.user["username"]}')
        self.setGeometry(100, 100, 1200, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Вкладки
        tabs = QTabWidget()
        tabs.addTab(self.create_suppliers_tab(), 'Поставщики и цены')
        tabs.addTab(self.create_purchase_tab(), 'Создать закупку')
        tabs.addTab(self.create_receipt_tab(), 'Приём поставки')
        tabs.addTab(self.create_writeoff_tab(), 'Списания')
        tabs.addTab(self.create_reports_tab(), 'Отчёты')
        
        layout.addWidget(tabs)
    
    def create_suppliers_tab(self):
        """Вкладка поставщиков и цен"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Поставщики
        layout.addWidget(QLabel('Поставщики:'))
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(4)
        self.suppliers_table.setHorizontalHeaderLabels(['ID', 'Название', 'Телефон', 'Email'])
        layout.addWidget(self.suppliers_table)
        
        # Цены поставщиков
        layout.addWidget(QLabel('Цены поставщиков:'))
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel('Поставщик:'))
        self.price_supplier_filter = QComboBox()
        self.price_supplier_filter.addItem('Все', None)
        self.price_supplier_filter.currentIndexChanged.connect(self.load_supplier_prices)
        filter_layout.addWidget(self.price_supplier_filter)
        layout.addLayout(filter_layout)
        
        self.supplier_prices_table = QTableWidget()
        self.supplier_prices_table.setColumnCount(5)
        self.supplier_prices_table.setHorizontalHeaderLabels(['Поставщик', 'Тип', 'Товар', 'Цена', 'ID товара'])
        layout.addWidget(self.supplier_prices_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_purchase_tab(self):
        """Вкладка создания закупки"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Выбор поставщика
        supplier_layout = QHBoxLayout()
        supplier_layout.addWidget(QLabel('Поставщик:'))
        self.purchase_supplier = QComboBox()
        supplier_layout.addWidget(self.purchase_supplier)
        layout.addLayout(supplier_layout)
        
        # Доступные товары
        layout.addWidget(QLabel('Доступные товары:'))
        self.purchase_items_table = QTableWidget()
        self.purchase_items_table.setColumnCount(4)
        self.purchase_items_table.setHorizontalHeaderLabels(['Тип', 'ID', 'Название', 'Цена поставщика'])
        self.purchase_items_table.cellDoubleClicked.connect(self.add_to_purchase)
        layout.addWidget(self.purchase_items_table)
        
        btn_add = QPushButton('Добавить в закупку')
        btn_add.clicked.connect(self.add_to_purchase)
        layout.addWidget(btn_add)
        
        # Корзина закупки
        layout.addWidget(QLabel('Позиции закупки:'))
        self.purchase_cart_table = QTableWidget()
        self.purchase_cart_table.setColumnCount(6)
        self.purchase_cart_table.setHorizontalHeaderLabels(['Тип', 'ID', 'Название', 'Цена', 'Кол-во', 'Сумма'])
        layout.addWidget(self.purchase_cart_table)
        
        btn_remove = QPushButton('Удалить из закупки')
        btn_remove.clicked.connect(self.remove_from_purchase)
        layout.addWidget(btn_remove)
        
        btn_create = QPushButton('Создать закупку')
        btn_create.clicked.connect(self.create_purchase)
        layout.addWidget(btn_create)
        
        widget.setLayout(layout)
        return widget
    
    def create_receipt_tab(self):
        """Вкладка приёма поставки"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel('Закупки для приёма:'))
        self.receipt_purchases_table = QTableWidget()
        self.receipt_purchases_table.setColumnCount(4)
        self.receipt_purchases_table.setHorizontalHeaderLabels(['ID', 'Поставщик', 'Дата', 'Статус'])
        layout.addWidget(self.receipt_purchases_table)
        
        btn_receive = QPushButton('Принять поставку')
        btn_receive.clicked.connect(self.receive_purchase)
        layout.addWidget(btn_receive)
        
        widget.setLayout(layout)
        return widget
    
    def create_writeoff_tab(self):
        """Вкладка списаний"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Форма списания
        form_layout = QFormLayout()
        
        self.writeoff_flower = QComboBox()
        self.writeoff_flower.setEditable(True)
        form_layout.addRow('Цветок (сорт):', self.writeoff_flower)
        
        self.writeoff_qty = QSpinBox()
        self.writeoff_qty.setMinimum(1)
        self.writeoff_qty.setMaximum(9999)
        form_layout.addRow('Количество:', self.writeoff_qty)
        
        self.writeoff_reason = QComboBox()
        # Добавляем русские названия, но сохраняем английские значения
        self.writeoff_reason.addItem('Истёк срок', 'EXPIRED')
        self.writeoff_reason.addItem('Повреждён', 'DAMAGED')
        self.writeoff_reason.addItem('Прочее', 'OTHER')
        form_layout.addRow('Причина:', self.writeoff_reason)
        
        layout.addLayout(form_layout)
        
        btn_writeoff = QPushButton('Списать')
        btn_writeoff.clicked.connect(self.process_writeoff)
        layout.addWidget(btn_writeoff)
        
        # История списаний
        layout.addWidget(QLabel('История списаний:'))
        self.writeoffs_table = QTableWidget()
        self.writeoffs_table.setColumnCount(6)
        self.writeoffs_table.setHorizontalHeaderLabels(['ID', 'Цветок', 'Сорт', 'Кол-во', 'Причина', 'Дата'])
        layout.addWidget(self.writeoffs_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_reports_tab(self):
        """Вкладка отчётов с процедурой и функцией"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Процедура: средняя цена
        proc_group = QWidget()
        proc_layout = QVBoxLayout()
        proc_layout.addWidget(QLabel('Процедура: Средняя стоимость цветка по типу за период'))
        
        proc_form = QFormLayout()
        self.proc_flower_name = QLineEdit()
        self.proc_flower_name.setPlaceholderText('Например: Роза')
        proc_form.addRow('Тип цветка:', self.proc_flower_name)
        
        self.proc_period_type = QComboBox()
        # Добавляем русские названия, но сохраняем английские значения
        self.proc_period_type.addItem('Месяц', 'MONTH')
        self.proc_period_type.addItem('Год', 'YEAR')
        self.proc_period_type.currentTextChanged.connect(self.update_period_fields)
        proc_form.addRow('Период:', self.proc_period_type)
        
        self.proc_year = QSpinBox()
        self.proc_year.setMinimum(2020)
        self.proc_year.setMaximum(2100)
        self.proc_year.setValue(datetime.now().year)
        proc_form.addRow('Год:', self.proc_year)
        
        self.proc_month = QSpinBox()
        self.proc_month.setMinimum(1)
        self.proc_month.setMaximum(12)
        self.proc_month.setValue(datetime.now().month)
        proc_form.addRow('Месяц:', self.proc_month)
        
        proc_layout.addLayout(proc_form)
        
        btn_proc = QPushButton('Посчитать среднюю цену')
        btn_proc.clicked.connect(self.calculate_avg_price)
        proc_layout.addWidget(btn_proc)
        
        self.proc_result = QLabel('Результат: -')
        proc_layout.addWidget(self.proc_result)
        
        proc_group.setLayout(proc_layout)
        layout.addWidget(proc_group)
        
        # Функция: процент списаний
        func_group = QWidget()
        func_layout = QVBoxLayout()
        func_layout.addWidget(QLabel('Функция: Процент списаний сорта за последние 3 месяца'))
        
        func_form = QFormLayout()
        self.func_variety = QLineEdit()
        self.func_variety.setPlaceholderText('Например: Red Naomi')
        func_form.addRow('Сорт:', self.func_variety)
        
        func_layout.addLayout(func_form)
        
        btn_func = QPushButton('Посчитать процент списаний')
        btn_func.clicked.connect(self.calculate_writeoff_percent)
        func_layout.addWidget(btn_func)
        
        self.func_result = QLabel('Результат: -')
        func_layout.addWidget(self.func_result)
        
        func_group.setLayout(func_layout)
        layout.addWidget(func_group)
        
        widget.setLayout(layout)
        return widget
    
    def update_period_fields(self):
        """Показывает/скрывает поле месяца в зависимости от типа периода"""
        # Простая реализация - поле всегда видно, но используется только для MONTH
        pass
    
    def load_suppliers(self):
        """Загружает поставщиков"""
        suppliers = db.fetch_all("SELECT * FROM suppliers ORDER BY supplier_id")
        self.suppliers_table.setRowCount(len(suppliers))
        for i, supplier in enumerate(suppliers):
            self.suppliers_table.setItem(i, 0, QTableWidgetItem(str(supplier['supplier_id'])))
            self.suppliers_table.setItem(i, 1, QTableWidgetItem(supplier['name']))
            self.suppliers_table.setItem(i, 2, QTableWidgetItem(supplier['phone'] or ''))
            self.suppliers_table.setItem(i, 3, QTableWidgetItem(supplier['email'] or ''))
        self.suppliers_table.resizeColumnsToContents()
        
        # Обновляем фильтр
        self.price_supplier_filter.clear()
        self.price_supplier_filter.addItem('Все', None)
        for supplier in suppliers:
            self.price_supplier_filter.addItem(supplier['name'], supplier['supplier_id'])
        
        # Обновляем ComboBox для закупок
        self.purchase_supplier.clear()
        for supplier in suppliers:
            self.purchase_supplier.addItem(supplier['name'], supplier['supplier_id'])
        
        self.load_supplier_prices()
    
    def load_supplier_prices(self):
        """Загружает цены поставщиков"""
        supplier_id = self.price_supplier_filter.currentData()
        
        if supplier_id:
            sql = """
                SELECT sp.*, s.name as supplier_name,
                       CASE sp.item_type
                           WHEN 'FLOWER' THEN (SELECT name FROM flowers WHERE flower_id = sp.item_id)
                           WHEN 'PACKAGING' THEN (SELECT name FROM packaging WHERE packaging_id = sp.item_id)
                           WHEN 'ACCESSORY' THEN (SELECT name FROM accessories WHERE accessory_id = sp.item_id)
                       END as item_name
                FROM supplier_prices sp
                JOIN suppliers s ON sp.supplier_id = s.supplier_id
                WHERE sp.supplier_id = %s
            """
            prices = db.fetch_all(sql, (supplier_id,))
        else:
            sql = """
                SELECT sp.*, s.name as supplier_name,
                       CASE sp.item_type
                           WHEN 'FLOWER' THEN (SELECT name FROM flowers WHERE flower_id = sp.item_id)
                           WHEN 'PACKAGING' THEN (SELECT name FROM packaging WHERE packaging_id = sp.item_id)
                           WHEN 'ACCESSORY' THEN (SELECT name FROM accessories WHERE accessory_id = sp.item_id)
                       END as item_name
                FROM supplier_prices sp
                JOIN suppliers s ON sp.supplier_id = s.supplier_id
            """
            prices = db.fetch_all(sql)
        
        self.supplier_prices_table.setRowCount(len(prices))
        for i, price in enumerate(prices):
            self.supplier_prices_table.setItem(i, 0, QTableWidgetItem(price['supplier_name']))
            self.supplier_prices_table.setItem(i, 1, QTableWidgetItem(get_item_type_ru(price['item_type'])))
            self.supplier_prices_table.setItem(i, 2, QTableWidgetItem(price['item_name']))
            self.supplier_prices_table.setItem(i, 3, QTableWidgetItem(f"{price['price']:.2f}"))
            self.supplier_prices_table.setItem(i, 4, QTableWidgetItem(str(price['item_id'])))
        self.supplier_prices_table.resizeColumnsToContents()
        
        # Загружаем товары для закупки
        self.load_purchase_items()
    
    def load_purchase_items(self):
        """Загружает товары для закупки (с ценами поставщиков)"""
        supplier_id = self.purchase_supplier.currentData()
        if not supplier_id:
            self.purchase_items_table.setRowCount(0)
            return
        
        items = []
        
        # Цветы с ценами поставщика
        sql = """
            SELECT f.*, COALESCE(sp.price, f.price * 0.8) as supplier_price
            FROM flowers f
            LEFT JOIN supplier_prices sp ON sp.supplier_id = %s AND sp.item_type = 'FLOWER' AND sp.item_id = f.flower_id
            WHERE f.is_active = 1
        """
        flowers = db.fetch_all(sql, (supplier_id,))
        for f in flowers:
            items.append(('FLOWER', f['flower_id'], f['name'], f['supplier_price']))
        
        # Упаковка
        sql = """
            SELECT p.*, COALESCE(sp.price, p.price * 0.8) as supplier_price
            FROM packaging p
            LEFT JOIN supplier_prices sp ON sp.supplier_id = %s AND sp.item_type = 'PACKAGING' AND sp.item_id = p.packaging_id
        """
        packaging = db.fetch_all(sql, (supplier_id,))
        for p in packaging:
            items.append(('PACKAGING', p['packaging_id'], p['name'], p['supplier_price']))
        
        # Аксессуары
        sql = """
            SELECT a.*, COALESCE(sp.price, a.price * 0.8) as supplier_price
            FROM accessories a
            LEFT JOIN supplier_prices sp ON sp.supplier_id = %s AND sp.item_type = 'ACCESSORY' AND sp.item_id = a.accessory_id
        """
        accessories = db.fetch_all(sql, (supplier_id,))
        for a in accessories:
            items.append(('ACCESSORY', a['accessory_id'], a['name'], a['supplier_price']))
        
        self.purchase_items_table.setRowCount(len(items))
        for i, (item_type, item_id, name, price) in enumerate(items):
            # Сохраняем английское значение в userData
            type_item = QTableWidgetItem(get_item_type_ru(item_type))
            type_item.setData(Qt.ItemDataRole.UserRole, item_type)
            self.purchase_items_table.setItem(i, 0, type_item)
            self.purchase_items_table.setItem(i, 1, QTableWidgetItem(str(item_id)))
            self.purchase_items_table.setItem(i, 2, QTableWidgetItem(name))
            self.purchase_items_table.setItem(i, 3, QTableWidgetItem(f'{price:.2f}'))
        self.purchase_items_table.resizeColumnsToContents()
    
    def add_to_purchase(self):
        """Добавляет товар в закупку"""
        row = self.purchase_items_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите товар')
            return
        
        # Получаем оригинальное английское значение из userData
        type_item = self.purchase_items_table.item(row, 0)
        item_type = type_item.data(Qt.ItemDataRole.UserRole) or get_item_type_en(type_item.text())
        item_id = int(self.purchase_items_table.item(row, 1).text())
        name = self.purchase_items_table.item(row, 2).text()
        price = float(self.purchase_items_table.item(row, 3).text())
        
        # Проверяем, есть ли уже
        for item in self.current_purchase_items:
            if item['item_type'] == item_type and item['item_id'] == item_id:
                item['qty'] += 1
                self.update_purchase_cart()
                return
        
        # Добавляем новый
        self.current_purchase_items.append({
            'item_type': item_type,
            'item_id': item_id,
            'name': name,
            'price': price,
            'qty': 1
        })
        self.update_purchase_cart()
    
    def remove_from_purchase(self):
        """Удаляет товар из закупки"""
        row = self.purchase_cart_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите товар')
            return
        
        self.current_purchase_items.pop(row)
        self.update_purchase_cart()
    
    def update_purchase_cart(self):
        """Обновляет таблицу корзины закупки"""
        self.purchase_cart_table.setRowCount(len(self.current_purchase_items))
        for i, item in enumerate(self.current_purchase_items):
            self.purchase_cart_table.setItem(i, 0, QTableWidgetItem(get_item_type_ru(item['item_type'])))
            self.purchase_cart_table.setItem(i, 1, QTableWidgetItem(str(item['item_id'])))
            self.purchase_cart_table.setItem(i, 2, QTableWidgetItem(item['name']))
            self.purchase_cart_table.setItem(i, 3, QTableWidgetItem(f"{item['price']:.2f}"))
            self.purchase_cart_table.setItem(i, 4, QTableWidgetItem(str(item['qty'])))
            self.purchase_cart_table.setItem(i, 5, QTableWidgetItem(f"{item['price'] * item['qty']:.2f}"))
        self.purchase_cart_table.resizeColumnsToContents()
    
    def create_purchase(self):
        """Создаёт закупку"""
        if not self.current_purchase_items:
            QMessageBox.warning(self, 'Ошибка', 'Добавьте товары в закупку')
            return
        
        supplier_id = self.purchase_supplier.currentData()
        if not supplier_id:
            QMessageBox.warning(self, 'Ошибка', 'Выберите поставщика')
            return
        
        try:
            # Создаём закупку
            purchase_id = db.execute(
                "INSERT INTO purchase_orders (supplier_id, status) VALUES (%s, %s)",
                (supplier_id, 'NEW')
            )
            
            # Добавляем позиции
            for item in self.current_purchase_items:
                db.execute(
                    "INSERT INTO purchase_items (purchase_id, item_type, item_id, qty, price) VALUES (%s, %s, %s, %s, %s)",
                    (purchase_id, item['item_type'], item['item_id'], item['qty'], item['price'])
                )
            
            QMessageBox.information(self, 'Успех', f'Закупка #{purchase_id} создана')
            self.current_purchase_items.clear()
            self.update_purchase_cart()
            self.load_purchases()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при создании закупки: {str(e)}')
    
    def load_purchases(self):
        """Загружает закупки"""
        purchases = db.fetch_all("""
            SELECT po.*, s.name as supplier_name
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.supplier_id
            ORDER BY po.purchase_id DESC
        """)
        
        self.receipt_purchases_table.setRowCount(len(purchases))
        for i, purchase in enumerate(purchases):
            self.receipt_purchases_table.setItem(i, 0, QTableWidgetItem(str(purchase['purchase_id'])))
            self.receipt_purchases_table.setItem(i, 1, QTableWidgetItem(purchase['supplier_name']))
            self.receipt_purchases_table.setItem(i, 2, QTableWidgetItem(str(purchase['created_at'])))
            self.receipt_purchases_table.setItem(i, 3, QTableWidgetItem(get_purchase_status_ru(purchase['status'])))
        self.receipt_purchases_table.resizeColumnsToContents()
    
    def receive_purchase(self):
        """Принимает поставку"""
        row = self.receipt_purchases_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Ошибка', 'Выберите закупку')
            return
        
        purchase_id = int(self.receipt_purchases_table.item(row, 0).text())
        
        purchase = db.fetch_one("SELECT * FROM purchase_orders WHERE purchase_id = %s", (purchase_id,))
        if not purchase:
            QMessageBox.warning(self, 'Ошибка', 'Закупка не найдена')
            return
        
        if purchase['status'] == 'RECEIVED':
            QMessageBox.warning(self, 'Ошибка', 'Поставка уже принята')
            return
        
        try:
            # Создаём приход
            receipt_id = db.execute(
                "INSERT INTO receipts (purchase_id, received_at) VALUES (%s, NOW())",
                (purchase_id,)
            )
            
            # Получаем позиции закупки
            items = db.fetch_all("SELECT * FROM purchase_items WHERE purchase_id = %s", (purchase_id,))
            
            # Создаём позиции прихода и увеличиваем остатки
            for item in items:
                db.execute(
                    "INSERT INTO receipt_items (receipt_id, item_type, item_id, qty, buy_price) VALUES (%s, %s, %s, %s, %s)",
                    (receipt_id, item['item_type'], item['item_id'], item['qty'], item['price'])
                )
                
                # Увеличиваем остатки
                # Проверяем, есть ли запись в inventory
                inv = db.fetch_one(
                    "SELECT * FROM inventory WHERE item_type = %s AND item_id = %s",
                    (item['item_type'], item['item_id'])
                )
                if inv:
                    db.execute(
                        "UPDATE inventory SET qty = qty + %s WHERE item_type = %s AND item_id = %s",
                        (item['qty'], item['item_type'], item['item_id'])
                    )
                else:
                    db.execute(
                        "INSERT INTO inventory (item_type, item_id, qty) VALUES (%s, %s, %s)",
                        (item['item_type'], item['item_id'], item['qty'])
                    )
            db.execute(
                "UPDATE purchase_orders SET status = 'RECEIVED' WHERE purchase_id = %s",
                (purchase_id,)
            )
            
            QMessageBox.information(self, 'Успех', f'Поставка #{receipt_id} принята, остатки обновлены')
            self.load_receipts()
            self.load_purchases()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при приёме поставки: {str(e)}')
    
    def load_receipts(self):
        """Загружает приходы (для информации)"""
        pass
    
    def load_writeoffs(self):
        writeoffs = db.fetch_all("""
            SELECT wo.*, f.name as flower_name, f.variety
            FROM write_offs wo
            JOIN flowers f ON wo.item_id = f.flower_id
            ORDER BY wo.created_at DESC
        """)
        
        self.writeoffs_table.setRowCount(len(writeoffs))
        for i, wo in enumerate(writeoffs):
            self.writeoffs_table.setItem(i, 0, QTableWidgetItem(str(wo['writeoff_id'])))
            self.writeoffs_table.setItem(i, 1, QTableWidgetItem(wo['flower_name']))
            self.writeoffs_table.setItem(i, 2, QTableWidgetItem(wo['variety']))
            self.writeoffs_table.setItem(i, 3, QTableWidgetItem(str(wo['qty'])))
            self.writeoffs_table.setItem(i, 4, QTableWidgetItem(get_writeoff_reason_ru(wo['reason'])))
            self.writeoffs_table.setItem(i, 5, QTableWidgetItem(str(wo['created_at'])))
        self.writeoffs_table.resizeColumnsToContents()
        
        # Загружаем цветы для списания
        flowers = db.fetch_all("SELECT flower_id, name, variety FROM flowers WHERE is_active = 1 ORDER BY name, variety")
        self.writeoff_flower.clear()
        for flower in flowers:
            self.writeoff_flower.addItem(f"{flower['name']} - {flower['variety']}", flower['flower_id'])
    
    def process_writeoff(self):
        flower_id = self.writeoff_flower.currentData()
        if not flower_id:
            text = self.writeoff_flower.currentText().strip()
            if not text:
                QMessageBox.warning(self, 'Ошибка', 'Выберите или введите цветок')
                return

            flower = db.fetch_one("SELECT flower_id FROM flowers WHERE name LIKE %s LIMIT 1", (f'%{text}%',))
            if not flower:
                QMessageBox.warning(self, 'Ошибка', 'Цветок не найден')
                return
            flower_id = flower['flower_id']
        
        qty = self.writeoff_qty.value()
        reason = self.writeoff_reason.currentData()

        inv = db.fetch_one(
            "SELECT qty FROM inventory WHERE item_type = 'FLOWER' AND item_id = %s",
            (flower_id,)
        )
        if not inv or inv['qty'] < qty:
            QMessageBox.warning(self, 'Ошибка', 'Недостаточно товара на складе')
            return
        
        try:
            db.execute(
                "INSERT INTO write_offs (item_type, item_id, qty, reason, created_at) VALUES ('FLOWER', %s, %s, %s, NOW())",
                (flower_id, qty, reason)
            )

            db.execute(
                "UPDATE inventory SET qty = qty - %s WHERE item_type = 'FLOWER' AND item_id = %s",
                (qty, flower_id)
            )
            
            QMessageBox.information(self, 'Успех', 'Товар списан')
            self.writeoff_qty.setValue(1)
            self.load_writeoffs()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при списании: {str(e)}')
    
    def calculate_avg_price(self):
        flower_name = self.proc_flower_name.text().strip()
        if not flower_name:
            QMessageBox.warning(self, 'Ошибка', 'Введите тип цветка')
            return
        
        period_type = self.proc_period_type.currentData()  # Получаем английское значение
        year = self.proc_year.value()
        month = self.proc_month.value()
        
        try:
            conn = db.get_connection()
            with conn.cursor() as cursor:
                if period_type == 'MONTH':
                    cursor.callproc('get_avg_flower_price', (flower_name, period_type, year, month))
                else:
                    cursor.callproc('get_avg_flower_price', (flower_name, period_type, year, 0))
                
                result = cursor.fetchone()
                if result:
                    avg_price = result['avg_price']
                    self.proc_result.setText(f'Результат: {avg_price:.2f} ₽')
                else:
                    self.proc_result.setText('Результат: Данные не найдены')
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при вызове процедуры: {str(e)}')
            self.proc_result.setText('Результат: Ошибка')
    
    def calculate_writeoff_percent(self):
        """Вызывает функцию расчёта процента списаний"""
        variety = self.func_variety.text().strip()
        if not variety:
            QMessageBox.warning(self, 'Ошибка', 'Введите сорт')
            return
        
        try:
            result = db.fetch_one("SELECT get_writeoff_percent(%s) as percent", (variety,))
            if result:
                percent = result['percent']
                self.func_result.setText(f'Результат: {percent:.2f}%')
            else:
                self.func_result.setText('Результат: Данные не найдены')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при вызове функции: {str(e)}')
            self.func_result.setText('Результат: Ошибка')

