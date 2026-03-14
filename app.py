import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from dataclasses import dataclass
from typing import Optional

DB_FILE = "techstore.db"


@dataclass
class Session:
    user_id: Optional[int]
    login: str
    role: str


class Database:
    def __init__(self, db_path: str = DB_FILE):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()
        self._seed_data()

    def _create_schema(self) -> None:
        self.conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role_id INTEGER,
                FOREIGN KEY (role_id) REFERENCES roles(id)
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                brand TEXT,
                price REAL,
                power TEXT,
                photo TEXT,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                client_name TEXT,
                order_date TEXT,
                quantity INTEGER,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            """
        )
        self.conn.commit()

    def _seed_data(self) -> None:
        role_count = self.conn.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
        if role_count:
            return

        self.conn.executemany(
            "INSERT INTO roles(role_name) VALUES (?)",
            [("admin",), ("client",)],
        )

        self.conn.executemany(
            "INSERT INTO users(login, password, role_id) VALUES (?, ?, ?)",
            [
                ("admin", "admin123", 1),
                ("ivan", "123", 2),
                ("anna", "123", 2),
                ("sergey", "123", 2),
                ("olga", "123", 2),
            ],
        )

        self.conn.executemany(
            "INSERT INTO categories(name) VALUES (?)",
            [
                ("Холодильники",),
                ("Стиральные машины",),
                ("Телевизоры",),
                ("Микроволновые печи",),
                ("Пылесосы",),
            ],
        )

        self.conn.executemany(
            """
            INSERT INTO products(name, brand, price, power, photo, category_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("LG InstaView", "LG", 79990, "A++", "", 1),
                ("Samsung EcoBubble", "Samsung", 56990, "2200W", "", 2),
                ("Sony Bravia 55", "Sony", 99990, "150W", "", 3),
                ("Bosch Serie 4", "Bosch", 18990, "900W", "", 4),
                ("Dyson V11", "Dyson", 45990, "545W", "", 5),
            ],
        )

        self.conn.executemany(
            """
            INSERT INTO orders(product_id, client_name, order_date, quantity)
            VALUES (?, ?, ?, ?)
            """,
            [
                (1, "Иван", "2025-01-15", 1),
                (1, "Анна", "2025-02-11", 2),
                (3, "Сергей", "2025-02-24", 1),
                (5, "Ольга", "2025-03-02", 1),
            ],
        )
        self.conn.commit()

    def login(self, login: str, password: str) -> Optional[Session]:
        row = self.conn.execute(
            """
            SELECT u.id, u.login, r.role_name
            FROM users u
            JOIN roles r ON r.id = u.role_id
            WHERE u.login = ? AND u.password = ?
            """,
            (login, password),
        ).fetchone()
        if not row:
            return None
        return Session(user_id=row["id"], login=row["login"], role=row["role_name"])

    def categories(self):
        return self.conn.execute("SELECT id, name FROM categories ORDER BY name").fetchall()

    def products(self, category_id: Optional[int] = None, search: str = ""):
        sql = """
            SELECT p.*, c.name AS category_name
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE 1 = 1
        """
        params = []
        if category_id:
            sql += " AND p.category_id = ?"
            params.append(category_id)
        if search:
            sql += " AND p.name LIKE ?"
            params.append(f"%{search}%")
        sql += " ORDER BY p.name"
        return self.conn.execute(sql, params).fetchall()

    def orders_for_product(self, product_id: int):
        return self.conn.execute(
            """
            SELECT o.client_name, o.order_date, o.quantity, p.price,
                   (o.quantity * p.price) AS total
            FROM orders o
            JOIN products p ON p.id = o.product_id
            WHERE o.product_id = ?
            ORDER BY o.order_date DESC
            """,
            (product_id,),
        ).fetchall()

    def add_product(self, name, brand, price, power, photo, category_id):
        self.conn.execute(
            """
            INSERT INTO products(name, brand, price, power, photo, category_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, brand, price, power, photo, category_id),
        )
        self.conn.commit()

    def update_product(self, product_id, name, brand, price, power, photo, category_id):
        self.conn.execute(
            """
            UPDATE products
            SET name = ?, brand = ?, price = ?, power = ?, photo = ?, category_id = ?
            WHERE id = ?
            """,
            (name, brand, price, power, photo, category_id, product_id),
        )
        self.conn.commit()

    def delete_product(self, product_id):
        self.conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()


class ProductDialog(simpledialog.Dialog):
    def __init__(self, parent, title, categories, initial=None):
        self.categories = categories
        self.initial = initial
        self.result_data = None
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Название:").grid(row=0, column=0, sticky="w")
        ttk.Label(master, text="Бренд:").grid(row=1, column=0, sticky="w")
        ttk.Label(master, text="Цена:").grid(row=2, column=0, sticky="w")
        ttk.Label(master, text="Мощность:").grid(row=3, column=0, sticky="w")
        ttk.Label(master, text="Фото (путь):").grid(row=4, column=0, sticky="w")
        ttk.Label(master, text="Категория:").grid(row=5, column=0, sticky="w")

        self.name = ttk.Entry(master, width=42)
        self.brand = ttk.Entry(master, width=42)
        self.price = ttk.Entry(master, width=42)
        self.power = ttk.Entry(master, width=42)
        self.photo = ttk.Entry(master, width=42)
        self.category_var = tk.StringVar()
        self.category_cb = ttk.Combobox(
            master,
            width=39,
            textvariable=self.category_var,
            state="readonly",
            values=[f"{c['id']} - {c['name']}" for c in self.categories],
        )

        for row, widget in enumerate([self.name, self.brand, self.price, self.power, self.photo, self.category_cb]):
            widget.grid(row=row, column=1, padx=6, pady=4, sticky="ew")

        if self.initial:
            self.name.insert(0, self.initial["name"] or "")
            self.brand.insert(0, self.initial["brand"] or "")
            self.price.insert(0, str(self.initial["price"] or ""))
            self.power.insert(0, self.initial["power"] or "")
            self.photo.insert(0, self.initial["photo"] or "")
            self.category_var.set(f"{self.initial['category_id']} - {self.initial['category_name']}")

        return self.name

    def validate(self):
        try:
            price = float(self.price.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Цена должна быть числом.")
            return False

        if not self.name.get().strip():
            messagebox.showerror("Ошибка", "Название обязательно.")
            return False
        if not self.category_var.get():
            messagebox.showerror("Ошибка", "Выберите категорию.")
            return False

        category_id = int(self.category_var.get().split(" - ")[0])
        self.result_data = {
            "name": self.name.get().strip(),
            "brand": self.brand.get().strip(),
            "price": price,
            "power": self.power.get().strip(),
            "photo": self.photo.get().strip(),
            "category_id": category_id,
        }
        return True


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("TechStore — Авторизация")
        self.root.geometry("420x260")
        self.db = Database()
        self.session = None
        self.products_cache = []
        self.current_product = None
        self.image_ref = None

        default_font = ("Segoe UI", 10)
        self.root.option_add("*Font", default_font)

        self._build_login_screen()

    def _clear_root(self):
        for child in self.root.winfo_children():
            child.destroy()

    def _build_login_screen(self):
        self._clear_root()
        frame = ttk.Frame(self.root, padding=24)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Логин:").pack(anchor="w", pady=(0, 4))
        self.login_entry = ttk.Entry(frame)
        self.login_entry.pack(fill="x", pady=(0, 12))

        ttk.Label(frame, text="Пароль:").pack(anchor="w", pady=(0, 4))
        self.password_entry = ttk.Entry(frame, show="*")
        self.password_entry.pack(fill="x", pady=(0, 18))

        btns = ttk.Frame(frame)
        btns.pack(fill="x")
        ttk.Button(btns, text="Войти", command=self._auth).pack(side="left")
        ttk.Button(btns, text="Просмотр", command=self._guest_mode).pack(side="left", padx=8)

        self.login_entry.focus_set()

    def _auth(self):
        session = self.db.login(self.login_entry.get().strip(), self.password_entry.get().strip())
        if not session:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
            return
        self.session = session
        self._build_main_screen()

    def _guest_mode(self):
        self.session = Session(user_id=None, login="guest", role="guest")
        self._build_main_screen()

    def _build_main_screen(self):
        self._clear_root()
        self.root.title("TechStore — Главное окно")
        self.root.geometry("980x620")

        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text=f"Пользователь: {self.session.login} ({self.session.role})").pack(side="left")

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=self.search_var, width=34)
        search_entry.pack(side="right", padx=(8, 0))
        ttk.Label(top, text="Поиск:").pack(side="right")

        if self.session.role == "guest":
            search_entry.configure(state="disabled")
        else:
            self.search_var.trace_add("write", lambda *_: self._load_products())

        filter_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        filter_frame.pack(fill="x")
        ttk.Label(filter_frame, text="Категория:").pack(side="left")

        self.categories = self.db.categories()
        self.category_var = tk.StringVar(value="Все")
        self.category_combo = ttk.Combobox(
            filter_frame,
            state="readonly",
            textvariable=self.category_var,
            values=["Все"] + [c["name"] for c in self.categories],
            width=28,
        )
        self.category_combo.pack(side="left", padx=8)
        self.category_combo.bind("<<ComboboxSelected>>", lambda *_: self._load_products())

        content = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        content.pack(fill="both", expand=True)

        left = ttk.Frame(content)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="Товары:").pack(anchor="w")

        self.product_list = ttk.Treeview(left, columns=("brand", "price"), show="headings", height=22)
        self.product_list.heading("brand", text="Бренд")
        self.product_list.heading("price", text="Цена")
        self.product_list.column("brand", width=130)
        self.product_list.column("price", width=90)
        self.product_list.pack(fill="y", pady=6)
        self.product_list.bind("<<TreeviewSelect>>", self._on_select_product)

        right = ttk.Frame(content, padding=(18, 0, 0, 0))
        right.pack(side="left", fill="both", expand=True)

        self.photo_label = ttk.Label(right, text="[Фото]", anchor="center")
        self.photo_label.pack(fill="x", pady=(0, 10), ipady=65)

        self.name_label = ttk.Label(right, text="", font=("Segoe UI", 20, "bold"))
        self.name_label.pack(anchor="w", pady=(0, 8))

        self.specs_label = ttk.Label(right, text="", justify="left")
        self.specs_label.pack(anchor="w", pady=(0, 12))

        self.orders_btn = ttk.Button(right, text="Показать заказы", command=self._show_orders)
        self.orders_btn.pack(anchor="w")

        if self.session.role == "admin":
            toolbar = ttk.Frame(self.root, padding=(10, 2, 10, 10))
            toolbar.pack(fill="x")
            ttk.Button(toolbar, text="Добавить", command=self._add_product).pack(side="left")
            ttk.Button(toolbar, text="Редактировать", command=self._edit_product).pack(side="left", padx=8)
            ttk.Button(toolbar, text="Удалить", command=self._delete_product).pack(side="left")

        self._load_products()

    def _selected_category_id(self) -> Optional[int]:
        selected = self.category_var.get()
        if selected == "Все":
            return None
        for c in self.categories:
            if c["name"] == selected:
                return c["id"]
        return None

    def _load_products(self):
        search_text = self.search_var.get().strip() if self.session.role != "guest" else ""
        self.products_cache = self.db.products(self._selected_category_id(), search_text)

        for row in self.product_list.get_children():
            self.product_list.delete(row)

        for p in self.products_cache:
            self.product_list.insert("", "end", iid=str(p["id"]), values=(p["brand"], f"{p['price']:.2f}"))

        if self.products_cache:
            self.product_list.selection_set(str(self.products_cache[0]["id"]))
            self._update_card(self.products_cache[0])
        else:
            self.current_product = None
            self.name_label.configure(text="")
            self.specs_label.configure(text="Товары не найдены")
            self.photo_label.configure(text="[Фото]", image="")

    def _on_select_product(self, _event):
        selected = self.product_list.selection()
        if not selected:
            return
        pid = int(selected[0])
        for product in self.products_cache:
            if product["id"] == pid:
                self._update_card(product)
                return

    def _update_card(self, product):
        self.current_product = product
        self.name_label.configure(text=product["name"])
        self.specs_label.configure(
            text=(
                f"Категория: {product['category_name'] or '-'}\n"
                f"Бренд: {product['brand'] or '-'}\n"
                f"Цена: {product['price']:.2f} д.е.\n"
                f"Мощность: {product['power'] or '-'}"
            )
        )
        self._load_product_image(product["photo"])

    def _load_product_image(self, photo_path: str):
        self.image_ref = None
        if photo_path and os.path.exists(photo_path):
            try:
                self.image_ref = tk.PhotoImage(file=photo_path)
                self.photo_label.configure(image=self.image_ref, text="")
                return
            except tk.TclError:
                pass

        self.photo_label.configure(image="", text="[Фото недоступно]")

    def _show_orders(self):
        if not self.current_product:
            return

        rows = self.db.orders_for_product(self.current_product["id"])
        win = tk.Toplevel(self.root)
        win.title(f"Заказы: {self.current_product['name']}")
        win.geometry("680x360")

        total_sum = sum(r["total"] for r in rows)
        ttk.Label(win, text=f"Общий итог: {total_sum:.2f} д.е.", font=("Segoe UI", 11, "bold")).pack(
            anchor="w", padx=10, pady=10
        )

        table = ttk.Treeview(win, columns=("client", "date", "qty", "total"), show="headings")
        table.heading("client", text="Клиент")
        table.heading("date", text="Дата")
        table.heading("qty", text="Количество")
        table.heading("total", text="Стоимость")
        table.column("client", width=180)
        table.column("date", width=140)
        table.column("qty", width=120)
        table.column("total", width=150)
        table.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        for r in rows:
            table.insert("", "end", values=(r["client_name"], r["order_date"], r["quantity"], f"{r['total']:.2f}"))

    def _add_product(self):
        dialog = ProductDialog(self.root, "Добавить товар", self.categories)
        if dialog.result_data:
            self.db.add_product(**dialog.result_data)
            self._load_products()

    def _edit_product(self):
        if not self.current_product:
            messagebox.showwarning("Внимание", "Сначала выберите товар.")
            return

        dialog = ProductDialog(
            self.root,
            "Редактировать товар",
            self.categories,
            initial=self.current_product,
        )
        if dialog.result_data:
            self.db.update_product(self.current_product["id"], **dialog.result_data)
            self._load_products()

    def _delete_product(self):
        if not self.current_product:
            messagebox.showwarning("Внимание", "Сначала выберите товар.")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранный товар?"):
            return
        self.db.delete_product(self.current_product["id"])
        self._load_products()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
