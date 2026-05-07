import tkinter as tk
from tkinter import ttk, messagebox
import json
import requests
import datetime
from typing import Dict, Optional


class CurrencyConverter:
    """Конвертер валют с использованием внешнего API."""

    HISTORY_FILE = "converter_history.json"

    # Список популярных валют
    CURRENCIES = [
        "USD", "EUR", "RUB", "GBP", "JPY", "CNY",
        "CHF", "CAD", "AUD", "KZT", "UAH", "BYN"
    ]

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Конвертер валют")
        self.root.geometry("700x850")
        self.root.resizable(True, True)
        self.root.minsize(600, 700)

        self.history = []
        self.current_rates = {}
        self.api_key = ""  # Будет загружен из файла

        self._load_api_key()
        self._setup_styles()
        self._setup_ui()
        self._load_history()
        self._load_rates()


    def _setup_styles(self):
        """Настройка стилей для ttk."""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Title.TLabel', font=('Arial', 20, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 13, 'bold'))
        style.configure('Normal.TLabel', font=('Arial', 11))
        style.configure('Convert.TButton', font=('Arial', 14, 'bold'))
        style.configure('History.Treeview', font=('Arial', 10))
        style.configure('History.Treeview.Heading', font=('Arial', 11, 'bold'))


    def _setup_ui(self):
        """Создание интерфейса."""
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        ttk.Label(main_frame, text="💱 Конвертер валют",
                 style='Title.TLabel').pack(pady=(0, 20))

        # Фрейм конвертации
        convert_frame = ttk.LabelFrame(main_frame, text="Конвертация", padding="15")
        convert_frame.pack(fill="x", pady=(0, 15))

        # Выбор валют
        currency_frame = ttk.Frame(convert_frame)
        currency_frame.pack(fill="x", pady=(0, 15))

        # Исходная валюта
        from_frame = ttk.Frame(currency_frame)
        from_frame.pack(side="left", expand=True, padx=(0, 10))
        ttk.Label(from_frame, text="Из:", style='Normal.TLabel').pack(anchor="w")
        self.from_currency = ttk.Combobox(from_frame, values=self.CURRENCIES,
                                          font=('Arial', 12), width=10, state="readonly")
        self.from_currency.set("USD")
        self.from_currency.pack(fill="x", pady=(5, 0))

        # Стрелка
        ttk.Label(currency_frame, text="→", font=('Arial', 20, 'bold')).pack(side="left", padx=20)

        # Целевая валюта
        to_frame = ttk.Frame(currency_frame)
        to_frame.pack(side="left", expand=True, padx=(10, 0))
        ttk.Label(to_frame, text="В:", style='Normal.TLabel').pack(anchor="w")
        self.to_currency = ttk.Combobox(to_frame, values=self.CURRENCIES,
                                        font=('Arial', 12), width=10, state="readonly")
        self.to_currency.set("RUB")
        self.to_currency.pack(fill="x", pady=(5, 0))

        # Кнопка смены валют местами
        ttk.Button(currency_frame, text="⇄", width=3,
                  command=self._swap_currencies).pack(side="left", padx=20, pady=(20, 0))

        # Сумма
        amount_frame = ttk.Frame(convert_frame)
        amount_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(amount_frame, text="Сумма:", style='Normal.TLabel').pack(anchor="w")
        self.amount_entry = ttk.Entry(amount_frame, font=('Arial', 14), width=25)
        self.amount_entry.pack(fill="x", pady=(5, 0))

        # Кнопка конвертации
        self.convert_btn = ttk.Button(convert_frame, text="Конвертировать",
                                      style='Convert.TButton', command=self._convert)
        self.convert_btn.pack(pady=(0, 10))

        # Результат
        result_frame = ttk.Frame(convert_frame)
        result_frame.pack(fill="x")

        ttk.Label(result_frame, text="Результат:", style='Normal.TLabel').pack(anchor="w")
        self.result_label = ttk.Label(result_frame, text="Введите данные для конвертации",
                                      font=('Arial', 18, 'bold'), foreground="#2196F3")
        self.result_label.pack(pady=(5, 0))

        # Курс валют
        rate_frame = ttk.LabelFrame(main_frame, text="Текущие курсы (USD)", padding="15")
        rate_frame.pack(fill="x", pady=(0, 15))

        # Таблица курсов
        columns = ("Валюта", "Курс")
        self.rates_tree = ttk.Treeview(rate_frame, columns=columns, show="headings", height=5)
        self.rates_tree.heading("Валюта", text="Валюта")
        self.rates_tree.heading("Курс", text="Курс к USD")
        self.rates_tree.column("Валюта", width=100)
        self.rates_tree.column("Курс", width=100)
        self.rates_tree.pack(fill="x")

        # Фрейм истории
        history_frame = ttk.LabelFrame(main_frame, text="История конвертаций", padding="15")
        history_frame.pack(fill="both", expand=True)

        # Таблица истории
        columns = ("Дата", "Из", "Сумма", "В", "Результат")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=8)

        self.history_tree.heading("Дата", text="Дата")
        self.history_tree.heading("Из", text="Из")
        self.history_tree.heading("Сумма", text="Сумма")
        self.history_tree.heading("В", text="В")
        self.history_tree.heading("Результат", text="Результат")

        self.history_tree.column("Дата", width=120)
        self.history_tree.column("Из", width=60)
        self.history_tree.column("Сумма", width=80)
        self.history_tree.column("В", width=60)
        self.history_tree.column("Результат", width=100)

        self.history_tree.pack(fill="both", expand=True, pady=(0, 10))

        # Кнопки управления историей
        history_buttons = ttk.Frame(history_frame)
        history_buttons.pack(fill="x")

        ttk.Button(history_buttons, text="Очистить историю",
                  command=self._clear_history).pack(side="left", padx=(0, 10))
        ttk.Button(history_buttons, text="Экспорт в JSON",
                  command=self._export_history).pack(side="left")

        # Статус бар
        self.status_label = ttk.Label(main_frame, text="Готов к работе",
                                      font=('Arial', 9), foreground="gray")
        self.status_label.pack(pady=(10, 0))


    def _load_api_key(self):
        """Загрузка API ключа."""
        try:
            with open("api_key.txt", "r") as f:
                self.api_key = f.read().strip()
        except FileNotFoundError:
            # Создаем файл с инструкцией
            with open("api_key.txt", "w") as f:
                f.write("ВСТАВЬТЕ_ВАШ_API_КЛЮЧ_СЮДА")

            # Запрашиваем ключ
            self.api_key = self._ask_api_key()

            if self.api_key:
                with open("api_key.txt", "w") as f:
                    f.write(self.api_key)


    def _ask_api_key(self):
        """Запрос API ключа у пользователя."""
        dialog = tk.Toplevel(self.root)
        dialog.title("API Ключ")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Введите API ключ с exchangerate-api.com",
                 font=('Arial', 11)).pack(pady=20)
        ttk.Label(dialog, text="(или оставьте пустым для демо-режима)",
                 font=('Arial', 9), foreground="gray").pack()

        entry = ttk.Entry(dialog, font=('Arial', 12), width=40)
        entry.pack(pady=20)
        entry.focus()

        result = []

        def submit():
            result.append(entry.get().strip())
            dialog.destroy()

        ttk.Button(dialog, text="OK", command=submit).pack()
        dialog.wait_window()

        return result[0] if result else ""


    def _load_rates(self):
        """Загрузка курсов валют."""
        if not self.api_key:
            self.status_label.config(text="⚠️ API ключ не указан, используем демо-режим")
            self._load_demo_rates()
            return

        try:
            url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/USD"
            response = requests.get(url, timeout=10)
            data = response.json()

            if data["result"] == "success":
                self.current_rates = data["conversion_rates"]
                self._update_rates_table()
                self.status_label.config(text="✅ Курсы обновлены")
            else:
                self.status_label.config(text="❌ Ошибка API, используем демо-режим")
                self._load_demo_rates()

        except Exception:
            self.status_label.config(text="❌ Нет подключения, используем демо-режим")
            self._load_demo_rates()


    def _load_demo_rates(self):
        """Загрузка демо-курсов для офлайн режима."""
        self.current_rates = {
            "USD": 1.0, "EUR": 0.85, "RUB": 75.0, "GBP": 0.73,
            "JPY": 110.0, "CNY": 6.45, "CHF": 0.92, "CAD": 1.25,
            "AUD": 1.35, "KZT": 425.0, "UAH": 27.5, "BYN": 2.55
        }
        self._update_rates_table()


    def _update_rates_table(self):
        """Обновление таблицы курсов."""
        for row in self.rates_tree.get_children():
            self.rates_tree.delete(row)

        for currency in self.CURRENCIES[:10]:
            if currency in self.current_rates:
                self.rates_tree.insert("", "end", values=(currency, f"{self.current_rates[currency]:.4f}"))


    def _swap_currencies(self):
        """Смена валют местами."""
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()
        self.from_currency.set(to_curr)
        self.to_currency.set(from_curr)


    def _convert(self):
        """Конвертация валюты."""
        amount_str = self.amount_entry.get().strip()

        # Валидация ввода
        if not amount_str:
            messagebox.showwarning("Ошибка", "Введите сумму!")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showwarning("Ошибка", "Сумма должна быть положительной!")
                return
        except ValueError:
            messagebox.showwarning("Ошибка", "Введите корректное число!")
            return

        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()

        if from_curr == to_curr:
            messagebox.showwarning("Ошибка", "Выберите разные валюты!")
            return

        # Конвертация
        if from_curr in self.current_rates and to_curr in self.current_rates:
            from_rate = self.current_rates[from_curr]
            to_rate = self.current_rates[to_curr]

            result = amount * (to_rate / from_rate)

            self.result_label.config(text=f"{amount:.2f} {from_curr} = {result:.2f} {to_curr}")

            # Сохранение в историю
            self._add_to_history(from_curr, to_curr, amount, result)
        else:
            messagebox.showwarning("Ошибка", "Выбранная валюта недоступна!")


    def _add_to_history(self, from_curr, to_curr, amount, result):
        """Добавление записи в историю."""
        date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

        record = {
            "date": date,
            "from": from_curr,
            "amount": amount,
            "to": to_curr,
            "result": result
        }

        self.history.append(record)
        self._save_history()
        self._update_history_table()


    def _update_history_table(self):
        """Обновление таблицы истории."""
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)

        for record in reversed(self.history):
            values = (
                record["date"],
                record["from"],
                f"{record['amount']:.2f}",
                record["to"],
                f"{record['result']:.2f}"
            )
            self.history_tree.insert("", "end", values=values)


    def _load_history(self):
        """Загрузка истории из JSON."""
        try:
            with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                self.history = json.load(f)
            self._update_history_table()
        except FileNotFoundError:
            self.history = []


    def _save_history(self):
        """Сохранение истории в JSON."""
        with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)


    def _clear_history(self):
        """Очистка истории."""
        if self.history and messagebox.askyesno("Подтверждение", "Очистить историю конвертаций?"):
            self.history.clear()
            self._update_history_table()
            self._save_history()
            self.status_label.config(text="🗑️ История очищена")


    def _export_history(self):
        """Экспорт истории в отдельный файл."""
        if not self.history:
            messagebox.showinfo("Информация", "История пуста!")
            return

        filename = f"export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

        self.status_label.config(text=f"📁 История экспортирована в {filename}")
        messagebox.showinfo("Успех", f"История сохранена в файл:\n{filename}")


def main():
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
