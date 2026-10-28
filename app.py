import sys
import serial.tools.list_ports
import serial
import json
import os

from PyQt6.QtCore import Qt
from PyQt6.QtCore import QTimer
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
    QGridLayout,
    QMessageBox,
    QPlainTextEdit,
    QDialog
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.usb_serial = None
        self.rm4_serial = None

        self.setWindowTitle("Проверка контроллера")
        self.resize(900, 600)

        self.tabs = QTabWidget()
        self.tab_settings = QWidget()
        self.tab_test = QWidget()

        self.tabs.addTab(self.tab_settings, "Настройки")
        self.tabs.addTab(self.tab_test, "Проверка устройства")

        self.setCentralWidget(self.tabs)

        self.create_settings_tab()
        self.create_test_tab()
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


    def create_test_tab(self):
        layout = QVBoxLayout(self.tab_test)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Заголовок
        title = QLabel("Проверка устройства")
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold;"
        )
        layout.addWidget(title)

        # Подключение оборудования и логи
        connection_layout = QGridLayout()

        self.usb_connect_button = QPushButton("Подключить USB")
        self.usb_connection_status = QLabel("Не подключено")
        self.usb_connection_status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.usb_connection_status.setStyleSheet(
            "color: #777777; font-weight: bold;"
        )

        self.rm4_connect_button = QPushButton("Подключить RM-4")
        self.rm4_connection_status = QLabel("Не подключено")
        self.rm4_connection_status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.rm4_connection_status.setStyleSheet(
            "color: #777777; font-weight: bold;"
        )

        self.usb_connect_button.clicked.connect(self.connect_usb)
        self.rm4_connect_button.clicked.connect(self.connect_rm4)

        # Окно лога USB
        self.usb_log = QPlainTextEdit()
        self.usb_log.setReadOnly(True)
        self.usb_log.setPlaceholderText(
            "Здесь будут отображаться данные USB..."
        )
        self.usb_log.setMaximumHeight(350)

        # Окно лога RM-4
        self.rm4_log = QPlainTextEdit()
        self.rm4_log.setReadOnly(True)
        self.rm4_log.setPlaceholderText(
            "Здесь будут отображаться данные RM-4..."
        )
        self.rm4_log.setMaximumHeight(110)

        connection_layout.addWidget(
            self.usb_connect_button, 0, 0
        )
        connection_layout.addWidget(
            self.usb_connection_status, 0, 1
        )
        connection_layout.addWidget(self.usb_log, 1, 0, 1, 2)

        connection_layout.addWidget(
            self.rm4_connect_button, 2, 0
        )
        connection_layout.addWidget(
            self.rm4_connection_status, 2, 1
        )
        connection_layout.addWidget(self.rm4_log, 3, 0, 1, 2)

        layout.addLayout(connection_layout)

        # Периодическое чтение входящих данных
        self.serial_timer = QTimer(self)
        self.serial_timer.timeout.connect(self.read_serial_logs)
        self.serial_timer.start(100)



        # ICCID
        iccid_layout = QHBoxLayout()

        iccid_layout.addWidget(QLabel("ICCID:"))

        self.iccid_input = QLineEdit()
        self.iccid_input.setPlaceholderText(
            "Введите ICCID SIM-карты"
        )
        iccid_layout.addWidget(self.iccid_input)

        layout.addLayout(iccid_layout)

        # Вывод алгоритма проверки
        self.algorithm_button = QPushButton(
            "Вывести алгоритм проверки"
        )
        layout.addWidget(self.algorithm_button)
        self.algorithm_button.clicked.connect(self.show_algorithm)

        # Этапы проверки
        stages = [
            "Этап 1 — Прошивка",
            "Этап 2 — Периферия, модем и LoRa",
            "Этап 3 — Проверка DI",
            "Этап 4 — Проверка LED",
            "Этап 5 — Проверка акселерометра",
            "Этап 6 — Проверка NIDD",
        ]

        self.stage_buttons = []
        self.stage_statuses = []

        for stage in stages:
            row = QHBoxLayout()

            button = QPushButton(stage)
            button.setMinimumHeight(36)

            status = QLabel("Не проводилась")
            status.setMinimumWidth(130)
            status.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            status.setStyleSheet(
                "color: #777777; font-weight: bold;"
            )

            row.addWidget(button, 3)
            row.addWidget(status, 1)

            layout.addLayout(row)

            self.stage_buttons.append(button)
            self.stage_statuses.append(status)

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


    def connect_usb(self):
        if self.usb_serial is not None and self.usb_serial.is_open:
            return

        port = self.usb_controller.currentText()
        speed = self.usb_speed.currentText()

        if port == "COM-порты не найдены" or not port:
            QMessageBox.warning(
                self, "USB", "Не выбран COM-порт контроллера."
            )
            return

        try:
            self.usb_serial = serial.Serial(
                port=port,
                baudrate=int(speed),
                timeout=1,
            )

            self.usb_connection_status.setText("Подключено")
            self.usb_connection_status.setStyleSheet(
                "color: green; font-weight: bold;"
            )

        except (serial.SerialException, ValueError) as error:
            self.usb_serial = None
            self.usb_connection_status.setText("Не подключено")

            QMessageBox.critical(
                self,
                "Ошибка подключения USB",
                f"Не удалось открыть {port}:\n{error}",
            )


    def connect_rm4(self):
        if self.rm4_serial is not None and self.rm4_serial.is_open:
            return

        port = self.modbus_com.currentText()
        speed = self.modbus_speed.currentText()

        if port == "COM-порты не найдены" or not port:
            QMessageBox.warning(
                self, "Modbus RM-4", "Не выбран COM-порт RM-4."
            )
            return

        try:
            self.rm4_serial = serial.Serial(
                port=port,
                baudrate=int(speed),
                timeout=1,
            )

            self.rm4_connection_status.setText("Подключено")
            self.rm4_connection_status.setStyleSheet(
                "color: green; font-weight: bold;"
            )

        except (serial.SerialException, ValueError) as error:
            self.rm4_serial = None
            self.rm4_connection_status.setText("Не подключено")

            QMessageBox.critical(
                self,
                "Ошибка подключения RM-4",
                f"Не удалось открыть {port}:\n{error}",
            )


    def read_serial_logs(self):
        # Читаем данные контроллера
        if self.usb_serial is not None and self.usb_serial.is_open:
            try:
                data = self.usb_serial.read_all()

                if data:
                    text = data.decode("utf-8", errors="replace")
                    self.usb_log.moveCursor(
                        self.usb_log.textCursor().MoveOperation.End
                    )
                    self.usb_log.insertPlainText(text)
                    self.usb_log.ensureCursorVisible()

            except serial.SerialException as error:
                self.usb_log.appendPlainText(
                    f"\n[Ошибка чтения USB: {error}]"
                )

        # Читаем данные RM-4
        if self.rm4_serial is not None and self.rm4_serial.is_open:
            try:
                data = self.rm4_serial.read_all()

                if data:
                    text = data.decode("utf-8", errors="replace")
                    self.rm4_log.moveCursor(
                        self.rm4_log.textCursor().MoveOperation.End
                    )
                    self.rm4_log.insertPlainText(text)
                    self.rm4_log.ensureCursorVisible()

            except serial.SerialException as error:
                self.rm4_log.appendPlainText(
                    f"\n[Ошибка чтения RM-4: {error}]"
                )



    def show_algorithm(self):
        text_placeholder = """1. прошивка платы
1.1 если нет компорта - проверить подключения
1.2 прошивка не прошла правильно - повторить прошивку платы
2. проверка периферии стенда и линии uart lora
2.1 Включить питание и имитацию светодиодной ленты с помощью K1-K7 (Relay1-3)
2.2 Убедиться что все лампы HL1-6 горят 
2.3 В случае получения сообщения  ATC<E77> - RX:\nOK  считать что линии для LoRa в порядке.
3. проверка DI
3.1 Дождаться строки States=.. в которой биты 0-5 установлены (таймаут 2 минуты)
3.2 Имитировать нормальный режим датчиков(замкнуты) DI включив реле K8-K12 (Relay4)
3.3 Дождаться строки States= в которой биты 0-4 равны "0"
3.4 Отключить реле K8-K12 (Relay4) 
4. проверка LED
4.1 Дождаться строки в которой биты 5-8 равны "0"
4.2 Снизить ток LED выключив часть макета отключив реле K5-K7 (Relay3)
4.3 Дождаться строки с битами 5-8 в "1"
4.4 Отключить имитацию LED отключив реле K2-K4 (Relay2)
5. проверка акселерометра
5.1 Получить строку с 10м битом равным "0"
5.2 Указание наклонить плату
5.3 Дождаться строки с 10м битом в состоянии "1" и проверить что бит 11 в состоянии "0"
5.4 Ударить плату
5.5 Дождаться строки States с 11м битом равным "1"
6. проверка NIDD
6.1 регистрация симки в тестовый стенд
6.2 отправка сообщения
	ATC<N21> - TX: 
	AT+NIPDATAEX=1,0,"0189701010051400395404202601020826333330000000"
	ATC<N21> - RX: 
	OK
6.3 проверка полученного сообщения
6.4 перерегистрация симки на продакшн"""

        dialog = QDialog(self)
        dialog.setWindowTitle("Алгоритм проверки")
        dialog.resize(600, 400)

        dialog_layout = QVBoxLayout(dialog)

        algorithm_text = QPlainTextEdit()
        algorithm_text.setReadOnly(True)
        algorithm_text.setPlainText(text_placeholder)

        dialog_layout.addWidget(algorithm_text)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.accept)

        dialog_layout.addWidget(close_button)

        dialog.exec()


app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())
