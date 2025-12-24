
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import db
from auth import LoginWindow
from admin_ui import SellerWindow
from chief_ui import ManagerWindow
from patient_ui import ClientWindow


class FlowerShopApp:
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.current_window = None
    
    def run(self):
        try:
            # Инициализация БД
            print("Запуск бд")
            db.run_migrations()
            db.seed_data()
            print("бд готова!")
            login_window = LoginWindow(self.on_login_success)
            login_window.show()
            self.current_window = login_window
            
            sys.exit(self.app.exec())
        except Exception as e:
            print(f"Error starting application: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def on_login_success(self, user):
        if self.current_window:
            self.current_window.close()

        role = user['role']
        
        if role == 'SELLER':
            window = SellerWindow(user)
        elif role == 'MANAGER':
            window = ManagerWindow(user)
        elif role == 'CLIENT':
            window = ClientWindow(user)
        else:
            print(f"Unknown role: {role}")
            return
        
        window.show()
        self.current_window = window


if __name__ == '__main__':
    app = FlowerShopApp()
    app.run()
