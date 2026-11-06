import math
import sqlite3
import tkinter as tk
from tkinter import messagebox

import database


class AGZSApp:
    """Графічний інтерфейс системи АГЗС із даними в SQLite."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("АВТОМАТИЗОВАНА СИСТЕМА АГЗС (SQLite)")
        self.root.geometry("820x660")
        self.root.minsize(720, 580)
        self.current_operator_id = 101
        self.displayed_fuels: list[tuple] = []

        self.create_widgets()
        self.load_fuels_from_db()

    def create_widgets(self) -> None:
        header = tk.Frame(self.root, bg="#1E3A8A")
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="АВТОМАТИЗОВАНА СИСТЕМА АГЗС ДЛЯ ЗАПРАВНИКІВ",
            font=("Arial", 13, "bold"),
            fg="white",
            bg="#1E3A8A",
            pady=8,
        ).pack(side=tk.LEFT, padx=15)
        tk.Button(
            header,
            text="Про програму",
            command=self.on_show_info,
            bg="#3B82F6",
            fg="white",
        ).pack(side=tk.RIGHT, padx=15, pady=5)

        search_frame = tk.Frame(self.root, padx=10, pady=5)
        search_frame.pack(fill=tk.X)
        tk.Label(search_frame, text="Пошук пального:").pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(
            search_frame, text="Знайти", command=self.on_search, bg="#EAB308"
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            search_frame, text="Скинути", command=self.load_fuels_from_db
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            search_frame, text="Історія заправок", command=self.on_show_orders
        ).pack(side=tk.RIGHT, padx=5)

        content = tk.Frame(self.root, padx=10, pady=5)
        content.pack(fill=tk.BOTH, expand=True)
        list_frame = tk.LabelFrame(content, text=" Резервуари з пальним ")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.fuel_listbox = tk.Listbox(
            list_frame, font=("Consolas", 10), selectmode=tk.SINGLE
        )
        self.fuel_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.fuel_listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.fuel_listbox.config(yscrollcommand=scrollbar.set)

        details = tk.LabelFrame(content, text=" Інформація та відпуск пального ")
        details.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.info_text = tk.Text(
            details, height=7, width=32, state=tk.DISABLED, bg="#F3F4F6"
        )
        self.info_text.pack(fill=tk.X, padx=8, pady=5)
        tk.Button(
            details,
            text="Показати деталі",
            command=self.on_select_fuel,
            bg="#2563EB",
            fg="white",
        ).pack(fill=tk.X, padx=8, pady=2)

        refuel_frame = tk.Frame(details, padx=8, pady=5)
        refuel_frame.pack(fill=tk.X)
        tk.Label(refuel_frame, text="Об'єм заправки (л):").pack(side=tk.LEFT)
        self.liters_entry = tk.Entry(refuel_frame, width=10)
        self.liters_entry.insert(0, "30.0")
        self.liters_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(
            details,
            text="Здійснити заправку",
            command=self.on_process_refueling,
            bg="#16A34A",
            fg="white",
        ).pack(fill=tk.X, padx=8, pady=2)

        edit_frame = tk.LabelFrame(details, text=" Редагування ціни та залишку ")
        edit_frame.pack(fill=tk.X, padx=8, pady=5)
        tk.Label(edit_frame, text="Ціна:").grid(row=0, column=0, padx=3)
        self.edit_price_entry = tk.Entry(edit_frame, width=9)
        self.edit_price_entry.grid(row=0, column=1, padx=3)
        tk.Label(edit_frame, text="Залишок:").grid(row=0, column=2, padx=3)
        self.edit_stock_entry = tk.Entry(edit_frame, width=9)
        self.edit_stock_entry.grid(row=0, column=3, padx=3)
        tk.Button(
            edit_frame,
            text="Зберегти",
            command=self.on_edit_fuel,
            bg="#D97706",
            fg="white",
        ).grid(row=0, column=4, padx=4)

        add_frame = tk.LabelFrame(
            self.root, text=" Додавання нового виду пального ", padx=8, pady=5
        )
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(add_frame, text="ID:").grid(row=0, column=0, sticky=tk.E)
        self.entry_id = tk.Entry(add_frame, width=7)
        self.entry_id.grid(row=0, column=1, padx=4, pady=2)
        tk.Label(add_frame, text="Назва:").grid(row=0, column=2, sticky=tk.E)
        self.entry_name = tk.Entry(add_frame, width=22)
        self.entry_name.grid(row=0, column=3, padx=4, pady=2)
        tk.Label(add_frame, text="Ціна (грн/л):").grid(
            row=1, column=0, sticky=tk.E
        )
        self.entry_price = tk.Entry(add_frame, width=7)
        self.entry_price.grid(row=1, column=1, padx=4, pady=2)
        tk.Label(add_frame, text="Залишок (л):").grid(
            row=1, column=2, sticky=tk.E
        )
        self.entry_stock = tk.Entry(add_frame, width=22)
        self.entry_stock.grid(row=1, column=3, padx=4, pady=2)
        tk.Button(
            add_frame,
            text="Додати",
            command=self.on_add_fuel,
            bg="#0D9488",
            fg="white",
        ).grid(row=0, column=4, rowspan=2, padx=8, sticky="nsew")

        controls = tk.Frame(self.root, padx=10, pady=5)
        controls.pack(fill=tk.X)
        tk.Button(
            controls,
            text="Видалити вибране",
            command=self.on_delete_fuel,
            bg="#DC2626",
            fg="white",
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            controls, text="Очистити все", command=self.on_clear_all
        ).pack(side=tk.LEFT, padx=5)
        self.lbl_count = tk.Label(controls, text="Всього позицій: 0")
        self.lbl_count.pack(side=tk.LEFT, padx=15)
        self.lbl_summary = tk.Label(
            controls,
            text="Загальна вартість: 0.00 грн",
            font=("Arial", 10, "bold"),
            fg="#1E3A8A",
        )
        self.lbl_summary.pack(side=tk.RIGHT, padx=5)

    def load_fuels_from_db(self, custom_list: list[tuple] | None = None) -> None:
        """Завантажує пальне з БД та оновлює список і підсумок."""
        all_fuels = database.get_fuels()
        fuels_to_show = all_fuels if custom_list is None else custom_list
        self.displayed_fuels = list(fuels_to_show)
        self.fuel_listbox.delete(0, tk.END)
        for fuel_id, name, price, stock, _ in self.displayed_fuels:
            self.fuel_listbox.insert(
                tk.END, f"[{fuel_id}] {name} — {price:.2f} грн/л ({stock:.1f} л)"
            )

        total_value = sum(price * stock for _, _, price, stock, _ in all_fuels)
        self.lbl_summary.config(
            text=f"Загальна вартість: {total_value:,.2f} грн"
        )
        self.lbl_count.config(text=f"Всього позицій: {len(self.displayed_fuels)}")

    def get_selected_fuel(self) -> tuple | None:
        """Повертає запис пального, вибраний у поточному списку."""
        selection = self.fuel_listbox.curselection()
        if not selection:
            messagebox.showwarning(
                "Увага", "Будь ласка, оберіть позицію пального зі списку!"
            )
            return None
        index = selection[0]
        if index >= len(self.displayed_fuels):
            messagebox.showerror(
                "Помилка", "Не вдалося визначити вибрану позицію пального."
            )
            return None
        return self.displayed_fuels[index]

    def show_fuel_details(self, fuel: tuple) -> None:
        fuel_id, name, price, stock, status = fuel
        details = (
            f"ID пального: {fuel_id}\n"
            f"Марка пального: {name}\n"
            f"Ціна за літр: {price:.2f} грн\n"
            f"Залишок у резервуарі: {stock:.1f} л\n"
            f"Статус запасу: {status}"
        )
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, details)
        self.info_text.config(state=tk.DISABLED)
        self.edit_price_entry.delete(0, tk.END)
        self.edit_price_entry.insert(0, str(price))
        self.edit_stock_entry.delete(0, tk.END)
        self.edit_stock_entry.insert(0, str(stock))

    def clear_fuel_details(self) -> None:
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.config(state=tk.DISABLED)
        self.edit_price_entry.delete(0, tk.END)
        self.edit_stock_entry.delete(0, tk.END)

    def on_select_fuel(self) -> None:
        fuel = self.get_selected_fuel()
        if fuel is not None:
            self.show_fuel_details(fuel)

    def on_process_refueling(self) -> None:
        fuel = self.get_selected_fuel()
        if fuel is None:
            return
        fuel_id, name, price = fuel[:3]
        try:
            liters = float(self.liters_entry.get().strip())
            if not math.isfinite(liters) or liters <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Помилка", "Введіть коректний додатний об'єм заправки!"
            )
            return

        total_price = round(liters * price, 2)
        try:
            order_id = database.create_refueling_transaction(
                fuel_id, self.current_operator_id, liters, total_price
            )
        except sqlite3.Error as error:
            messagebox.showerror(
                "Помилка бази даних", f"Не вдалося зберегти заправку:\n{error}"
            )
            return
        if order_id is None:
            messagebox.showerror(
                "Помилка заправки",
                "Недостатньо пального або позиція більше не існує. "
                "Оновіть список і спробуйте ще раз.",
            )
            self.load_fuels_from_db()
            return

        messagebox.showinfo(
            "Чек заправки",
            f"Заправку №{order_id} проведено та збережено в БД!\n"
            f"Пальне: {name}\nОб'єм: {liters:.1f} л\n"
            f"До сплати: {total_price:.2f} грн",
        )
        self.load_fuels_from_db()
        updated_fuel = next(
            (item for item in self.displayed_fuels if item[0] == fuel_id), None
        )
        if updated_fuel is not None:
            self.show_fuel_details(updated_fuel)

    def on_edit_fuel(self) -> None:
        fuel = self.get_selected_fuel()
        if fuel is None:
            return
        fuel_id = fuel[0]
        try:
            price = float(self.edit_price_entry.get().strip())
            stock = float(self.edit_stock_entry.get().strip())
            if (
                not math.isfinite(price)
                or not math.isfinite(stock)
                or price <= 0
                or stock < 0
            ):
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Помилка", "Ціна має бути скінченною та > 0, залишок — >= 0."
            )
            return

        try:
            updated = database.update_fuel_price_stock(fuel_id, price, stock)
        except (sqlite3.Error, ValueError) as error:
            messagebox.showerror("Помилка бази даних", str(error))
            return
        if not updated:
            messagebox.showerror(
                "Помилка", "Пальне не знайдено. Оновіть список."
            )
            self.load_fuels_from_db()
            return

        self.load_fuels_from_db()
        updated_fuel = next(
            (item for item in self.displayed_fuels if item[0] == fuel_id), None
        )
        if updated_fuel is not None:
            self.show_fuel_details(updated_fuel)
        messagebox.showinfo("Успіх", "Дані пального оновлено.")

    def on_add_fuel(self) -> None:
        name = self.entry_name.get().strip()
        try:
            fuel_id = int(self.entry_id.get().strip())
            price = float(self.entry_price.get().strip())
            stock = float(self.entry_stock.get().strip())
            if (
                fuel_id <= 0
                or not name
                or not math.isfinite(price)
                or not math.isfinite(stock)
                or price <= 0
                or stock < 0
            ):
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Помилка введення",
                "Вкажіть ID > 0, непорожню назву, ціну > 0 "
                "та залишок >= 0.",
            )
            return

        try:
            added = database.add_fuel(fuel_id, name, price, stock)
        except (sqlite3.Error, ValueError) as error:
            messagebox.showerror("Помилка бази даних", str(error))
            return
        if not added:
            messagebox.showerror(
                "Помилка", f"Пальне з ID {fuel_id} вже існує!"
            )
            return

        self.load_fuels_from_db()
        for entry in (
            self.entry_id,
            self.entry_name,
            self.entry_price,
            self.entry_stock,
        ):
            entry.delete(0, tk.END)
        messagebox.showinfo("Успіх", f"Пальне '{name}' додано.")

    def on_delete_fuel(self) -> None:
        fuel = self.get_selected_fuel()
        if fuel is None:
            return
        if not messagebox.askyesno(
            "Підтвердження",
            f"Видалити '{fuel[1]}'? Пов'язані записи заправок також буде видалено.",
        ):
            return
        try:
            deleted = database.delete_fuel(fuel[0])
        except sqlite3.Error as error:
            messagebox.showerror("Помилка бази даних", str(error))
            return
        if not deleted:
            messagebox.showerror("Помилка", "Пальне більше не існує.")
        self.load_fuels_from_db()
        self.clear_fuel_details()

    def on_clear_all(self) -> None:
        if not messagebox.askyesno(
            "Підтвердження очищення",
            "Видалити всі позиції пального та пов'язані записи заправок?",
        ):
            return
        try:
            database.delete_all_fuels()
        except sqlite3.Error as error:
            messagebox.showerror("Помилка бази даних", str(error))
            return
        self.load_fuels_from_db()
        self.clear_fuel_details()

    def on_search(self) -> None:
        query = self.search_entry.get().strip()
        if not query:
            self.load_fuels_from_db()
            return
        try:
            found = database.search_fuels(query)
        except sqlite3.Error as error:
            messagebox.showerror("Помилка бази даних", str(error))
            return
        self.load_fuels_from_db(custom_list=found)

    def on_show_orders(self) -> None:
        try:
            orders = database.get_refueling_orders_joined()
        except sqlite3.Error as error:
            messagebox.showerror("Помилка бази даних", str(error))
            return

        window = tk.Toplevel(self.root)
        window.title("Історія заправок")
        window.geometry("760x320")
        text = tk.Text(window, wrap=tk.NONE)
        text.pack(fill=tk.BOTH, expand=True)
        if not orders:
            text.insert(tk.END, "Записів про заправки ще немає.")
        else:
            text.insert(
                tk.END,
                f"{'№':<6} {'Пальне':<30} {'Заправник':<24} "
                f"{'Літри':>9} {'Сума, грн':>12} {'Дата'}\n",
            )
            text.insert(tk.END, "-" * 110 + "\n")
            for order_id, fuel_name, refueler_name, liters, total, date in orders:
                text.insert(
                    tk.END,
                    f"{order_id:<6} {fuel_name:<30} {refueler_name:<24} "
                    f"{liters:>9.1f} {total:>12.2f} {date}\n",
                )
        text.config(state=tk.DISABLED)

    def on_show_info(self) -> None:
        messagebox.showinfo(
            "Про програму",
            "Автоматизована система АГЗС\n"
            "Облік пального та запис заправок у базі SQLite.",
        )


def main() -> None:
    root = tk.Tk()
    try:
        database.create_tables()
        database.add_initial_data()
        AGZSApp(root)
    except sqlite3.Error as error:
        messagebox.showerror(
            "Помилка бази даних",
            f"Не вдалося ініціалізувати базу даних:\n{error}",
            parent=root,
        )
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()