import sys
import serial.tools.list_ports
import serial
import json
import os

from PyQt6.QtCore import Qt, QTimer, QProcess
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
            if stage.startswith("Этап 1"):
                button.clicked.connect(self.start_firmware_stage)
            elif stage.startswith("Этап 2"):
                button.clicked.connect(self.start_stage2)

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
                    self.check_stage2_response(text)
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


    def start_firmware_stage(self):
        if not self.show_firmware_instructions():
            return
        if not self.enable_board_power():
            return
        command = self.firmware_command.text().strip()

        if not command:
            QMessageBox.warning(
                self,
                "Прошивка",
                "Сначала укажи команду для прошивки "
                "во вкладке «Настройки».",
            )
            return

        # Создаём окно прошивки
        self.firmware_dialog = QDialog(self)
        dialog = self.firmware_dialog
        dialog.setWindowTitle("Этап 1 — Прошивка")
        dialog.resize(650, 400)

        dialog_layout = QVBoxLayout(dialog)

        dialog_layout.addWidget(QLabel("Выполняемая команда:"))

        command_view = QLineEdit(command)
        command_view.setReadOnly(True)
        dialog_layout.addWidget(command_view)

        dialog_layout.addWidget(QLabel("Вывод PowerShell:"))

        self.firmware_log = QPlainTextEdit()
        self.firmware_log.setReadOnly(True)
        dialog_layout.addWidget(self.firmware_log)

        self.firmware_result = QLabel("Ожидание запуска прошивки")
        dialog_layout.addWidget(self.firmware_result)

        start_button = QPushButton("Начать прошивку")
        dialog_layout.addWidget(start_button)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.accept)
        dialog_layout.addWidget(close_button)

        self.firmware_timed_out = False

        start_button.clicked.connect(lambda: self.run_firmware_command(command, start_button))

        dialog.exec()


    def show_firmware_instructions(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Этап 1 — Подготовка к прошивке")
        dialog.setMinimumWidth(450)

        layout = QVBoxLayout(dialog)

        message = QLabel(
            "Перед началом прошивки выполните следующие действия:\n\n"
            "1. Поставьте джампер на JP3.\n"
            "2. Подключите USB к плате."
        )
        message.setWordWrap(True)
        layout.addWidget(message)

        continue_button = QPushButton("Готово, продолжить")
        continue_button.clicked.connect(dialog.accept)
        layout.addWidget(continue_button)

        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(dialog.reject)
        layout.addWidget(cancel_button)

        return dialog.exec() == QDialog.DialogCode.Accepted


    def run_firmware_command(self, command, start_button):
        start_button.setEnabled(False)

        self.firmware_result.setText("Выполняется прошивка...")
        self.firmware_result.setStyleSheet(
            "color: #b8860b; font-weight: bold;"
        )

        self.firmware_timed_out = False

        self.firmware_process = QProcess(self)
        self.firmware_process.setProgram("powershell.exe")
        self.firmware_process.setArguments([
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ])

        self.firmware_process.readyReadStandardOutput.connect(
            self.read_firmware_output
        )
        self.firmware_process.readyReadStandardError.connect(
            self.read_firmware_error
        )
        self.firmware_process.finished.connect(
            self.firmware_finished
        )
        self.firmware_process.errorOccurred.connect(
            self.firmware_process_error
        )

        self.firmware_timer = QTimer(self)
        self.firmware_timer.setSingleShot(True)
        self.firmware_timer.timeout.connect(
            self.firmware_timeout
        )

        self.firmware_log.appendPlainText(
            "\nЗапуск PowerShell..."
        )
        self.firmware_process.start()
        self.firmware_timer.start(60000)


    def read_firmware_output(self):
        data = self.firmware_process.readAllStandardOutput().data()
        if data:
            self.firmware_log.appendPlainText(
                data.decode("utf-8", errors="replace").rstrip()
            )


    def read_firmware_error(self):
        data = self.firmware_process.readAllStandardError().data()
        if data:
            self.firmware_log.appendPlainText(
                data.decode("utf-8", errors="replace").rstrip()
            )


    def firmware_finished(self, exit_code, exit_status):
        self.firmware_timer.stop()

        # Считываем остаток вывода перед завершением
        self.read_firmware_output()
        self.read_firmware_error()

        if self.firmware_timed_out:
            return

        output = self.firmware_log.toPlainText()

        if (exit_status == QProcess.ExitStatus.NormalExit and exit_code == 0 and "Download verified successfully" in output):
            self.firmware_result.setText("Прошивка: команда завершилась успешно")
            self.stage_statuses[0].setText("Пройдено")
            if self.disable_board_power():
                self.show_remove_jumper_dialog()
            self.stage_statuses[0].setStyleSheet(
                "color: green; font-weight: bold;"
            )
        else:
            self.firmware_result.setText(
                f"Ошибка выполнения. Код завершения: {exit_code}"
            )
            self.stage_statuses[0].setText("Неудачно")
            self.stage_statuses[0].setStyleSheet(
                "color: red; font-weight: bold;"
            )


    def firmware_timeout(self):
        if self.firmware_process.state() == QProcess.ProcessState.NotRunning:
            return

        self.firmware_timed_out = True
        self.firmware_log.appendPlainText(
            "\nВремя ожидания истекло: 60 секунд."
        )
        self.firmware_result.setText("Ошибка: превышено время ожидания")

        self.stage_statuses[0].setText("Неудачно")
        self.stage_statuses[0].setStyleSheet(
            "color: red; font-weight: bold;"
        )

        self.firmware_process.kill()


    def firmware_process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.firmware_timer.stop()
            self.firmware_log.appendPlainText(
                "Не удалось запустить PowerShell."
            )
            self.firmware_result.setText("Ошибка запуска процесса")

            self.stage_statuses[0].setText("Неудачно")
            self.stage_statuses[0].setStyleSheet(
                "color: red; font-weight: bold;"
            )


    def enable_board_power(self):
        if self.rm4_serial is None or not self.rm4_serial.is_open:
            QMessageBox.warning(
                self,
                "RM-4 не подключён",
                "Сначала подключите RM-4 на вкладке проверки устройства."
            )
            return False

        command = bytes.fromhex("01 05 00 01 FF 00 DD FA")

        try:
            self.rm4_serial.reset_input_buffer()
            self.rm4_serial.write(command)
            self.rm4_serial.flush()

            response = self.rm4_serial.read(8)

            if response != command:
                return True

            QMessageBox.warning(
                self,
                "Ошибка RM-4",
                f"Нет корректного подтверждения включения питания.\n"
                f"Ответ: {response.hex(' ').upper() or 'нет ответа'}"
            )
            return False

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка RM-4",
                f"Не удалось включить питание платы:\n{e}"
            )
            return False


    def disable_board_power(self):
        if self.rm4_serial is None or not self.rm4_serial.is_open:
            QMessageBox.critical(
                self,
                "Ошибка RM-4",
                "Нет подключения к RM-4. Не удалось выключить питание."
            )
            return False

        command = bytes.fromhex("01 05 00 01 00 00 9C 0A")

        try:
            self.rm4_serial.reset_input_buffer()
            self.rm4_serial.write(command)
            self.rm4_serial.flush()

            response = self.rm4_serial.read(8)

            if response == command:
                return True

            QMessageBox.critical(
                self,
                "Ошибка RM-4",
                "Не получено подтверждение выключения питания.\n"
                f"Ответ: {response.hex(' ').upper() or 'нет ответа'}"
            )
            return False

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка RM-4",
                f"Не удалось выключить питание платы:\n{e}"
            )
            return False


    def show_remove_jumper_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Этап 1 — Завершение")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        message = QLabel(
            "Прошивка успешно завершена.\n\n"
            "Питание платы выключено.\n\n"
            "Уберите джампер с платы."
        )
        message.setWordWrap(True)
        layout.addWidget(message)

        button = QPushButton("Готово")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)

        dialog.exec()


    def modbus_crc16(self, data):
        crc = 0xFFFF

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1

        return crc


    def set_rm4_relay(self, relay_number, enabled):
        if self.rm4_serial is None or not self.rm4_serial.is_open:
            QMessageBox.warning(
                self, "RM-4", "Сначала подключите RM-4."
            )
            return False

        address = relay_number.to_bytes(2, "big")
        value = b"\xFF\x00" if enabled else b"\x00\x00"

        frame = b"\x01\x05" + address + value
        crc = self.modbus_crc16(frame)
        command = frame + bytes([crc & 0xFF, crc >> 8])

        try:
            self.rm4_serial.reset_input_buffer()
            self.rm4_serial.write(command)
            self.rm4_serial.flush()

            response = self.rm4_serial.read(8)

            if response == command:
                return True

            QMessageBox.warning(
                self,
                "RM-4",
                f"Реле {relay_number}: нет корректного ответа.\n"
                f"Получено: {response.hex(' ').upper() or 'нет ответа'}"
            )
            return False

        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка RM-4", str(e)
            )
            return False


    def start_stage2(self):
        # 1. Питание платы — реле 1
        if not self.enable_board_power():
            return

        # 2. Включаем имитацию — реле 2 и 3
        if not self.set_rm4_relay(2, True):
            return

        if not self.set_rm4_relay(3, True):
            return

        # 3. Проверяем лампы HL1–HL6
        answer = QMessageBox.question(
            self,
            "Этап 2 — Проверка индикации",
            "Горят ли лампы HL1–HL6?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if answer != QMessageBox.StandardButton.Yes:
            self.stage_statuses[1].setText("Не пройдено")
            self.stage_statuses[1].setStyleSheet(
                "color: red; font-weight: bold;"
            )
            return

        # 4. Ожидаем ответ контроллера по USB
        if self.usb_serial is None or not self.usb_serial.is_open:
            QMessageBox.warning(
                self,
                "USB",
                "Подключите USB-порт контроллера на вкладке проверки."
            )
            return

        self.stage2_usb_buffer = ""
        self.stage2_waiting_for_response = True

        self.stage_statuses[1].setText("Ожидание ответа контроллера...")
        self.stage_statuses[1].setStyleSheet(
            "color: #b8860b; font-weight: bold;"
        )

        self.stage2_timer = QTimer(self)
        self.stage2_timer.setSingleShot(True)
        self.stage2_timer.timeout.connect(
            self.stage2_response_timeout
        )
        self.stage2_timer.start(60000)


    def check_stage2_response(self, text):
        if not getattr(self, "stage2_waiting_for_response", False):
            return

        self.stage2_usb_buffer += text

        # Защита от бесконечного накопления данных
        self.stage2_usb_buffer = self.stage2_usb_buffer[-2000:]

        marker = "ATC<E77> - RX:"
        if marker in self.stage2_usb_buffer:
            response = self.stage2_usb_buffer.split(marker, 1)[1]

            if "OK" in response:
                self.stage2_waiting_for_response = False
                self.stage2_timer.stop()

                self.stage_statuses[1].setText("Пройдено")
                self.stage_statuses[1].setStyleSheet(
                    "color: green; font-weight: bold;"
                )


    def stage2_response_timeout(self):
        if not getattr(self, "stage2_waiting_for_response", False):
            return

        self.stage2_waiting_for_response = False

        self.stage_statuses[1].setText("Не пройдено — нет ответа")
        self.stage_statuses[1].setStyleSheet(
            "color: red; font-weight: bold;"
        )

        QMessageBox.warning(
            self,
            "Этап 2",
            "За 60 секунд не получен ожидаемый ответ:\n"
            "ATC<E77> - RX: OK"
        )



app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())
