import sys
import traceback
from pathlib import Path

from PyQt6 import uic  # Импортируем uic
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QCheckBox, QVBoxLayout, \
    QHeaderView, QMessageBox, QLineEdit, QInputDialog, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout
from PyQt6.QtCore import QDate, QSettings, Qt  # Текущая дата

# Список Ui виджетов
shadow_elements = {
    "menu_widget",
    "header_menu_frame",
    "loader_menu_frame",
    "header_main_frame",
    "main_frame"
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('interface.ui', self)  # Загружаем дизайн
        sys.excepthook = self.exception_hook

        self.max_calories = 2600
        self.today_calories = 0
        self.full_screen = False

        # Минимальный размер окна
        self.setMinimumSize(850, 700)
        self.setGeometry(300, 100, 850, 700)

        # Название окна
        self.setWindowTitle("Подсчет калорий")

        # Страница настроек
        self.settings_window = SettingsWindow()

        # Добавляем страницы в стек
        self.main_stackedWidget.addWidget(self.page_today)
        self.main_stackedWidget.addWidget(self.page_products)
        self.main_stackedWidget.addWidget(self.page_add_food)
        self.main_stackedWidget.addWidget(self.page_add_breakfast)
        self.main_stackedWidget.addWidget(self.page_history)

        # Подключение кнопок переключения страниц
        self.today.clicked.connect(lambda: self.main_stackedWidget.setCurrentIndex(0))
        self.products.clicked.connect(lambda: self.main_stackedWidget.setCurrentIndex(1))
        self.add_food.clicked.connect(lambda: self.main_stackedWidget.setCurrentIndex(2))
        self.add_breakfast.clicked.connect(lambda: self.main_stackedWidget.setCurrentIndex(3))
        self.history.clicked.connect(lambda: self.main_stackedWidget.setCurrentIndex(4))

        # Подключение кнопки настроек
        self.settings.clicked.connect(self.to_settings)

        # Кнопки приборной панели
        self.close_window.clicked.connect(self.to_close)
        self.unwrap_window.clicked.connect(self.to_unwrap)
        self.roll_up_window.clicked.connect(self.to_roll_up)

        # Установка текущей даты
        self.dateEdit.setDate(QDate.currentDate())

        # Страница главная
        # Подключение кнопки на главной странице для добавления еды
        self.add_food_2.clicked.connect(lambda: self.main_stackedWidget.setCurrentIndex(1))


        # Страница добавления приёма пищи
        # Подключение кнопки для добавления еды
        self.button_add_food.clicked.connect(
            self.on_add_food_item)

        # Страница добавления приёма пищи
        # Подключение кнопки для добавления приёма пищи
        self.button_add_breakfast.clicked.connect(self.add_meal)

        # Кнопка обновления бд
        self.pushButton_ubdate_history.clicked.connect(self.update_bd)
        self.pushButton_ubdate_product.clicked.connect(self.update_bd)

        # Кнопка удаления строки из бд истории
        self.pushButton_delete.clicked.connect(self.delete_record_by_id)

        self.update_bd()

    def update_bd(self):
        # Подключаем бд
        db1 = QSqlDatabase.addDatabase('QSQLITE', "db1")
        db1.setDatabaseName('calorie_tracker.db')
        db1.open()

        # Создание модели для продуктов
        model = QSqlTableModel(self, db1)
        model.setTable("food_items")
        model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)  # автоматическое сохранение при изменении

        # Создание модели для истории
        model2 = QSqlTableModel(self, db1)
        model2.setTable("meals")
        model2.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)

        # Заголовки для продуктов
        model.setHeaderData(0, Qt.Orientation.Horizontal, "ID")
        model.setHeaderData(1, Qt.Orientation.Horizontal, "Продукт")
        model.setHeaderData(2, Qt.Orientation.Horizontal, "Категория")
        model.setHeaderData(3, Qt.Orientation.Horizontal, "Калории (ккал)")
        model.setHeaderData(4, Qt.Orientation.Horizontal, "Протеин")
        model.setHeaderData(5, Qt.Orientation.Horizontal, "Жиры")
        model.setHeaderData(6, Qt.Orientation.Horizontal, "Углеводы")
        model.setHeaderData(7, Qt.Orientation.Horizontal, "Белок")
        model.setHeaderData(8, Qt.Orientation.Horizontal, "Размер порции")
        model.setHeaderData(9, Qt.Orientation.Horizontal, "Избранное")

        # Заголовки для истории
        model2.setHeaderData(0, Qt.Orientation.Horizontal, "ID")
        model2.setHeaderData(1, Qt.Orientation.Horizontal, "Время")
        model2.setHeaderData(2, Qt.Orientation.Horizontal, "Калории")
        model2.setHeaderData(3, Qt.Orientation.Horizontal, "Тип")
        model2.setHeaderData(4, Qt.Orientation.Horizontal, "Заметки")

        # Отображение в таблице
        self.table_products.setModel(model)
        self.table_history.setModel(model2)
        # Настройка таблицы
        self.table_history.setColumnWidth(0, 10)
        self.table_history.setColumnWidth(1, 150)

        header = self.table_history.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)

        # Загружаем данные из БД продуктов
        if not model.select():
            print("Ошибка загрузки данных:", model.lastError().text())
        else:
            print(f"Загружено {model.rowCount()} строк.")

        # Загружаем данные из БД истории
        if not model2.select():
            print("Ошибка загрузки данных:", model2.lastError().text())
        else:
            print(f"Загружено {model2.rowCount()} строк.")

        # Данные в количество калорий в день
        sql = "SELECT calories FROM meals"
        query = QSqlQuery(QSqlDatabase.database("db1"))

        if not query.exec(sql):
            print(f"Ошибка выполнения запроса: {query.lastError().text()}")
            return []

        self.today_calories = 0

        while query.next():
            value = query.value(0)

            if value is not None:
                try:
                    self.today_calories += int(value)
                except (ValueError, TypeError) as e:
                    print(f"Некорректное значение в столбце calories: {value}, ошибка: {e}")

        self.count_max_calories.setText(str(self.max_calories))
        self.count_today_calories.setText(str(self.today_calories) + "/" + str(self.max_calories))
        self.count_today_calories.setReadOnly(True)

        # Прогресс бар
        self.progressBar.setRange(0, self.max_calories)
        self.progressBar.setValue(self.today_calories)

    # Проверка перед добавлением продукта
    def on_add_food_item(self):
        # Получаем данные из полей ввода
        name = self.name_product.text()
        category = self.category_product.text()
        calories_text = self.count_calories.text()
        protein = self.protein_product.text()
        fat = self.fat_product.text()
        carbs = self.carbs_product.text()
        fiber = self.fiber_product.text()
        serving_size = self.veight_product.text()

        # Проверяем, что поля заполнены
        if not name or not category or not calories_text or not protein or not fat or not carbs or not fiber:
            print("Заполните все поля!")
            return

        try:
            calories = float(calories_text)
        except ValueError:
            print("Калории должны быть числом!")
            return

        # Вызываем функцию добавления в БД
        self.add_food_item(name, category, calories, protein, fat, carbs, fiber, serving_size)

    # Добавление новой еды
    def add_food_item(self, name, category, calories, protein, fat, carbs, fiber=0, serving_size=None):
        """Добавляет продукт в food_items."""
        query = QSqlQuery(QSqlDatabase.database("db1"))
        query.prepare("INSERT INTO food_items "
                      "(name, category, calories, protein, fat, carbs, fiber, serving_size) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                      )
        query.addBindValue(name)
        query.addBindValue(category)
        query.addBindValue(calories)
        query.addBindValue(protein)
        query.addBindValue(fat)
        query.addBindValue(carbs)
        query.addBindValue(fiber)
        query.addBindValue(serving_size)

        if query.exec():
            print(f"Продукт '{name}' добавлен.")
        else:
            print(f"Ошибка добавления продукта: {query.lastError().text()}")

    # Добавление нового приема пищи
    def add_meal(self):
        try:
            meal_type = self.comboBox_type_meal.currentText()
            notes = self.text_notes.toPlainText()
            calories = self.total_calories.text()
        except Exception:
            print(Exception)
        """Добавляет приём пищи в meals."""
        query = QSqlQuery(QSqlDatabase.database("db1"))
        query.prepare("INSERT INTO meals (calories, meal_type, notes)"
                      "VALUES (?, ?, ?)")
        query.addBindValue(calories)
        query.addBindValue(meal_type)
        query.addBindValue(notes)

        if query.exec():
            meal_id = query.lastInsertId()
            print(f"Приём пищи ({meal_type}) добавлен. ID: {meal_id}")
            return meal_id
        else:
            print(f"Ошибка добавления приёма пищи: {query.lastError().text()}")
            return None

    # Удаление строки из бд
    def delete_record_by_id(self, current_id=None) -> bool:
        """
        Диалог: ввод ID + подтверждение → удаление строки из SQL-таблицы.

        Параметры:
            table_name (str): имя таблицы в БД.
            current_id (int, optional): предустановленный ID (для удобства).

        Возвращает:
            True — если запись удалена.
            False — если отмена, ошибка ввода или SQL-ошибка.
        """
        # Диалог
        label = "Введите ID записи для удаления:"
        if current_id is not None:
            label += f" (текущий: {current_id})"

        text, ok = QInputDialog.getText(
            self,
            "Удаление записи",
            label,
            QLineEdit.EchoMode.Normal,
            str(current_id) if current_id else ""
        )

        if not ok or not text.strip():
            return False  # Отмена или пустое поле
        try:
            record_id = int(text.strip())
            if record_id < 1:
                QMessageBox.warning(self, "Ошибка", "ID должен быть положительным числом")
                return False
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Некорректный формат ID")
            return False

        # Подтверждение
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы точно хотите удалить запись с ID = {record_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return False

        # Удаление
        query = QSqlQuery(QSqlDatabase.database("db1"))
        query.prepare("DELETE FROM meals WHERE meal_id = ?")
        query.addBindValue(int(record_id))

        if query.exec():
            if query.numRowsAffected() > 0:
                QMessageBox.information(self, "Успех", f"Запись с ID {record_id} удалена из таблицы")
                return True
            else:
                QMessageBox.warning(self, "Не найдено", f"Запись с ID {record_id} не найдена в таблице")
                return False
        else:
            QMessageBox.critical(self, "SQL-ошибка", f"Не удалось выполнить удаление:\n{query.lastError().text()}")
            return False

    # Настройки
    def to_settings(self):
        self.settings_window.show()

    # Закрытие страницы
    def to_close(self):
        self.close()

    # Разворачивание и свёртывание страницы
    def to_roll_up(self):
        self.showMinimized()

    # Сворачивание в окно
    def to_unwrap(self):
        if self.full_screen:
            self.full_screen = False
            self.resize(self.last_width, self.last_height)
            self.center()
        else:
            self.full_screen = True
            self.last_width, self.last_height = self.width(), self.height()
            self.showMaximized()

    # Установка окна по центру экрана
    def center(self):
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        window_size = self.size()
        x = (screen_size.width() - window_size.width()) // 2
        y = (screen_size.height() - window_size.height()) // 2
        self.move(x, y)

    # Изменение нужного количества калорий
    def change_max_calories(self):
        print("change_max_calories")
        self.max_calories = self.count_max_calories.value()
        print("max_calories: ", self.max_calories)

    # Обработка ошибок
    def exception_hook(exctype, value, tb):
        print("Произошла ошибка:")
        traceback.print_exception(exctype, value, tb)


# Класс настроек
class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Настройки темы")
        self.resize(320, 160)

        # Путь к файлу настроек
        self.theme_file = Path("theme.txt")

        # Основной макет
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Заголовок
        title_label = QLabel("Настройки темы")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Чекбокс темы
        self.theme_checkbox = QCheckBox("Тёмная тема")
        layout.addWidget(self.theme_checkbox)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        apply_btn = QPushButton("Применить")
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Загружаем тему при старте
        self.load_theme()

    def load_theme(self):
        # Читает тему из файла theme.txt, если файла нет — ставит светлую
        try:
            if self.theme_file.exists():
                with open(self.theme_file, "r", encoding="utf-8") as f:
                    line = f.readline().strip()
                    is_dark = line.lower() == "dark"
            else:
                is_dark = False  # Дефолт — светлая тема

            self.theme_checkbox.setChecked(is_dark)
            self._apply_theme(is_dark)

        except Exception as e:
            print(f"Ошибка при загрузке темы: {e}")
            self.theme_checkbox.setChecked(False)
            self._apply_theme(False)

    def save_theme(self, is_dark: bool):
        # Сохраняет выбранную тему в theme.txt
        try:
            with open(self.theme_file, "w", encoding="utf-8") as f:
                f.write("dark" if is_dark else "light")
        except Exception as e:
            print(f"Ошибка при сохранении темы: {e}")

    def apply_settings(self):
        # Применяет и сохраняет выбранную тему
        is_dark = self.theme_checkbox.isChecked()
        self.save_theme(is_dark)
        self._apply_theme(is_dark)
        print(f"Тема сохранена: {'тёмная' if is_dark else 'светлая'}")
        self.close()

    def _apply_theme(self, is_dark: bool):
        # Применяет цветовую схему
        palette = QPalette()

        if is_dark:
            # Тёмная тема
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

            self.setStyleSheet("background-color: #353535; color: white;")
        else:
            # Светлая тема
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.WindowText, QColor(50, 50, 50))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.AlternateBase, QColor(230, 230, 230))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.ToolTipText, QColor(30, 30, 30))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Text, QColor(60, 60, 60))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Button, QColor(220, 220, 220))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.ButtonText, QColor(50, 50, 50))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Link, QColor(0, 100, 200))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Highlight, QColor(0, 120, 220))
            palette.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

            self.setStyleSheet("")

        self.setPalette(palette)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    Window = MainWindow()
    Window.show()
    sys.exit(app.exec())
