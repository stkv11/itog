import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
import datetime  # Импортируем модуль для работы с датой и временем

# --- Настройки ---
API_KEY = "ВАШ_API_КЛЮЧ"  # Замените на свой ключ с exchangerate-api.com
HISTORY_FILE = "history.json"  # Файл для сохранения истории


# --- Функции работы с API ---
def get_conversion_rate(from_currency, to_currency):
    """Получает курс конвертации из API."""
    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{from_currency}/{to_currency}"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("result") == "success":
            return data["conversion_rate"]
        else:
            # Если API вернуло ошибку, показываем её пользователю
            messagebox.showerror("Ошибка API", data.get("error-type", "Неизвестная ошибка"))
            return None
    except Exception as e:
        # Обработка ошибок сети (нет интернета и т.д.)
        messagebox.showerror("Ошибка сети", str(e))
        return None


# --- Функции работы с историей ---
def save_history(entry):
    """Сохраняет запись о конвертации в JSON-файл."""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []
        history.append(entry)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить историю: {e}")


def load_history():
    """Загружает историю из JSON-файла."""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить историю: {e}")
        return []


# --- Основная логика приложения ---
class CurrencyConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер валют")
        self.root.geometry("600x450")

        # Список доступных валют
        self.currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY"]

        # Создаем все виджеты (кнопки, поля, таблицу)
        self.create_widgets()

        # При запуске приложения загружаем историю в таблицу
        self.load_history_to_table()

    def create_widgets(self):
        # --- Блок выбора валют и ввода суммы ---
        input_frame = ttk.LabelFrame(self.root, text="Параметры конвертации", padding="10")
        input_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(input_frame, text="Из:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.from_currency_var = tk.StringVar(value="USD")
        ttk.Combobox(input_frame, textvariable=self.from_currency_var,
                     values=self.currencies, state="readonly", width=8).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="В:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.to_currency_var = tk.StringVar(value="EUR")
        ttk.Combobox(input_frame, textvariable=self.to_currency_var,
                     values=self.currencies, state="readonly", width=8).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="Сумма:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.amount_entry = ttk.Entry(input_frame)
        self.amount_entry.grid(row=2, column=1, padx=5, pady=2)

        ttk.Button(input_frame, text="Конвертировать", command=self.convert).grid(row=3, column=0, columnspan=2,
                                                                                  pady=10)

        # --- Блок вывода результата ---
        self.result_label = ttk.Label(self.root, text="", font=("Arial", 12), wraplength=500)
        self.result_label.pack(pady=5)

        # --- Блок таблицы истории ---
        history_frame = ttk.LabelFrame(self.root, text="История операций", padding="5")
        history_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.history_tree = ttk.Treeview(history_frame,
                                         columns=("from", "to", "amount", "result", "date"),
                                         show="headings")

        # Определяем заголовки таблицы
        self.history_tree.heading("from", text="Из")
        self.history_tree.heading("to", text="В")
        self.history_tree.heading("amount", text="Сумма")
        self.history_tree.heading("result", text="Результат")
        self.history_tree.heading("date", text="Дата и время")

        self.history_tree.column("date", width=150)  # Делаем колонку с датой шире

        self.history_tree.pack(fill="both", expand=True)

    def is_valid_amount(self):
        """Проверяет корректность введённой суммы."""
        amount_str = self.amount_entry.get()
        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showwarning("Ошибка ввода", "Сумма должна быть положительным числом.")
                return False
            return True
        except ValueError:
            messagebox.showwarning("Ошибка ввода", "Введите корректное число.")
            return False

    def convert(self):
        """Выполняет конвертацию валюты."""
        if not self.is_valid_amount():
            return

        from_cur = self.from_currency_var.get()
        to_cur = self.to_currency_var.get()

        rate = get_conversion_rate(from_cur, to_cur)

        if rate is not None:
            amount = float(self.amount_entry.get())
            result = round(amount * rate, 2)

            # Получаем текущую дату и время в виде строки
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Отображение результата пользователю
            self.result_label.config(
                text=f"{amount} {from_cur} = {result} {to_cur} (Курс: 1 {from_cur} = {rate} {to_cur})"
            )

            # Подготовка данных для сохранения в историю
            entry = {
                "from": from_cur,
                "to": to_cur,
                "amount": amount,
                "result": result,
                "rate": rate,
                "timestamp": current_time  # Сохраняем актуальное время
            }

            save_history(entry)  # Сохраняем в файл

            # Добавляем строку в таблицу (в начало списка)
            self.history_tree.insert("", 0,
                                     values=(from_cur, to_cur, amount,
                                             f"{result} {to_cur}", current_time))

    def load_history_to_table(self):
        """Загружает историю из файла в таблицу при запуске."""
        history = load_history()

        # Очищаем таблицу перед загрузкой (на случай повторных вызовов)
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        for entry in history:
            self.history_tree.insert("", 0,
                                     values=(entry["from"],
                                             entry["to"],
                                             entry["amount"],
                                             f"{entry['result']} {entry['to']}",
                                             entry["timestamp"]))


if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverterApp(root)
    root.mainloop()