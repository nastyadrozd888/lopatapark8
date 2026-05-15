import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DB_NAME = "lopata.db"

def get_table_columns(table_name):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()
        return columns
    except:
        return []


class Database:
    def get_connection():
        return sqlite3.connect(DB_NAME)

    def get_user_id():
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users LIMIT 1")
        user = cursor.fetchone()
        conn.close()

        if user:
            return user[0]
        else:
            conn = Database.get_connection()
            cursor = conn.cursor()
            columns = get_table_columns('users')

            if 'name' in columns:
                cursor.execute("INSERT INTO users (name, email) VALUES ('Гость', 'guest@park.ru')")
            elif 'username' in columns:
                cursor.execute("INSERT INTO users (username, email) VALUES ('Гость', 'guest@park.ru')")
            else:
                cursor.execute("INSERT INTO users (email) VALUES ('guest@park.ru')")

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id

    def get_all_products():
        conn = Database.get_connection()
        cursor = conn.cursor()
        products = []
        try:
            columns = get_table_columns('products')
            print(f"Колонки products: {columns}")

            stock_field = None
            for field in ['in_stock', 'stock', 'quantity', 'count']:
                if field in columns:
                    stock_field = field
                    break

            if stock_field:
                cursor.execute(f"SELECT id, name, price, {stock_field} FROM products")
            else:
                cursor.execute("SELECT id, name, price FROM products")

            products = cursor.fetchall()
            print(f"Найдено товаров: {len(products)}")
        except Exception as e:
            print(f"Ошибка загрузки товаров: {e}")
        conn.close()
        return products

    def update_stock(product_id, quantity):
        conn = Database.get_connection()
        cursor = conn.cursor()
        columns = get_table_columns('products')

        for field in ['in_stock', 'stock', 'quantity', 'count']:
            if field in columns:
                cursor.execute(f"UPDATE products SET {field} = {field} - ? WHERE id=?", (quantity, product_id))
                break
        conn.commit()
        conn.close()

    def create_order(user_id, total_amount):
        conn = Database.get_connection()
        cursor = conn.cursor()
        columns = get_table_columns('orders')

        insert_fields = ['user_id']
        placeholders = ['?']
        values = [user_id]

        for field in ['total_amount', 'amount', 'total', 'sum', 'price']:
            if field in columns:
                insert_fields.append(field)
                placeholders.append('?')
                values.append(total_amount)
                break

        for field in ['created_at', 'date', 'order_date', 'datetime', 'timestamp']:
            if field in columns:
                insert_fields.append(field)
                placeholders.append('?')
                values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                break

        if 'status' in columns:
            insert_fields.append('status')
            placeholders.append('?')
            values.append('pending')

        query = f"INSERT INTO orders ({', '.join(insert_fields)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(query, values)
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id

    def get_all_orders():
        conn = Database.get_connection()
        cursor = conn.cursor()
        orders = []
        try:
            orders_columns = get_table_columns('orders')
            users_columns = get_table_columns('users')

            name_field = 'name'
            for field in ['name', 'username', 'full_name']:
                if field in users_columns:
                    name_field = field
                    break

            amount_field = None
            for field in ['total_amount', 'amount', 'total', 'sum', 'price']:
                if field in orders_columns:
                    amount_field = field
                    break

            date_field = None
            for field in ['created_at', 'date', 'order_date', 'datetime']:
                if field in orders_columns:
                    date_field = field
                    break

            select_fields = ['orders.id', f'users.{name_field} as user_name']
            if amount_field:
                select_fields.append(f'orders.{amount_field}')
            if date_field:
                select_fields.append(f'orders.{date_field}')

            query = f"SELECT {', '.join(select_fields)} FROM orders JOIN users ON orders.user_id = users.id ORDER BY orders.id DESC"
            cursor.execute(query)
            orders = cursor.fetchall()
        except Exception as e:
            print(f"Ошибка загрузки заказов: {e}")
        conn.close()
        return orders

    def add_order_item(order_id, product_id, quantity, price):
        conn = Database.get_connection()
        cursor = conn.cursor()
        columns = get_table_columns('order_items')

        insert_fields = ['order_id', 'product_id', 'quantity']
        placeholders = ['?', '?', '?']
        values = [order_id, product_id, quantity]

        if 'price_at_order' in columns:
            insert_fields.append('price_at_order')
            placeholders.append('?')
            values.append(price)
        elif 'price' in columns:
            insert_fields.append('price')
            placeholders.append('?')
            values.append(price)
        elif 'unit_price' in columns:
            insert_fields.append('unit_price')
            placeholders.append('?')
            values.append(price)

        for field in ['total', 'total_price', 'sum']:
            if field in columns:
                insert_fields.append(field)
                placeholders.append('?')
                values.append(quantity * price)
                break

        query = f"INSERT INTO order_items ({', '.join(insert_fields)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(query, values)
        conn.commit()
        conn.close()

    def get_order_items(order_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        items = []
        try:
            columns = get_table_columns('order_items')

            price_field = None
            for field in ['price_at_order', 'price', 'unit_price']:
                if field in columns:
                    price_field = field
                    break

            if price_field:
                cursor.execute(f'''
                    SELECT order_items.id, products.name, order_items.quantity, order_items.{price_field}
                    FROM order_items
                    JOIN products ON order_items.product_id = products.id
                    WHERE order_items.order_id=?
                ''', (order_id,))
            else:
                cursor.execute('''
                    SELECT order_items.id, products.name, order_items.quantity
                    FROM order_items
                    JOIN products ON order_items.product_id = products.id
                    WHERE order_items.order_id=?
                ''', (order_id,))
            items = cursor.fetchall()
        except Exception as e:
            print(f"Ошибка загрузки деталей заказа: {e}")
        conn.close()
        return items

    def get_waiting_list():
        conn = Database.get_connection()
        cursor = conn.cursor()
        waiting = []
        try:
            cursor.execute('''
                SELECT waiting_list.id, products.name, users.name, 
                       waiting_list.quantity, waiting_list.queue_number, waiting_list.status
                FROM waiting_list
                LEFT JOIN products ON waiting_list.product_id = products.id
                LEFT JOIN users ON waiting_list.user_id = users.id
                ORDER BY waiting_list.queue_number
            ''')
            waiting = cursor.fetchall()
        except Exception as e:
            print(f"Ошибка загрузки листа ожидания: {e}")
        conn.close()
        return waiting

    def add_to_waiting_list(product_id, visitor_name, quantity, user_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MAX(queue_number) FROM waiting_list")
            max_queue = cursor.fetchone()[0]
            queue_number = (max_queue or 0) + 1

            cursor.execute('''
                INSERT INTO waiting_list (user_id, product_id, quantity, queue_number, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, product_id, quantity, queue_number, 'ожидание', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            conn.commit()
            return queue_number
        except Exception as e:
            print(f"Ошибка добавления в лист ожидания: {e}")
            return None
        finally:
            conn.close()

    def delete_from_waiting(waiting_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM waiting_list WHERE id = ?", (waiting_id,))
        conn.commit()
        conn.close()

class ParkShop:
    def __init__(self, root):
        self.root = root
        self.root.title("🎡 Парк аттракционов 'Качели' - Интернет-магазин")
        self.root.geometry("1300x750")

        self.colors = {
            'bg': '#0a0a0a',
            'fg': '#ffffff',
            'accent': '#e63946',
            'button_bg': '#e63946',
            'button_fg': '#ffffff',
            'frame_bg': '#1a1a1a',
            'header_bg': '#8b0000',
        }

        self.root.configure(bg=self.colors['bg'])

        self.cart = {}
        self.current_user_id = Database.get_user_id()

        self.setup_styles()
        self.create_header()
        self.create_main_content()

        self.load_products()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TNotebook', background=self.colors['bg'])
        style.configure('TNotebook.Tab', background=self.colors['frame_bg'], foreground=self.colors['fg'],
                        padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', self.colors['accent'])])
        style.configure('Treeview', background=self.colors['frame_bg'], foreground=self.colors['fg'],
                        fieldbackground=self.colors['frame_bg'])
        style.configure('Treeview.Heading', background=self.colors['accent'], foreground='white',
                        font=('Arial', 10, 'bold'))

    def create_header(self):
        header = tk.Frame(self.root, bg=self.colors['header_bg'], height=90)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        left_frame = tk.Frame(header, bg=self.colors['header_bg'])
        left_frame.pack(side=tk.LEFT, padx=20, pady=15)

        logo = tk.Label(left_frame, text="🎡 ПАРК 'КАЧЕЛИ' 🎢",
                        font=("Arial", 26, "bold"),
                        bg=self.colors['header_bg'],
                        fg='white')
        logo.pack()

        slogan = tk.Label(left_frame, text="Магазин аттракционов и сувениров",
                          font=("Arial", 11),
                          bg=self.colors['header_bg'],
                          fg='#ffcccc')
        slogan.pack()

        right_frame = tk.Frame(header, bg=self.colors['header_bg'])
        right_frame.pack(side=tk.RIGHT, padx=20)

        self.cart_btn = tk.Button(right_frame, text="🛒 КОРЗИНА (0)",
                                  command=self.show_cart,
                                  bg='white',
                                  fg=self.colors['accent'],
                                  font=("Arial", 13, "bold"),
                                  cursor="hand2",
                                  padx=20,
                                  pady=8,
                                  relief=tk.RAISED,
                                  bd=2)
        self.cart_btn.pack(pady=20)

    def create_main_content(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.shop_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.shop_frame, text="🛍️  МАГАЗИН АТТРАКЦИОНОВ")
        self.setup_shop_tab()

        self.orders_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.orders_frame, text="📦  МОИ ЗАКАЗЫ")
        self.setup_orders_tab()

        self.waiting_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.waiting_frame, text="⏳  ЛИСТ ОЖИДАНИЯ")
        self.setup_waiting_tab()

    def setup_shop_tab(self):
        search_frame = tk.Frame(self.shop_frame, bg=self.colors['bg'])
        search_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(search_frame, text="🔍 ПОИСК:", bg=self.colors['bg'], fg=self.colors['fg'],
                 font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, width=30, bg=self.colors['frame_bg'],
                                     fg=self.colors['fg'], font=("Arial", 11),
                                     insertbackground='white')
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.search_products)

        tk.Button(search_frame, text="СБРОСИТЬ",
                  command=self.reset_search,
                  bg=self.colors['frame_bg'],
                  fg=self.colors['fg'],
                  font=("Arial", 10),
                  cursor="hand2").pack(side=tk.LEFT, padx=10)

        columns = ("ID", "Название", "Цена (руб)", "В наличии")
        self.product_tree = ttk.Treeview(self.shop_frame, columns=columns, show="headings", height=18)

        self.product_tree.heading("ID", text="ID")
        self.product_tree.heading("Название", text="Название")
        self.product_tree.heading("Цена (руб)", text="Цена (руб)")
        self.product_tree.heading("В наличии", text="В наличии")

        self.product_tree.column("ID", width=50, anchor='center')
        self.product_tree.column("Название", width=350)
        self.product_tree.column("Цена (руб)", width=120, anchor='center')
        self.product_tree.column("В наличии", width=100, anchor='center')

        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=10)

        scrollbar = ttk.Scrollbar(self.shop_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.product_tree.configure(yscrollcommand=scrollbar.set)

        control_frame = tk.Frame(self.shop_frame, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, padx=15, pady=15)

        add_btn = tk.Button(control_frame, text="➕ ДОБАВИТЬ В КОРЗИНУ",
                            command=self.add_to_cart,
                            bg=self.colors['button_bg'],
                            fg='white',
                            font=("Arial", 13, "bold"),
                            cursor="hand2",
                            padx=20,
                            pady=8,
                            relief=tk.RAISED)
        add_btn.pack(side=tk.LEFT, padx=5)

        refresh_btn = tk.Button(control_frame, text="🔄 ОБНОВИТЬ СПИСОК",
                                command=self.load_products,
                                bg=self.colors['frame_bg'],
                                fg=self.colors['fg'],
                                font=("Arial", 12),
                                cursor="hand2",
                                padx=15,
                                pady=8)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        self.info_label = tk.Label(control_frame, text="", bg=self.colors['bg'], fg=self.colors['accent'])
        self.info_label.pack(side=tk.RIGHT, padx=10)

    def setup_orders_tab(self):
        columns = ("ID", "Покупатель", "Сумма", "Дата")
        self.orders_tree = ttk.Treeview(self.orders_frame, columns=columns, show="headings", height=12)

        for col, width in zip(columns, [80, 200, 120, 180]):
            self.orders_tree.heading(col, text=col)
            self.orders_tree.column(col, width=width)

        self.orders_tree.pack(fill=tk.X, padx=15, pady=10)

        details_frame = tk.LabelFrame(self.orders_frame, text="📋 ДЕТАЛИ ЗАКАЗА",
                                      bg=self.colors['frame_bg'], fg=self.colors['accent'],
                                      font=("Arial", 12, "bold"))
        details_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.order_details = tk.Text(details_frame, height=10,
                                     bg=self.colors['bg'],
                                     fg=self.colors['fg'],
                                     wrap=tk.WORD,
                                     font=("Courier", 10),
                                     insertbackground='white')
        self.order_details.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = tk.Frame(self.orders_frame, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Button(btn_frame, text="🔍 ПОКАЗАТЬ ДЕТАЛИ", command=self.show_order_details,
                  bg=self.colors['button_bg'], fg='white', font=("Arial", 11, "bold"),
                  cursor="hand2", padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="🔄 ОБНОВИТЬ ЗАКАЗЫ", command=self.load_orders,
                  bg=self.colors['frame_bg'], fg=self.colors['fg'], font=("Arial", 11),
                  cursor="hand2", padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        self.load_orders()

    def setup_waiting_tab(self):
        columns = ("ID", "Товар", "Покупатель", "Кол-во", "№ очереди", "Статус")
        self.waiting_tree = ttk.Treeview(self.waiting_frame, columns=columns, show="headings", height=15)

        widths = [50, 200, 150, 70, 80, 100]
        for col, width in zip(columns, widths):
            self.waiting_tree.heading(col, text=col)
            self.waiting_tree.column(col, width=width)

        self.waiting_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        btn_frame = tk.Frame(self.waiting_frame, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Button(btn_frame, text="🔄 ОБНОВИТЬ", command=self.load_waiting_list,
                  bg=self.colors['frame_bg'], fg=self.colors['fg'], font=("Arial", 11),
                  cursor="hand2", padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="❌ УДАЛИТЬ", command=self.remove_from_waiting,
                  bg='#c62828', fg='white', font=("Arial", 11),
                  cursor="hand2", padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        self.load_waiting_list()

    def load_products(self, search_term=""):
        for row in self.product_tree.get_children():
            self.product_tree.delete(row)

        products = Database.get_all_products()

        if not products:
            self.product_tree.insert("", tk.END, values=("", "❌ ТОВАРЫ НЕ НАЙДЕНЫ", "", ""))
            return

        count = 0
        for product in products:
            name = str(product[1]) if len(product) > 1 and product[1] else ""
            if search_term and search_term.lower() not in name.lower():
                continue

            values = list(product)
            while len(values) < 4:
                values.append("")

            item_id = self.product_tree.insert("", tk.END, values=values)

            if len(product) > 3 and product[3] == 0:
                self.product_tree.tag_configure('outofstock', foreground='#888888')
                self.product_tree.item(item_id, tags=('outofstock',))

            count += 1

        self.info_label.config(text=f"📊 Товаров: {count}")

    def search_products(self, event=None):
        self.load_products(self.search_entry.get())

    def reset_search(self):
        self.search_entry.delete(0, tk.END)
        self.load_products()

    def add_to_cart(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "❌ Выберите товар")
            return

        item = self.product_tree.item(selected[0])['values']
        if len(item) < 3 or not item[0]:
            messagebox.showwarning("Ошибка", "❌ Товар не выбран")
            return

        product_id = item[0]
        product_name = item[1]
        in_stock = item[3] if len(item) > 3 else 0

        try:
            price = float(item[2]) if item[2] else 0
        except:
            price = 0

        if in_stock == 0:
            answer = messagebox.askyesno(
                "❌ Товара нет в наличии",
                f"Товар '{product_name}' отсутствует на складе.\n\n"
                f"Хотите добавить его в ЛИСТ ОЖИДАНИЯ?\n"
                f"Когда товар появится, мы вас уведомим."
            )
            if answer:
                self.add_to_waiting_list_from_shop(product_id, product_name)
            return

        qty_window = tk.Toplevel(self.root)
        qty_window.title("Количество")
        qty_window.geometry("350x250")
        qty_window.configure(bg=self.colors['bg'])
        qty_window.transient(self.root)
        qty_window.grab_set()

        tk.Label(qty_window, text="🛒 ДОБАВЛЕНИЕ В КОРЗИНУ",
                 font=("Arial", 14, "bold"),
                 bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=10)

        tk.Label(qty_window, text=f"{product_name}",
                 bg=self.colors['bg'], fg=self.colors['fg'], font=("Arial", 12)).pack(pady=5)
        tk.Label(qty_window, text=f"💰 Цена: {price} руб.",
                 bg=self.colors['bg'], fg=self.colors['fg']).pack()
        tk.Label(qty_window, text=f"📦 В наличии: {in_stock} шт.",
                 bg=self.colors['bg'], fg=self.colors['fg']).pack()

        tk.Label(qty_window, text="Количество:",
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=10)
        qty_entry = tk.Entry(qty_window, bg=self.colors['frame_bg'], fg=self.colors['fg'],
                             font=("Arial", 12), justify='center', width=10)
        qty_entry.pack()
        qty_entry.insert(0, "1")

        def add():
            try:
                qty = int(qty_entry.get())
                if qty <= 0:
                    raise ValueError
                if qty > in_stock:
                    messagebox.showerror("Ошибка", f"❌ Недостаточно товара! В наличии только {in_stock} шт.")
                    return

                if product_id in self.cart:
                    new_qty = self.cart[product_id]['quantity'] + qty
                    if new_qty > in_stock:
                        messagebox.showerror("Ошибка", f"❌ В корзине уже {self.cart[product_id]['quantity']} шт.")
                        return
                    self.cart[product_id]['quantity'] += qty
                else:
                    self.cart[product_id] = {
                        'name': product_name,
                        'quantity': qty,
                        'price': price,
                    }

                self.update_cart_display()
                qty_window.destroy()
                messagebox.showinfo("Успех", f"✅ {product_name} добавлен в корзину!")
            except ValueError:
                messagebox.showerror("Ошибка", "❌ Введите корректное количество")

        tk.Button(qty_window, text="ДОБАВИТЬ", command=add,
                  bg=self.colors['button_bg'], fg='white', font=("Arial", 12, "bold"),
                  cursor="hand2", padx=20, pady=8).pack(pady=15)

    def add_to_waiting_list_from_shop(self, product_id, product_name):

        name_window = tk.Toplevel(self.root)
        name_window.title("Лист ожидания")
        name_window.geometry("400x280")
        name_window.configure(bg=self.colors['bg'])
        name_window.transient(self.root)
        name_window.grab_set()

        tk.Label(name_window, text="📋 ДОБАВЛЕНИЕ В ЛИСТ ОЖИДАНИЯ",
                 font=("Arial", 14, "bold"),
                 bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=15)

        tk.Label(name_window, text=f"Товар: {product_name}",
                 bg=self.colors['bg'], fg=self.colors['fg'], font=("Arial", 12)).pack(pady=5)

        tk.Label(name_window, text="Ваше имя:",
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=10)

        name_entry = tk.Entry(name_window, width=30,
                              bg=self.colors['frame_bg'], fg=self.colors['fg'],
                              font=("Arial", 12))
        name_entry.pack(pady=5)

        tk.Label(name_window, text="Количество:",
                 bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=5)

        qty_entry = tk.Entry(name_window, width=10,
                             bg=self.colors['frame_bg'], fg=self.colors['fg'],
                             font=("Arial", 12), justify='center')
        qty_entry.pack()
        qty_entry.insert(0, "1")

        def add_to_waiting():
            visitor_name = name_entry.get().strip()
            if not visitor_name:
                messagebox.showerror("Ошибка", "❌ Введите ваше имя")
                return

            try:
                quantity = int(qty_entry.get().strip())
                if quantity <= 0:
                    raise ValueError
            except:
                messagebox.showerror("Ошибка", "❌ Введите корректное количество")
                return

            queue_number = Database.add_to_waiting_list(product_id, visitor_name, quantity, self.current_user_id)

            if queue_number:
                name_window.destroy()
                self.load_waiting_list()
                messagebox.showinfo("Успех!",
                                    f"✅ {product_name} добавлен в лист ожидания!\n"
                                    f"👤 {visitor_name}, ваш номер в очереди: {queue_number}")
            else:
                messagebox.showerror("Ошибка", "❌ Не удалось добавить в лист ожидания")

        tk.Button(name_window, text="📋 ДОБАВИТЬ В ЛИСТ ОЖИДАНИЯ",
                  command=add_to_waiting,
                  bg=self.colors['button_bg'], fg='white',
                  font=("Arial", 12, "bold"),
                  cursor="hand2", padx=20, pady=8).pack(pady=15)

    def get_cart_total_quantity(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_cart_total_sum(self):
        return sum(item['quantity'] * item['price'] for item in self.cart.values())

    def update_cart_display(self):
        total_qty = self.get_cart_total_quantity()
        total_sum = self.get_cart_total_sum()
        self.cart_btn.config(text=f"🛒 КОРЗИНА ({total_qty}) - {total_sum} руб.")

    def show_cart(self):
        if not self.cart:
            messagebox.showinfo("Корзина", "🛒 Корзина пуста")
            return

        cart_window = tk.Toplevel(self.root)
        cart_window.title("Корзина")
        cart_window.geometry("650x500")
        cart_window.configure(bg=self.colors['bg'])
        cart_window.transient(self.root)

        tk.Label(cart_window, text="🛍️ ВАША КОРЗИНА",
                 font=("Arial", 18, "bold"),
                 bg=self.colors['bg'], fg=self.colors['accent']).pack(pady=15)

        tree = ttk.Treeview(cart_window, columns=("Товар", "Цена", "Кол-во", "Сумма"), show="headings", height=12)
        for col, width in zip(("Товар", "Цена", "Кол-во", "Сумма"), (280, 100, 100, 120)):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor='center')
        tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        for item in self.cart.values():
            total = item['quantity'] * item['price']
            tree.insert("", tk.END, values=(item['name'], f"{item['price']}", item['quantity'], f"{total}"))

        total_frame = tk.Frame(cart_window, bg=self.colors['bg'])
        total_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(total_frame, text=f"ИТОГО: {self.get_cart_total_sum()} руб.",
                 font=("Arial", 16, "bold"),
                 bg=self.colors['bg'], fg=self.colors['accent']).pack(side=tk.RIGHT)

        btn_frame = tk.Frame(cart_window, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, padx=15, pady=15)

        tk.Button(btn_frame, text="✅ ОФОРМИТЬ ЗАКАЗ", command=lambda: self.checkout(cart_window),
                  bg=self.colors['button_bg'], fg='white', font=("Arial", 13, "bold"),
                  cursor="hand2", padx=25, pady=8).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="🗑️ ОЧИСТИТЬ", command=lambda: self.clear_cart(cart_window),
                  bg='#555', fg='white', font=("Arial", 12),
                  cursor="hand2", padx=20, pady=8).pack(side=tk.LEFT, padx=5)

    def clear_cart(self, window):
        self.cart.clear()
        self.update_cart_display()
        window.destroy()

    def checkout(self, cart_window):
        if not self.cart:
            messagebox.showwarning("Ошибка", "❌ Корзина пуста")
            return

        total = self.get_cart_total_sum()

        try:
            order_id = Database.create_order(self.current_user_id, total)

            for product_id, item in self.cart.items():
                Database.add_order_item(order_id, product_id, item['quantity'], item['price'])
                Database.update_stock(product_id, item['quantity'])

            cart_window.destroy()
            self.cart.clear()
            self.update_cart_display()
            self.load_products()
            self.load_orders()

            messagebox.showinfo("УСПЕХ!", f"✅ ЗАКАЗ #{order_id} ОФОРМЛЕН!\n💰 Сумма: {total} руб.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"❌ Ошибка: {str(e)}")

    def load_orders(self):
        for row in self.orders_tree.get_children():
            self.orders_tree.delete(row)

        orders = Database.get_all_orders()
        for order in orders:
            values = list(order)
            while len(values) < 4:
                values.append("")
            self.orders_tree.insert("", tk.END, values=values)

    def show_order_details(self):
        selected = self.orders_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "❌ Выберите заказ")
            return

        item = self.orders_tree.item(selected[0])['values']
        order_id = item[0]
        items = Database.get_order_items(order_id)

        self.order_details.delete(1.0, tk.END)
        self.order_details.insert(tk.END, f"📄 ЗАКАЗ #{order_id}\n")
        self.order_details.insert(tk.END, "=" * 50 + "\n\n")

        if items:
            self.order_details.insert(tk.END, f"{'Товар':<35} {'Кол-во':<10}")
            if len(items[0]) >= 4:
                self.order_details.insert(tk.END, f"{'Цена':<12} {'Сумма':<12}")
            self.order_details.insert(tk.END, "\n" + "-" * 70 + "\n")

            for it in items:
                self.order_details.insert(tk.END, f"{it[1]:<35} {it[2]:<10}")
                if len(it) >= 4:
                    total = it[2] * it[3] if isinstance(it[3], (int, float)) else 0
                    self.order_details.insert(tk.END, f"{it[3]:<12} {total:<12}")
                self.order_details.insert(tk.END, "\n")
        else:
            self.order_details.insert(tk.END, "Нет деталей заказа\n")

    def load_waiting_list(self):
        for row in self.waiting_tree.get_children():
            self.waiting_tree.delete(row)

        waiting = Database.get_waiting_list()
        for item in waiting:
            values = list(item)
            if len(values) < 6:
                while len(values) < 6:
                    values.append("")
            self.waiting_tree.insert("", tk.END, values=values)

    def remove_from_waiting(self):
        selected = self.waiting_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "❌ Выберите заявку")
            return

        if not messagebox.askyesno("Подтверждение", "❌ Удалить заявку из листа ожидания?"):
            return

        item = self.waiting_tree.item(selected[0])['values']
        waiting_id = item[0]

        Database.delete_from_waiting(waiting_id)
        self.load_waiting_list()
        messagebox.showinfo("Успех", "🗑️ Заявка удалена")

if __name__ == "__main__":
    root = tk.Tk()
    app = ParkShop(root)
    root.mainloop()