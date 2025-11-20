import sys
import traceback

from PyQt6 import uic, QtWidgets, QtSql  # Импортируем uic
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QStackedWidget, QWidget, QCheckBox, QVBoxLayout, \
    QTableView
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

        # Название окна
        self.setWindowTitle("Подсчет калорий")

        # Страница настроек
        self.settings_window = SettingsWindow()

        # Добавляем страницы в стек
        self.main_stackedWidget.addWidget(self.page_today)
        self.main_stackedWidget.addWidget(self.page_add_food)
        self.main_stackedWidget.addWidget(self.page_products)

        # Подключение кнопок переключения страниц
        self.today.clicked.connect(lambda: self.main_stackedWidget.setCurrentIndex(0))
        self.add_food.clicked.connect(lambda: self.main_stackedWidget.setCurrentIndex(1))
        self.products.clicked.connect(lambda: self.main_stackedWidget.setCurrentIndex(2))

        # Подключение кнопки настроек
        self.settings.clicked.connect(self.to_settings)

        # Кнопки приборной панели
        self.close_window.clicked.connect(self.to_close)
        self.unwrap_window.clicked.connect(self.to_unwrap)
        self.roll_up_window.clicked.connect(self.to_roll_up)

        # Кнопка убирания меню
        self.menu_button.clicked.connect(self.off_menu)

        # Установка текущей даты
        self.dateEdit.setDate(QDate.currentDate())

        # Применяем эффект тени к списку элементов
        # for element in shadow_elements:
        #     # Настройка эффекта тени
        #     effect = QtWidgets.QGraphicsDropShadowEffect(self)
        #     effect.setBlurRadius(18)
        #     effect.setXOffset(0)
        #     effect.setYOffset(0)
        #     effect.setColor(QColor(0, 0, 0, 255))
        #     getattr(self, element).setGraphicsEffect(effect)

        # Страница основная
        # Подключение кнопки на главной странице для добавления еды
        self.add_food_2.clicked.connect(lambda: self.main_stackedWidget.setCurrentIndex(1))
        self.count_max_calories.setText(str(self.max_calories))
        self.count_today_calories.setText(str(self.today_calories) + "/" + str(self.max_calories))

        # Страница добавления приёма пищи
        # Название продукта
        self.add_breakfast.clicked.connect(
            self.on_add_food_item)

        # # Зададим тип базы данных
        # db = QSqlDatabase.addDatabase('QSQLITE')
        # # Укажем имя базы данных
        # db.setDatabaseName('calorie_tracker.db')
        # # И откроем подключение
        # db.open()

        # db1 = QSqlDatabase.addDatabase("QSQLITE", "connection1");
        # db1.setDatabaseName("data1.db");
        #
        # # Создадим объект QSqlTableModel,
        # # зададим таблицу, с которой он будет работать,
        # #  и выберем все данные

        # Подключаем бд
        db1 = QSqlDatabase.addDatabase('QSQLITE', 'con1')
        db1.setDatabaseName('calorie_tracker.db')
        db1.commit()
        db1.open()

        # Создание модели
        model = QSqlTableModel(self, db1)
        model.setTable("food_items")
        model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)  # автоматическое сохранение при изменении

        # Заголовки
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

        # Отображение в таблице
        self.table_products.setModel(model)

        # Загружаем данные из БД
        if not model.select():
            print("Ошибка загрузки данных:", model.lastError().text())
        else:
            print(f"Загружено {model.rowCount()} строк.")

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
        """Добавляет продукт в data1.db."""
        query = QSqlQuery(QSqlDatabase.database("db1"))
        query.prepare("""",
            INSERT INTO food_items
            (name, category, calories, protein, fat, carbs, fiber, serving_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """)
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
    def add_meal(meal_type, notes=None):
        """Добавляет приём пищи в data2.db."""
        query = QSqlQuery(QSqlDatabase.database("db1"))
        query.prepare("""",
            INSERT INTO meals (meal_type, notes)
            VALUES (?, ?)
        """)
        query.addBindValue(meal_type)
        query.addBindValue(notes)

        if query.exec():
            meal_id = query.lastInsertId()
            print(f"Приём пищи ({meal_type}) добавлен. ID: {meal_id}")
            return meal_id
        else:
            print(f"Ошибка добавления приёма пищи: {query.lastError().text()}")
            return None

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

    # Скрытие меню
    def off_menu(self):
        print("off_menu")

    # Страница добавления приёма пищи
    # Добавление нового приёма пищи
    def new_breakfast(self):
        print("new_breakfast")

    # Добавление нового продукта
    def new_product(self):
        print("new_product")

    # 
    def exception_hook(exctype, value, tb):
        print("Произошла ошибка:")
        traceback.print_exception(exctype, value, tb)


# Класс настроек
class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("MyCompany", "MyApp")

        self.checkbox = QCheckBox("Включить опцию")
        self.checkbox.setChecked(self.settings.value("option_enabled", False, type=bool))

        self.setMinimumSize(350, 350)

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_settings)

        layout = QVBoxLayout()
        layout.addWidget(self.checkbox)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def save_settings(self):
        self.settings.setValue("option_enabled", self.checkbox.isChecked())
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    Window = MainWindow()
    Window.show()
    sys.exit(app.exec())
