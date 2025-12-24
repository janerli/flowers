from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
import db


class LoginWindow(QWidget):
    
    def __init__(self, on_success_callback):
        super().__init__()
        self.on_success = on_success_callback
        self.current_user = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('Авторизация - Цветочный магазин')
        self.setFixedSize(400, 280)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel('ВХОД В СИСТЕМУ')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        login_label = QLabel('Логин:')
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText('Введите логин')
        self.login_input.setMinimumHeight(30)
        layout.addWidget(login_label)
        layout.addWidget(self.login_input)
        
        password_label = QLabel('Пароль:')
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Введите пароль')
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(30)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        
        login_btn = QPushButton('Войти')
        login_btn.setDefault(True)
        login_btn.setMinimumHeight(35)
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)
        
        hint = QLabel('Тестовые логины: seller/seller, manager/manager, client1/client1')
        hint.setWordWrap(True)
        font = hint.font()
        font.setPointSize(8)
        hint.setFont(font)
        hint.setStyleSheet('color: gray;')
        layout.addWidget(hint)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        self.login_input.setFocus()
    
    def handle_login(self):
        username = self.login_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Введите логин и пароль')
            return
        
        password_hash = db.hash_password(password)
        user = db.fetch_one(
            "SELECT * FROM users WHERE username = %s AND password_hash = %s",
            (username, password_hash)
        )
        
        if not user:
            QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль')
            self.password_input.clear()
            return
        
        self.current_user = user
        self.on_success(user)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.handle_login()
        else:
            super().keyPressEvent(event)

