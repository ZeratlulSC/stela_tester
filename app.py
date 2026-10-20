
import sys
import serial.tools.list_ports
import json
import os


from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QGridLayout
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Проверка контроллера")
        self.resize(900, 600)

        self.tabs = QTabWidget()
        self.tab_settings = QWidget()
        self.tab_test = QWidget()

        self.tabs.addTab(self.tab_settings, "Настройки")
        self.tabs.addTab(self.tab_test, "Проверка устройства")

        self.setCentralWidget(self.tabs)

        self.create_settings_tab()
        self.load_settings()

        
    def create_settings_tab(self):
        layout = QVBoxLayout(self.tab_settings)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Заголовок страницы
        title = QLabel("Настройки контроллера")
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(title)

        # 1. USB контроллера
        usb_group = QGroupBox("1. USB контроллера")
        usb_layout = QGridLayout(usb_group)
        usb_layout.setContentsMargins(12, 18, 12, 12)
        usb_layout.setHorizontalSpacing(12)
        usb_layout.setVerticalSpacing(10)

        self.usb_controller = QComboBox()
        self.usb_controller.addItems(self.get_com_ports())

        self.usb_speed = QComboBox()
        self.usb_speed.addItems([
            "9600", "19200", "38400", "57600", "115200"
        ])
        self.usb_speed.setCurrentText("115200")

        usb_layout.addWidget(QLabel("COM-порт:"), 0, 0)
        usb_layout.addWidget(self.usb_controller, 0, 1)
        usb_layout.addWidget(QLabel("Скорость:"), 1, 0)
        usb_layout.addWidget(self.usb_speed, 1, 1)

        layout.addWidget(usb_group)

        # 2. Modbus RM-4
        modbus_group = QGroupBox("2. Modbus RM-4")
        modbus_layout = QGridLayout(modbus_group)
        modbus_layout.setContentsMargins(12, 18, 12, 12)
        modbus_layout.setHorizontalSpacing(12)
        modbus_layout.setVerticalSpacing(10)

        self.modbus_com = QComboBox()
        self.modbus_com.addItems(self.get_com_ports())

        self.modbus_address = QComboBox()
        self.modbus_address.addItems(
            [str(address) for address in range(1, 248)]
        )
        self.modbus_address.setCurrentText("1")

        self.modbus_speed = QComboBox()
        self.modbus_speed.addItems([
            "9600", "19200", "38400", "57600", "115200"
        ])
        self.modbus_speed.setCurrentText("9600")

        modbus_layout.addWidget(QLabel("COM-порт:"), 0, 0)
        modbus_layout.addWidget(self.modbus_com, 0, 1)
        modbus_layout.addWidget(QLabel("Адрес модуля:"), 1, 0)
        modbus_layout.addWidget(self.modbus_address, 1, 1)
        modbus_layout.addWidget(QLabel("Скорость:"), 2, 0)
        modbus_layout.addWidget(self.modbus_speed, 2, 1)

        layout.addWidget(modbus_group)

        # 3. Прошивка контроллера
        firmware_group = QGroupBox("3. Прошивка контроллера")
        firmware_layout = QVBoxLayout(firmware_group)
        firmware_layout.setContentsMargins(12, 18, 12, 12)

        firmware_layout.addWidget(
            QLabel("Команда для прошивки:")
        )

        self.firmware_command = QLineEdit()
        self.firmware_command.setPlaceholderText(
            "Введите команду для прошивки"
        )
        firmware_layout.addWidget(self.firmware_command)

        layout.addWidget(firmware_group)

        # Кнопка сохранения
        self.save_button = QPushButton("Сохранить")
        self.save_button.setMinimumHeight(36)
        self.save_button.clicked.connect(self.save_settings)

        layout.addWidget(self.save_button)
        layout.addStretch()



    def get_com_ports(self):
        ports = [
            port.device
            for port in serial.tools.list_ports.comports()
        ]

        return ports if ports else ["COM-порты не найдены"]

    def select_firmware(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите прошивку контроллера",
            "",
            "Файлы прошивки (*.hex *.bin *.elf);;Все файлы (*)",
        )

        if file_path:
            self.firmware_path.setText(file_path)

    
    def save_settings(self):
        settings = {
            "usb_controller": self.usb_controller.currentText(),
            "usb_speed": self.usb_speed.currentText(),
            "modbus_com": self.modbus_com.currentText(),
            "modbus_address": self.modbus_address.currentText(),
            "modbus_speed": self.modbus_speed.currentText(),
            "firmware_command": self.firmware_command.text(),
        }

        settings_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "settings.json",
        )

        with open(settings_path, "w", encoding="utf-8") as file:
            json.dump(settings, file, ensure_ascii=False, indent=4)

    def load_settings(self):
        settings_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "settings.json",
        )

        try:
            with open(settings_path, "r", encoding="utf-8") as file:
                settings = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return

        # USB контроллера
        self.set_combo_value(
            self.usb_controller,
            settings.get("usb_controller", ""),
        )
        self.usb_speed.setCurrentText(
            settings.get("usb_speed", "115200")
        )

        # Modbus RM-4
        self.set_combo_value(
            self.modbus_com,
            settings.get("modbus_com", ""),
        )
        self.modbus_address.setCurrentText(
            settings.get("modbus_address", "1")
        )
        self.modbus_speed.setCurrentText(
            settings.get("modbus_speed", "9600")
        )

        # Команда прошивки
        self.firmware_command.setText(
            settings.get("firmware_command", "")
        )

    def set_combo_value(self, combo, value):
        if not value:
            return

        if combo.findText(value) == -1:
            combo.addItem(value)

        combo.setCurrentText(value)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())
