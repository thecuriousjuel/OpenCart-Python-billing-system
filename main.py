# main.py
import os
import sys
import json
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets import ToastNotification

# --- CONFIG & DIRECTORY SETUP ---
DIRS = ["data", "logs", "bills"]
for d in DIRS:
    os.makedirs(d, exist_ok=True)

# Import core modules
from src.database import InventoryModel, CategoryModel, CustomerModel, TransactionModel, CartModel, CartItemModel
from src.utils import logger, PDFInvoiceGenerator, sanitize_filename

class MainApplication(tb.Window):
    """Main window controller managing configurations, layouts, and frame switching."""
    def __init__(self):
        # Load persisted settings from ROOT folder
        self.config_file = "settings.json"
        self.config = self.load_settings()
        initial_theme = self.config.get("theme", "cosmo")
        if initial_theme not in ["cosmo", "superhero"]:
            initial_theme = "cosmo"
        
        super().__init__(
            title="OpenCart - Python Billing System",
            themename=initial_theme,
            size=(1300, 850),
            position=(50, 50)
        )
        self.state("zoomed") # Maximize by default
        
        # Configure global treeview style rules (boost font size to 12, row height to 35, header padding to 5)
        self.apply_treeview_styles()
        
        # Instantiate CSV models
        self.inventory_model = InventoryModel()
        self.category_model = CategoryModel()
        self.customer_model = CustomerModel()
        self.transaction_model = TransactionModel()
        self.cart_model = CartModel()
        self.cart_item_model = CartItemModel()
        
        # Build core layout container - adapt background to theme
        self.sidebar = tb.Frame(self, width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        self.content_area = tb.Frame(self)
        self.content_area.pack(side="right", expand=True, fill="both")
        
        # Initialize page dictionaries
        self.pages = {}
        self.current_page = None
        
        # Initialize frames (including new CustomersPage)
        for PageClass in (HomePage, InventoryPage, BillingPage, CustomersPage, HistoryPage, SettingsPage):
            page_name = PageClass.__name__
            frame = PageClass(parent=self.content_area, controller=self)
            self.pages[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        self.build_sidebar()
        self.show_frame("HomePage")
        
        # Setup Menu Bar
        self.menu_bar = tk.Menu(self)
        
        # File Menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Exit Application", command=self.destroy)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Navigate Menu (includes Customer Details page command)
        nav_menu = tk.Menu(self.menu_bar, tearoff=0)
        nav_menu.add_command(label="Home Dashboard", command=lambda: self.show_frame("HomePage"))
        nav_menu.add_command(label="Inventory Manager", command=lambda: self.show_frame("InventoryPage"))
        nav_menu.add_command(label="Billing Terminal", command=lambda: self.show_frame("BillingPage"))
        nav_menu.add_command(label="Customer Details", command=lambda: self.show_frame("CustomersPage"))
        nav_menu.add_command(label="Transaction History", command=lambda: self.show_frame("HistoryPage"))
        nav_menu.add_command(label="Settings & Logs", command=lambda: self.show_frame("SettingsPage"))
        self.menu_bar.add_cascade(label="Navigate", menu=nav_menu)
        
        # Theme Menu (Menu bar toggle)
        theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        theme_menu.add_command(label="Light Mode (Cosmo)", command=lambda: self.change_theme("cosmo"))
        theme_menu.add_command(label="Dark Mode (Superhero)", command=lambda: self.change_theme("superhero"))
        self.menu_bar.add_cascade(label="Theme", menu=theme_menu)
        
        # Help Menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.configure(menu=self.menu_bar)
        
        logger.info("Main Application layout loaded successfully.")

    def show_about_dialog(self):
        Messagebox.show_info(
            title="About Application",
            message="OpenCart - Python Billing System\nVersion 1.0\n\nMade with ♥ by Biswajit"
        )

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read settings: {e}")
        # Default fallback
        default_config = {"theme": "cosmo"}
        self.save_settings(default_config)
        return default_config

    def save_settings(self, config):
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def apply_treeview_styles(self):
        bootstyles = ["", "primary", "secondary", "success", "info", "warning", "danger", "light", "dark"]
        for bs in bootstyles:
            style_name = f"{bs}.Treeview" if bs else "Treeview"
            heading_style = f"{bs}.Treeview.Heading" if bs else "Treeview.Heading"
            self.style.configure(style_name, font=("Helvetica", 12), rowheight=35)
            self.style.configure(heading_style, font=("Helvetica", 12, "bold"), padding=(5, 5))

    def build_sidebar(self):
        # Application Branding
        brand = tb.Label(
            self.sidebar, 
            text="OpenCart Billing", 
            bootstyle="primary", 
            font=("Helvetica", 16, "bold"), 
            justify="center",
            padding=(0, 25)
        )
        brand.pack(fill="x")
        
        # Divider Line
        div = tb.Separator(self.sidebar)
        div.pack(fill="x", padx=10, pady=5)
        
        # Navigation Buttons configuration (includes Customer Details section)
        nav_items = [
            ("Home Dashboard", "HomePage"),
            ("Inventory Manager", "InventoryPage"),
            ("Billing / Cart", "BillingPage"),
            ("Customer Details", "CustomersPage"),
            ("Invoice History", "HistoryPage"),
            ("Settings & Logs", "SettingsPage")
        ]
        
        self.nav_buttons = {}
        for text, frame_name in nav_items:
            btn = tb.Button(
                self.sidebar, 
                text=text, 
                bootstyle="primary-outline", 
                command=lambda f=frame_name: self.show_frame(f)
            )
            btn.pack(fill="x", padx=15, pady=8)
            self.nav_buttons[frame_name] = btn

        # Sidebar Footer with red heart symbol
        self.footer_frame = tb.Frame(self.sidebar)
        self.footer_frame.pack(side="bottom", fill="x", pady=20)
        
        inner_footer = tb.Frame(self.footer_frame)
        inner_footer.pack(anchor="center")
        
        lbl1 = tb.Label(inner_footer, text="Made with ", font=("Helvetica", 10, "italic"))
        lbl1.pack(side="left")
        
        lbl_heart = tb.Label(inner_footer, text="♥", font=("Helvetica", 10), foreground="red")
        lbl_heart.pack(side="left")
        
        lbl2 = tb.Label(inner_footer, text=" by Biswajit", font=("Helvetica", 10, "italic"))
        lbl2.pack(side="left")
            
    def show_frame(self, page_name):
        frame = self.pages[page_name]
        frame.tkraise()
        self.current_page = page_name
        
        # Visual indication of active nav button
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(bootstyle="primary")
            else:
                btn.configure(bootstyle="primary-outline")
                
        # Trigger reload hooks if present
        if hasattr(frame, "on_show"):
            frame.on_show()

    def change_theme(self, new_theme):
        self.style.theme_use(new_theme)
        
        # Re-apply Treeview style rules because changing theme resets them
        self.apply_treeview_styles()
        
        self.config["theme"] = new_theme
        self.save_settings(self.config)
        logger.info(f"Theme successfully updated to {new_theme}")
        
        # Update Settings page theme selector if initialized
        if hasattr(self, "pages"):
            if "SettingsPage" in self.pages and hasattr(self.pages["SettingsPage"], "theme_combo"):
                self.pages["SettingsPage"].theme_combo.set(new_theme)
            if "BillingPage" in self.pages and hasattr(self.pages["BillingPage"], "update_listbox_colors"):
                self.pages["BillingPage"].update_listbox_colors()
            if "SettingsPage" in self.pages and hasattr(self.pages["SettingsPage"], "draw_graphs"):
                self.pages["SettingsPage"].draw_graphs()
        self.show_toast("Theme Changed", f"Successfully loaded '{new_theme}' theme.", "success")

    def show_toast(self, title, message, level="info"):
        """Displays a non-blocking toast notification at the bottom-right corner."""
        bootstyle = SUCCESS if level == "success" else (DANGER if level == "error" else INFO)
        toast = ToastNotification(
            title=title,
            message=message,
            duration=3000,
            bootstyle=bootstyle,
            position='se' # strictly bottom-right
        )
        toast.show_toast()


# --- HOME PAGE VIEW (DASHBOARD) ---
class HomePage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header banner
        header = tb.Label(
            self, 
            text="Dashboard Overview", 
            font=("Helvetica", 24, "bold"), 
            bootstyle="primary",
            padding=(20, 20)
        )
        header.pack(anchor="w")
        
        # Card Grid container
        self.cards_frame = tb.Frame(self)
        self.cards_frame.pack(fill="x", padx=20, pady=10)
        self.cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Instantiate Dashboard KPI metrics cards (no highlight)
        self.total_items_card = self.create_kpi_card("Total Items in Stock", "0", 0)
        self.low_stock_card = self.create_kpi_card("Low Stock Warnings", "0", 1)
        self.tx_today_card = self.create_kpi_card("Sales Invoices Today", "0", 2)
        self.rev_today_card = self.create_kpi_card("Revenue Today", "₹0.00", 3)
        
        # Shortcuts panel
        shortcuts_lbl = tb.Label(
            self, 
            text="Quick Action Panels", 
            font=("Helvetica", 14, "bold"), 
            bootstyle="primary",
            padding=(20, 30, 20, 10)
        )
        shortcuts_lbl.pack(anchor="w")
        
        sh_frame = tb.Frame(self)
        sh_frame.pack(fill="x", padx=20, pady=10)
        
        btn_new_bill = tb.Button(
            sh_frame, 
            text="Launch New Cart Checkout", 
            bootstyle="success", 
            padding=15, 
            command=lambda: self.controller.show_frame("BillingPage")
        )
        btn_new_bill.pack(side="left", padx=10)
        
        btn_add_item = tb.Button(
            sh_frame, 
            text="Manage Inventory catalog", 
            bootstyle="info", 
            padding=15, 
            command=lambda: self.controller.show_frame("InventoryPage")
        )
        btn_add_item.pack(side="left", padx=10)
        
        btn_view_logs = tb.Button(
            sh_frame, 
            text="View System Diagnostics", 
            bootstyle="warning", 
            padding=15, 
            command=lambda: self.controller.show_frame("SettingsPage")
        )
        btn_view_logs.pack(side="left", padx=10)

    def create_kpi_card(self, title, initial_val, column):
        card = tb.Labelframe(self.cards_frame, text=title, padding=15)
        card.grid(row=0, column=column, padx=10, sticky="nsew")
        
        lbl_val = tb.Label(card, text=initial_val, font=("Helvetica", 20, "bold"), bootstyle="primary")
        lbl_val.pack(anchor="center")
        return lbl_val

    def on_show(self):
        """Reload metric numbers on show."""
        # 1. Total items count
        active_items = self.controller.inventory_model.get_all()
        total_qty = sum(int(item["quantity"]) for item in active_items)
        self.total_items_card.configure(text=str(total_qty))
        
        # 2. Low stock warnings count
        low_stock = self.controller.inventory_model.get_low_stock(threshold=5)
        self.low_stock_card.configure(text=str(len(low_stock)))
        
        # 3. Transactions today & daily revenue
        txs = self.controller.transaction_model.get_history()
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        txs_today = 0
        revenue_today = 0.0
        for tx in txs:
            if tx["timestamp"].startswith(today_str):
                txs_today += 1
                revenue_today += float(tx["grand_total"])
                
        self.tx_today_card.configure(text=str(txs_today))
        self.rev_today_card.configure(text=f"₹{revenue_today:.2f}")


# --- INVENTORY PAGE VIEW ---
class InventoryPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Layout splits into Form Panel (Left) and Grid Table (Right)
        self.grid_columnconfigure(0, weight=4) # Form
        self.grid_columnconfigure(1, weight=6) # Table
        self.grid_rowconfigure(0, weight=1)
        
        # Left Panel (Inputs)
        left_panel = tb.Frame(self, padding=20)
        left_panel.grid(row=0, column=0, sticky="nsew")
        
        lbl_title = tb.Label(left_panel, text="Manage Inventory Catalog", font=("Helvetica", 16, "bold"), bootstyle="primary")
        lbl_title.pack(anchor="w", pady=(0, 20))
        
        # Entry form widgets
        self.var_id = tk.StringVar()
        self.var_name = tk.StringVar()
        self.var_category = tk.StringVar()
        self.var_price = tk.StringVar()
        self.var_qty = tk.StringVar()
        self.var_mfg = tk.StringVar()
        self.var_exp = tk.StringVar()
        
        # Auto Generated ID field (Read Only)
        tb.Label(left_panel, text="Product ID (Auto Generated)").pack(anchor="w", pady=(5, 2))
        self.ent_id = tb.Entry(left_panel, textvariable=self.var_id, state="readonly")
        self.ent_id.pack(fill="x", pady=(0, 10))
        
        # Name field
        tb.Label(left_panel, text="Product Name *").pack(anchor="w", pady=(5, 2))
        self.ent_name = tb.Entry(left_panel, textvariable=self.var_name)
        self.ent_name.pack(fill="x", pady=(0, 10))
        
        # Category field (Combobox - removed Add New button per requirements)
        cat_lbl_frame = tb.Frame(left_panel)
        cat_lbl_frame.pack(fill="x", pady=(5, 2))
        tb.Label(cat_lbl_frame, text="Category Selection *").pack(side="left")
        
        self.combo_category = tb.Combobox(left_panel, textvariable=self.var_category, state="readonly")
        self.combo_category.pack(fill="x", pady=(0, 10))
        
        # Price and Quantity Row
        pq_frame = tb.Frame(left_panel)
        pq_frame.pack(fill="x", pady=(0, 10))
        pq_frame.grid_columnconfigure((0, 1), weight=1)
        
        p_frame = tb.Frame(pq_frame)
        p_frame.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        tb.Label(p_frame, text="Unit Price (₹) *").pack(anchor="w", pady=(0, 2))
        tb.Entry(p_frame, textvariable=self.var_price).pack(fill="x")
        
        q_frame = tb.Frame(pq_frame)
        q_frame.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        tb.Label(q_frame, text="Stock Quantity *").pack(anchor="w", pady=(0, 2))
        tb.Entry(q_frame, textvariable=self.var_qty).pack(fill="x")
        
        # Manufacture and Expiry Dates Row
        dates_frame = tb.Frame(left_panel)
        dates_frame.pack(fill="x", pady=(0, 10))
        dates_frame.grid_columnconfigure((0, 1), weight=1)
        
        m_frame = tb.Frame(dates_frame)
        m_frame.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        tb.Label(m_frame, text="Mfg Date (YYYY-MM-DD) *").pack(anchor="w", pady=(0, 2))
        tb.Entry(m_frame, textvariable=self.var_mfg).pack(fill="x")
        
        e_frame = tb.Frame(dates_frame)
        e_frame.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        tb.Label(e_frame, text="Expiry Date (YYYY-MM-DD) *").pack(anchor="w", pady=(0, 2))
        tb.Entry(e_frame, textvariable=self.var_exp).pack(fill="x")
        
        # Action Buttons Form
        actions_frame = tb.Frame(left_panel)
        actions_frame.pack(fill="x", pady=(15, 0))
        
        self.btn_save = tb.Button(actions_frame, text="Add Product", bootstyle="success", command=self.save_item)
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_update = tb.Button(actions_frame, text="Update", bootstyle="warning", state="disabled", command=self.update_item)
        self.btn_update.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_delete = tb.Button(actions_frame, text="Delete", bootstyle="danger", state="disabled", command=self.delete_item)
        self.btn_delete.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        tb.Button(left_panel, text="Clear Form", bootstyle="secondary-outline", command=self.clear_form).pack(fill="x", pady=10)

        # Category Manager section (moved from SettingsPage)
        self.cat_frame = tb.Labelframe(left_panel, text="Category Manager", padding=10, bootstyle="primary")
        self.cat_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        self.cat_tree = tb.Treeview(self.cat_frame, columns=("name", "count"), show="headings", height=4)
        self.cat_tree.pack(fill="both", expand=True, pady=(0, 5))
        
        self.cat_tree.heading("name", text="Category Name")
        self.cat_tree.heading("count", text="Products Count")
        self.cat_tree.column("name", width=140, anchor="w")
        self.cat_tree.column("count", width=90, anchor="center")
        
        cat_actions = tb.Frame(self.cat_frame)
        cat_actions.pack(fill="x")
        
        tb.Button(cat_actions, text="Add Category", bootstyle="success", command=self.add_category).pack(side="left", fill="x", expand=True, padx=(0, 2))
        tb.Button(cat_actions, text="Delete Selected", bootstyle="danger-outline", command=self.delete_category).pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Right Panel (List Grid View)
        right_panel = tb.Frame(self, padding=20)
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Search & Sort & Filter Controls (includes category filter and Asc/Desc sorting)
        search_frame = tb.Frame(right_panel)
        search_frame.pack(fill="x", pady=(0, 15))
        
        tb.Label(search_frame, text="Search: ").pack(side="left", padx=(0, 5))
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", lambda *args: self.reload_tree())
        self.ent_search = tb.Entry(search_frame, textvariable=self.var_search, width=15)
        self.ent_search.pack(side="left", padx=5)
        
        tb.Label(search_frame, text="Filter: ").pack(side="left", padx=(10, 5))
        self.var_filter = tk.StringVar(value="All")
        self.combo_filter = tb.Combobox(search_frame, textvariable=self.var_filter, state="readonly", width=12)
        self.combo_filter.pack(side="left", padx=5)
        self.combo_filter.bind("<<ComboboxSelected>>", lambda e: self.reload_tree())
        
        tb.Label(search_frame, text="Sort: ").pack(side="left", padx=(10, 5))
        self.var_sort = tk.StringVar(value="name")
        self.combo_sort = tb.Combobox(search_frame, textvariable=self.var_sort, values=["name", "price", "quantity", "expiry_date", "mfg_date"], state="readonly", width=10)
        self.combo_sort.pack(side="left", padx=5)
        self.combo_sort.bind("<<ComboboxSelected>>", lambda e: self.reload_tree())
        
        # Ascending / Descending Toggle
        self.var_sort_desc = tk.BooleanVar(value=False)
        self.btn_sort_dir = tb.Button(
            search_frame, 
            text="Asc", 
            bootstyle="secondary-outline", 
            command=self.toggle_sort_dir,
            width=5
        )
        self.btn_sort_dir.pack(side="left", padx=5)
        
        # Grid View table
        columns = ("item_id", "name", "category", "price", "quantity", "mfg_date", "expiry_date")
        self.tree = tb.Treeview(right_panel, columns=columns, show="headings", bootstyle="primary")
        self.tree.pack(fill="both", expand=True)
        
        # Setup table headers
        self.tree.heading("item_id", text="Item ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("category", text="Category")
        self.tree.heading("price", text="Price")
        self.tree.heading("quantity", text="Stock")
        self.tree.heading("mfg_date", text="Mfg Date")
        self.tree.heading("expiry_date", text="Expiry Date")
        
        # Column alignments & widths
        self.tree.column("item_id", width=110, anchor="center")
        self.tree.column("name", width=140, anchor="w")
        self.tree.column("category", width=100, anchor="center")
        self.tree.column("price", width=70, anchor="e")
        self.tree.column("quantity", width=60, anchor="center")
        self.tree.column("mfg_date", width=95, anchor="center")
        self.tree.column("expiry_date", width=95, anchor="center")
        
        # Binding selection
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    def on_show(self):
        self.reload_categories()
        self.clear_form()
        self.reload_tree()

    def toggle_sort_dir(self):
        if self.var_sort_desc.get():
            self.var_sort_desc.set(False)
            self.btn_sort_dir.configure(text="Asc")
        else:
            self.var_sort_desc.set(True)
            self.btn_sort_dir.configure(text="Desc")
        self.reload_tree()

    def reload_categories(self):
        categories = [r["category_name"] for r in self.controller.category_model.get_all()]
        self.combo_category.configure(values=categories)
        self.combo_filter.configure(values=["All"] + categories)
        
        # Also reload category table
        self.cat_tree.delete(*self.cat_tree.get_children())
        all_categories = self.controller.category_model.get_all()
        for cat in all_categories:
            self.cat_tree.insert("", "end", values=(cat["category_name"], cat["total_items"]))

    def reload_tree(self):
        self.tree.delete(*self.tree.get_children())
        items = self.controller.inventory_model.get_all()
        
        # Apply Search Filter
        search_query = self.var_search.get().strip().lower()
        if search_query:
            items = [
                i for i in items 
                if search_query in i["item_id"].lower() or search_query in i["name"].lower() or search_query in i["category"].lower()
            ]
            
        # Apply Category Filter
        filter_cat = self.var_filter.get()
        if filter_cat and filter_cat != "All":
            items = [i for i in items if i["category"].lower() == filter_cat.lower()]
            
        # Apply Sorting with Asc/Desc toggles
        sort_key = self.var_sort.get()
        is_desc = self.var_sort_desc.get()
        
        if sort_key in ("price", "quantity"):
            items.sort(key=lambda x: float(x[sort_key]) if sort_key == "price" else int(x[sort_key]), reverse=is_desc)
        else:
            items.sort(key=lambda x: x[sort_key].lower(), reverse=is_desc)
            
        for item in items:
            self.tree.insert("", "end", values=(
                item["item_id"],
                item["name"],
                item["category"],
                f"₹{float(item['price']):.2f}",
                item["quantity"],
                item["mfg_date"],
                item["expiry_date"]
            ))

    def on_row_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        
        row = self.tree.item(selected[0])["values"]
        item_id = row[0]
        
        item = self.controller.inventory_model.get_by_id(item_id)
        if item:
            self.var_id.set(item["item_id"])
            self.var_name.set(item["name"])
            self.var_category.set(item["category"])
            self.var_price.set(item["price"])
            self.var_qty.set(item["quantity"])
            self.var_mfg.set(item["mfg_date"])
            self.var_exp.set(item["expiry_date"])
            
            self.btn_save.configure(state="disabled")
            self.btn_update.configure(state="normal")
            self.btn_delete.configure(state="normal")

    def clear_form(self):
        self.var_id.set("")
        self.var_name.set("")
        self.var_category.set("")
        self.var_price.set("")
        self.var_qty.set("")
        self.var_mfg.set("")
        self.var_exp.set("")
        
        self.btn_save.configure(state="normal")
        self.btn_update.configure(state="disabled")
        self.btn_delete.configure(state="disabled")
        self.tree.selection_remove(self.tree.selection())

    def save_item(self):
        success, res = self.controller.inventory_model.add_item(
            self.var_name.get(),
            self.var_category.get(),
            self.var_price.get(),
            self.var_qty.get(),
            self.var_mfg.get(),
            self.var_exp.get()
        )
        if success:
            logger.info(f"Inventory item added: ID {res}, Name: {self.var_name.get()}")
            self.controller.show_toast("Success", f"Product added successfully. ID: {res}", "success")
            self.on_show()
        else:
            Messagebox.show_error(res, "Validation Error")

    def update_item(self):
        item_id = self.var_id.get()
        success, res = self.controller.inventory_model.update_item(
            item_id,
            self.var_name.get(),
            self.var_category.get(),
            self.var_price.get(),
            self.var_qty.get(),
            self.var_mfg.get(),
            self.var_exp.get()
        )
        if success:
            logger.info(f"Inventory item updated: ID {item_id}, Name: {self.var_name.get()}")
            self.controller.show_toast("Success", "Product details updated.", "success")
            self.on_show()
        else:
            Messagebox.show_error(res, "Validation Error")

    def delete_item(self):
        item_id = self.var_id.get()
        confirm = Messagebox.okcancel(
            f"Are you sure you want to delete Product ID {item_id}? It will be soft-deleted and relocated to database archives.", 
            "Confirm Delete"
        )
        if confirm == "OK":
            success, res = self.controller.inventory_model.delete_item(item_id)
            if success:
                logger.info(f"Inventory item soft-deleted: ID {item_id}")
                self.controller.show_toast("Archived", "Product relocated to deleted inventory file.", "success")
                self.on_show()
            else:
                Messagebox.show_error(res, "Execution Error")

    def add_category(self):
        dialog = tb.Toplevel(self, title="Add Category")
        dialog.geometry("380x180")
        dialog.resizable(False, False)
        dialog.grab_set() # Modal behavior
        
        lbl = tb.Label(dialog, text="Enter Category Name:", font=("Helvetica", 11))
        lbl.pack(pady=(20, 5))
        
        ent = tb.Entry(dialog, width=30)
        ent.pack(pady=5)
        ent.focus_set()
        
        btn_frame = tb.Frame(dialog)
        btn_frame.pack(pady=15)
        
        def save_category():
            cat_name = ent.get().strip()
            success, msg = self.controller.category_model.add_category(cat_name)
            if success:
                logger.info(f"Category added: {cat_name}")
                self.controller.show_toast("Success", msg, "success")
                self.reload_categories()
                dialog.destroy()
            else:
                Messagebox.show_error(msg, "Error", parent=dialog)
                
        tb.Button(btn_frame, text="Save", bootstyle="success", command=save_category).pack(side="left", padx=5)
        tb.Button(btn_frame, text="Cancel", bootstyle="secondary-outline", command=dialog.destroy).pack(side="left", padx=5)

    def delete_category(self):
        selected = self.cat_tree.selection()
        if not selected:
            return
        
        row = self.cat_tree.item(selected[0])["values"]
        cat_name = row[0]
        
        confirm = Messagebox.okcancel(f"Are you sure you want to delete category '{cat_name}'?", "Confirm Delete")
        if confirm == "OK":
            success, msg = self.controller.category_model.delete_category(cat_name)
            if success:
                logger.info(f"Category deleted: {cat_name}")
                self.controller.show_toast("Success", msg, "success")
                self.reload_categories()
            else:
                Messagebox.show_error(msg, "Deletion Blocked")


# --- BILLING & MULTI-CART terminal VIEW ---
class BillingPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Cart structure: Up to 5 carts concurrent support (now loaded from CSV)
        self.active_cart_index = 1
        self.carts = self.load_carts()
            
        # Top Panel: Cart tabs and Invoice ID display
        top_frame = tb.Frame(self, padding=15)
        top_frame.pack(fill="x")
        
        tb.Label(top_frame, text="Active Billing Terminals: ", font=("Helvetica", 12, "bold"), bootstyle="primary").pack(side="left")
        
        self.cart_buttons = {}
        for idx in range(1, 6):
            btn = tb.Button(
                top_frame, 
                text=f"Cart {idx}", 
                bootstyle="light-outline" if idx != 1 else "success",
                command=lambda val=idx: self.switch_cart(val)
            )
            btn.pack(side="left", padx=5)
            self.cart_buttons[idx] = btn
            
        # Invoice indicator on top right
        self.lbl_invoice_meta = tb.Label(
            top_frame, 
            text="Invoice ID: N/A | Time: N/A", 
            font=("Helvetica", 11, "bold"), 
            bootstyle="warning"
        )
        self.lbl_invoice_meta.pack(side="right", padx=10)
        
        # Grid partitions: Left (Customer + Item Picker + Cart list) and Right (Total Summary Box)
        main_billing_split = tb.Frame(self)
        main_billing_split.pack(fill="both", expand=True, padx=15, pady=5)
        
        main_billing_split.grid_columnconfigure(0, weight=7) # Left Panel
        main_billing_split.grid_columnconfigure(1, weight=3) # Right Panel
        main_billing_split.grid_rowconfigure(0, weight=1)
        
        left_layout = tb.Frame(main_billing_split)
        left_layout.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Section A: Customer Details
        cust_frame = tb.Labelframe(left_layout, text="Buyer Information Details", padding=10, bootstyle="primary")
        cust_frame.pack(fill="x", pady=(0, 10))
        cust_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.var_c_phone = tk.StringVar()
        self.var_c_name = tk.StringVar()
        self.var_c_address = tk.StringVar()
        self.var_c_purchases = tk.StringVar(value="0")
        
        # Handle phone and name traces to trigger matching customer suggestions
        self.var_c_phone.trace_add("write", lambda *args: self.handle_customer_suggestions("phone"))
        self.var_c_name.trace_add("write", lambda *args: self.handle_customer_suggestions("name"))
        
        # Phone
        p_frame = tb.Frame(cust_frame)
        p_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        tb.Label(p_frame, text="Phone Number * (Type to query)", font=("Helvetica", 9)).pack(anchor="w")
        tb.Entry(p_frame, textvariable=self.var_c_phone).pack(fill="x")
        
        # Name
        n_frame = tb.Frame(cust_frame)
        n_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        tb.Label(n_frame, text="Customer Name * (Type to query)", font=("Helvetica", 9)).pack(anchor="w")
        tb.Entry(n_frame, textvariable=self.var_c_name).pack(fill="x")
        
        # Address
        a_frame = tb.Frame(cust_frame)
        a_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        tb.Label(a_frame, text="Address (Optional)", font=("Helvetica", 9)).pack(anchor="w")
        tb.Entry(a_frame, textvariable=self.var_c_address).pack(fill="x")

        # Loyalty Purchases Count (Read Only uneditable field)
        purch_frame = tb.Frame(cust_frame)
        purch_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=(5, 5), sticky="w")
        tb.Label(purch_frame, text="Loyalty Purchases Count: ", font=("Helvetica", 9, "bold")).pack(side="left")
        self.ent_purchases = tb.Entry(purch_frame, textvariable=self.var_c_purchases, state="readonly", width=8)
        self.ent_purchases.pack(side="left")
        
        tb.Button(
            purch_frame, 
            text="Clear Customer Details", 
            bootstyle="secondary-outline", 
            padding=2,
            command=self.clear_customer_fields
        ).pack(side="left", padx=15)

        # Customer Suggestions dropdown container (grids on row 2, columnspan=3)
        self.cust_suggestion_container = tb.Frame(cust_frame)
        self.list_cust_suggestions = tk.Listbox(
            self.cust_suggestion_container, 
            height=4, 
            font=("Segoe UI", 10),
            highlightthickness=0
        )
        self.list_cust_suggestions.pack(fill="both", expand=True)
        self.list_cust_suggestions.bind("<Double-Button-1>", lambda e: self.select_suggested_customer())
        self.list_cust_suggestions.bind("<Return>", lambda e: self.select_suggested_customer())

        # Section B: Item Search & Selection Bar
        item_picker_frame = tb.Labelframe(left_layout, text="Search & Insert Product to Cart", padding=10, bootstyle="primary")
        item_picker_frame.pack(fill="x", pady=10)
        
        tb.Label(item_picker_frame, text="Type Item Name or ID:", font=("Helvetica", 10)).pack(anchor="w", pady=(0, 2))
        
        self.var_item_search = tk.StringVar()
        self.var_item_search.trace_add("write", lambda *args: self.handle_item_suggestion())
        self.ent_item_search = tb.Entry(item_picker_frame, textvariable=self.var_item_search)
        self.ent_item_search.pack(fill="x")
        
        # Dynamic Suggestion Listbox (packed below input when searching)
        self.suggestion_container = tb.Frame(item_picker_frame)
        self.list_suggestions = tk.Listbox(
            self.suggestion_container, 
            height=4, 
            font=("Segoe UI", 10),
            highlightthickness=0
        )
        self.list_suggestions.pack(fill="both", expand=True)
        self.list_suggestions.bind("<Double-Button-1>", lambda e: self.add_suggested_item())
        self.list_suggestions.bind("<Return>", lambda e: self.add_suggested_item())
        
        # Section C: Active Cart Table view
        cart_table_frame = tb.Labelframe(left_layout, text="Active Checkout Cart items", padding=10, bootstyle="primary")
        cart_table_frame.pack(fill="both", expand=True, pady=10)
        
        columns = ("item_id", "name", "price", "quantity", "subtotal")
        self.cart_tree = tb.Treeview(cart_table_frame, columns=columns, show="headings", bootstyle="primary", height=10)
        self.cart_tree.pack(fill="both", expand=True)
        
        self.cart_tree.heading("item_id", text="Item ID")
        self.cart_tree.heading("name", text="Name")
        self.cart_tree.heading("price", text="Price")
        self.cart_tree.heading("quantity", text="Cart Qty")
        self.cart_tree.heading("subtotal", text="Subtotal")
        
        self.cart_tree.column("item_id", width=120, anchor="center")
        self.cart_tree.column("name", width=220, anchor="w")
        self.cart_tree.column("price", width=90, anchor="e")
        self.cart_tree.column("quantity", width=80, anchor="center")
        self.cart_tree.column("subtotal", width=110, anchor="e")
        
        self.cart_tree.bind("<Double-Button-1>", self.modify_cart_qty_popup)
        
        # Row action buttons
        row_actions = tb.Frame(cart_table_frame)
        row_actions.pack(fill="x", pady=(8, 0))
        
        tb.Button(row_actions, text="Remove Selected Item", bootstyle="danger", command=self.remove_cart_item).pack(side="left")
        tb.Label(row_actions, text="* Double-click a row to update quantity", font=("Helvetica", 9, "italic")).pack(side="right")

        # Right Panel (Receipt Totals Drawer) - Adapt to Theme
        right_panel = tb.Frame(main_billing_split, padding=20)
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        tb.Label(right_panel, text="Receipt Summary", font=("Helvetica", 14, "bold"), bootstyle="primary").pack(anchor="w", pady=(0, 20))
        
        # Summary totals labels
        self.lbl_subtotal = tb.Label(right_panel, text="Subtotal: ₹0.00", font=("Helvetica", 12))
        self.lbl_subtotal.pack(anchor="w", pady=10)
        
        # Discount field
        disc_frame = tb.Frame(right_panel)
        disc_frame.pack(fill="x", pady=10)
        tb.Label(disc_frame, text="Discount (%): ", font=("Helvetica", 11)).pack(side="left")
        
        self.var_discount = tk.StringVar(value="0")
        self.var_discount.trace_add("write", lambda *args: self.recalculate_totals())
        self.ent_discount = tb.Entry(disc_frame, textvariable=self.var_discount, width=8)
        self.ent_discount.pack(side="right")
        
        # Grand total
        self.lbl_grand = tb.Label(right_panel, text="Grand Total: ₹0.00", font=("Helvetica", 16, "bold"), bootstyle="primary")
        self.lbl_grand.pack(anchor="w", pady=(30, 20))
        
        # Checkout buttons
        tb.Button(
            right_panel, 
            text="Confirm checkout & Print PDF", 
            bootstyle="success", 
            padding=12,
            command=self.process_checkout
        ).pack(fill="x", pady=10)
        
        tb.Button(
            right_panel, 
            text="Cancel Checkout Order", 
            bootstyle="danger-outline", 
            command=self.reset_active_cart
        ).pack(fill="x")
        
        # Initial colors for suggestions
        self.update_listbox_colors()

    def get_empty_cart_structure(self):
        invoice_id = self.controller.transaction_model.generate_invoice_id()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "invoice_id": invoice_id,
            "timestamp": timestamp,
            "customer": {"phone": "", "name": "", "address": ""},
            "items": [],
            "discount": 0.0
        }

    def load_carts(self):
        carts = {}
        # Initialize default structures
        for idx in range(1, 6):
            carts[idx] = self.get_empty_cart_structure()
            
        try:
            # Load cart headers & line items from CSV databases
            headers = self.controller.cart_model.read_all()
            items_data = self.controller.cart_item_model.read_all()
            
            # Group items by cart_index
            items_by_cart = {}
            for item in items_data:
                idx = int(item["cart_index"])
                items_by_cart.setdefault(idx, []).append(item)
                
            # Populate cart structures
            for h in headers:
                idx = int(h["cart_index"])
                if idx in carts:
                    carts[idx]["invoice_id"] = h["invoice_id"]
                    carts[idx]["timestamp"] = h["timestamp"]
                    carts[idx]["customer"]["phone"] = h["customer_phone"]
                    carts[idx]["customer"]["name"] = h["customer_name"]
                    carts[idx]["customer"]["address"] = h["customer_address"]
                    try:
                        carts[idx]["discount"] = float(h["discount"])
                    except ValueError:
                        carts[idx]["discount"] = 0.0
                        
                    raw_items = items_by_cart.get(idx, [])
                    carts[idx]["items"] = []
                    for ri in raw_items:
                        item_id = ri["item_id"]
                        qty = ri["quantity"]
                        
                        # Fetch current details from active catalog
                        item_info = self.controller.inventory_model.get_by_id(item_id)
                        if item_info:
                            carts[idx]["items"].append({
                                "item_id": item_id,
                                "name": item_info["name"],
                                "price": item_info["price"],
                                "quantity": qty
                            })
                        else:
                            carts[idx]["items"].append({
                                "item_id": item_id,
                                "name": "Deleted/Unknown Item",
                                "price": "0.00",
                                "quantity": qty
                            })
        except Exception as e:
            logger.error(f"Failed to read carts from CSV: {e}")
            
        return carts

    def save_carts(self):
        # Sync currently active cart variables before saving
        idx = self.active_cart_index
        self.carts[idx]["customer"]["phone"] = self.var_c_phone.get()
        self.carts[idx]["customer"]["name"] = self.var_c_name.get()
        self.carts[idx]["customer"]["address"] = self.var_c_address.get()
        try:
            self.carts[idx]["discount"] = float(self.var_discount.get())
        except ValueError:
            self.carts[idx]["discount"] = 0.0
            
        headers_to_write = []
        items_to_write = []
        
        for idx, cart in self.carts.items():
            headers_to_write.append({
                "cart_index": str(idx),
                "invoice_id": cart["invoice_id"],
                "timestamp": cart["timestamp"],
                "customer_phone": cart["customer"]["phone"],
                "customer_name": cart["customer"]["name"],
                "customer_address": cart["customer"]["address"],
                "discount": str(cart["discount"])
            })
            
            for item in cart["items"]:
                items_to_write.append({
                    "cart_index": str(idx),
                    "item_id": item["item_id"],
                    "quantity": item["quantity"]
                })
                
        try:
            self.controller.cart_model.write_all(headers_to_write)
            self.controller.cart_item_model.write_all(items_to_write)
        except Exception as e:
            logger.error(f"Failed to write carts to CSV: {e}")

    def on_show(self):
        self.carts = self.load_carts() # Reload to stay synced
        self.switch_cart(self.active_cart_index)
        self.suggestion_container.pack_forget()
        self.cust_suggestion_container.grid_forget()
        self.update_listbox_colors()

    def handle_customer_suggestions(self, source_field):
        if hasattr(self, "_updating_customer_fields") and self._updating_customer_fields:
            return
            
        q = ""
        if source_field == "phone":
            q = self.var_c_phone.get().strip()
        else:
            q = self.var_c_name.get().strip()
            
        if not q:
            self.cust_suggestion_container.grid_forget()
            self.var_c_purchases.set("0")
            return
            
        # Immediate autocomplete if 10-digit phone
        if source_field == "phone":
            digits_only = "".join(filter(str.isdigit, q))
            if len(digits_only) == 10:
                cust = self.controller.customer_model.get_by_phone(digits_only)
                if cust:
                    self._updating_customer_fields = True
                    self.var_c_name.set(cust["name"])
                    self.var_c_address.set(cust["address"])
                    count = self.controller.transaction_model.get_customer_purchase_count(digits_only)
                    self.var_c_purchases.set(str(count))
                    self._updating_customer_fields = False
                    self.cust_suggestion_container.grid_forget()
                    self.controller.show_toast("Buyer Found", f"Autocompleted details for customer: {cust['name']}", "info")
                    return
                else:
                    self.var_c_purchases.set("0")
            else:
                self.var_c_purchases.set("0")
        else:
            self.var_c_purchases.set("0")
            
        matches = self.controller.customer_model.search_customers(q)
        
        self.list_cust_suggestions.delete(0, tk.END)
        if matches:
            for c in matches:
                self.list_cust_suggestions.insert(tk.END, f"{c['phone']} - {c['name']}")
            self.cust_suggestion_container.grid(row=2, column=0, columnspan=3, pady=(5, 5), sticky="ew")
        else:
            self.cust_suggestion_container.grid_forget()

    def select_suggested_customer(self):
        selected = self.list_cust_suggestions.curselection()
        if not selected:
            return
            
        val = self.list_cust_suggestions.get(selected[0])
        phone = val.split(" - ")[0]
        
        cust = self.controller.customer_model.get_by_phone(phone)
        if cust:
            self._updating_customer_fields = True
            
            self.var_c_phone.set(cust["phone"])
            self.var_c_name.set(cust["name"])
            self.var_c_address.set(cust["address"])
            
            # Fetch purchase counts
            count = self.controller.transaction_model.get_customer_purchase_count(phone)
            self.var_c_purchases.set(str(count))
            
            self._updating_customer_fields = False
            self.cust_suggestion_container.grid_forget()
            
            self.controller.show_toast("Buyer Selected", f"Details loaded for {cust['name']}", "info")

    def switch_cart(self, index):
        old_idx = self.active_cart_index
        self.carts[old_idx]["customer"]["phone"] = self.var_c_phone.get()
        self.carts[old_idx]["customer"]["name"] = self.var_c_name.get()
        self.carts[old_idx]["customer"]["address"] = self.var_c_address.get()
        try:
            self.carts[old_idx]["discount"] = float(self.var_discount.get())
        except ValueError:
            self.carts[old_idx]["discount"] = 0.0
            
        self.active_cart_index = index
        
        # Render active tab state
        for idx, btn in self.cart_buttons.items():
            if idx == index:
                btn.configure(bootstyle="success")
            else:
                btn.configure(bootstyle="light-outline")
                
        # Load variables of new active cart
        cart = self.carts[index]
        self.lbl_invoice_meta.configure(text=f"Invoice ID: {cart['invoice_id']} | Date: {cart['timestamp'][:10]}")
        
        # Temporarily disable autocomplete checks while filling fields
        self._updating_customer_fields = True
        self.var_c_phone.set("")
        self.var_c_name.set(cart["customer"]["name"])
        self.var_c_address.set(cart["customer"]["address"])
        self.var_c_phone.set(cart["customer"]["phone"])
        
        # Reload purchases count
        if cart["customer"]["phone"]:
            count = self.controller.transaction_model.get_customer_purchase_count(cart["customer"]["phone"])
            self.var_c_purchases.set(str(count))
        else:
            self.var_c_purchases.set("0")
            
        self._updating_customer_fields = False
        
        self.var_discount.set(str(int(cart["discount"]) if cart["discount"].is_integer() else cart["discount"]))
        self.var_item_search.set("")
        self.suggestion_container.pack_forget()
        self.cust_suggestion_container.grid_forget()
        
        self.reload_cart_table()

    def reload_cart_table(self):
        self.cart_tree.delete(*self.cart_tree.get_children())
        cart = self.carts[self.active_cart_index]
        for item in cart["items"]:
            sub = round(int(item["quantity"]) * float(item["price"]), 2)
            self.cart_tree.insert("", "end", values=(
                item["item_id"],
                item["name"],
                f"₹{float(item['price']):.2f}",
                item["quantity"],
                f"₹{sub:.2f}"
            ))
        self.recalculate_totals()
        self.save_carts() # Auto save changes to disk

    def recalculate_totals(self):
        cart = self.carts[self.active_cart_index]
        subtotal = 0.0
        for item in cart["items"]:
            subtotal += int(item["quantity"]) * float(item["price"])
            
        subtotal = round(subtotal, 2)
        
        # Get discount
        try:
            disc = float(self.var_discount.get())
            if not (0 <= disc <= 100):
                disc = 0.0
        except ValueError:
            disc = 0.0
            
        grand = round(subtotal * (1 - (disc / 100.0)), 2)
        
        self.lbl_subtotal.configure(text=f"Subtotal: ₹{subtotal:.2f}")
        self.lbl_grand.configure(text=f"Grand Total: ₹{grand:.2f}")

    def handle_item_suggestion(self):
        q = self.var_item_search.get().strip().lower()
        if not q:
            self.suggestion_container.pack_forget()
            return
            
        items = self.controller.inventory_model.get_all()
        matches = [
            item for item in items 
            if q in item["item_id"].lower() or q in item["name"].lower()
        ]
        
        self.list_suggestions.delete(0, tk.END)
        if matches:
            for item in matches[:5]:
                self.list_suggestions.insert(tk.END, f"{item['item_id']} - {item['name']} [Stock: {item['quantity']}]")
            self.suggestion_container.pack(fill="x", pady=2)
        else:
            self.suggestion_container.pack_forget()

    def add_suggested_item(self):
        selected = self.list_suggestions.curselection()
        if not selected:
            return
        
        val = self.list_suggestions.get(selected[0])
        item_id = val.split(" - ")[0]
        
        item = self.controller.inventory_model.get_by_id(item_id)
        if item:
            avail_stock = int(item["quantity"])
            if avail_stock <= 0:
                Messagebox.show_warning(f"Item '{item['name']}' is out of stock.", "Stock Warning")
                return
                
            cart = self.carts[self.active_cart_index]
            
            found_item = None
            for cart_item in cart["items"]:
                if cart_item["item_id"] == item_id:
                    found_item = cart_item
                    break
                    
            if found_item:
                if int(found_item["quantity"]) + 1 > avail_stock:
                    Messagebox.show_error(f"Cannot exceed available stock of {avail_stock} units.", "Stock Overflow")
                    return
                found_item["quantity"] = str(int(found_item["quantity"]) + 1)
            else:
                cart["items"].append({
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "price": item["price"],
                    "quantity": "1"
                })
                
            self.var_item_search.set("")
            self.suggestion_container.pack_forget()
            self.reload_cart_table()
            self.controller.show_toast("Cart Updated", f"Added '{item['name']}' to Cart.", "info")

    def remove_cart_item(self):
        selected = self.cart_tree.selection()
        if not selected:
            return
        
        row = self.cart_tree.item(selected[0])["values"]
        item_id = row[0]
        
        cart = self.carts[self.active_cart_index]
        cart["items"] = [item for item in cart["items"] if item["item_id"] != item_id]
        
        self.reload_cart_table()
        self.controller.show_toast("Item Removed", "Product removed from cart.", "warning")

    def modify_cart_qty_popup(self, event):
        selected = self.cart_tree.selection()
        if not selected:
            return
        
        row = self.cart_tree.item(selected[0])["values"]
        item_id = row[0]
        current_qty = int(row[3])
        
        item_info = self.controller.inventory_model.get_by_id(item_id)
        if not item_info:
            return
        max_stock = int(item_info["quantity"])
        
        dialog = tb.Toplevel(self, title="Update Quantity")
        dialog.geometry("320x160")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        tb.Label(dialog, text=f"Update quantity for:\n{item_info['name']}\n(Available stock: {max_stock})", font=("Helvetica", 10), justify="center").pack(pady=10)
        
        var_q = tk.StringVar(value=str(current_qty))
        ent = tb.Entry(dialog, textvariable=var_q, width=10)
        ent.pack()
        ent.focus_set()
        
        btn_frame = tb.Frame(dialog)
        btn_frame.pack(pady=15)
        
        def save_qty():
            try:
                new_q = int(var_q.get())
                if new_q <= 0:
                    Messagebox.show_error("Quantity must be a positive integer.", "Error", parent=dialog)
                    return
                if new_q > max_stock:
                    Messagebox.show_error(f"Stock limit exceeded. Maximum available is {max_stock}.", "Error", parent=dialog)
                    return
                
                # Apply changes
                cart = self.carts[self.active_cart_index]
                for item in cart["items"]:
                    if item["item_id"] == item_id:
                        item["quantity"] = str(new_q)
                        break
                        
                self.reload_cart_table()
                dialog.destroy()
            except ValueError:
                Messagebox.show_error("Invalid quantity. Enter integer digits.", "Error", parent=dialog)
                
        tb.Button(btn_frame, text="Confirm", bootstyle="success", command=save_qty).pack(side="left", padx=5)
        tb.Button(btn_frame, text="Cancel", bootstyle="secondary-outline", command=dialog.destroy).pack(side="left", padx=5)

    def reset_active_cart(self):
        confirm = Messagebox.okcancel("Are you sure you want to discard the active cart details?", "Discard Cart")
        if confirm == "OK":
            self.carts[self.active_cart_index] = self.get_empty_cart_structure()
            self.switch_cart(self.active_cart_index)
            self.controller.show_toast("Cart Reset", "Cart contents cleared.", "info")

    def process_checkout(self):
        cart = self.carts[self.active_cart_index]
        
        if not cart["items"]:
            Messagebox.show_error("Cannot proceed to checkout. Cart is empty.", "Cart Empty")
            return
            
        phone = self.var_c_phone.get().strip()
        name = self.var_c_name.get().strip()
        address = self.var_c_address.get().strip()
        
        digits_phone = "".join(filter(str.isdigit, phone))
        if len(digits_phone) != 10:
            Messagebox.show_error("Phone number must be exactly 10 digits.", "Validation Error")
            return
        if not name:
            Messagebox.show_error("Customer Name is mandatory.", "Validation Error")
            return
            
        try:
            discount_percent = float(self.var_discount.get())
            if not (0 <= discount_percent <= 100):
                Messagebox.show_error("Discount percentage must be between 0 and 100.", "Validation Error")
                return
        except ValueError:
            Messagebox.show_error("Discount percentage must be a numeric value.", "Validation Error")
            return
            
        success, res = self.controller.transaction_model.checkout(
            digits_phone,
            cart["items"],
            discount_percent
        )
        
        if success:
            invoice_data = res
            invoice_id = invoice_data["invoice_id"]
            
            # Save customer profile
            self.controller.customer_model.add_or_update(digits_phone, name, address)
            
            # Map item names for PDF
            items_list = []
            for item in cart["items"]:
                items_list.append({
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "price_at_sale": item["price"],
                    "quantity": item["quantity"],
                    "subtotal": round(int(item["quantity"]) * float(item["price"]), 2)
                })
                
            # Compile PDF receipt
            pdf_filename = f"{invoice_id}_{invoice_data['timestamp'][:10]}_{invoice_data['timestamp'][11:19].replace(':', '-')}.pdf"
            customer_details = {"phone": digits_phone, "name": name, "address": address}
            
            pdf_path = PDFInvoiceGenerator.generate(
                invoice_data,
                items_list,
                customer_details,
                pdf_filename
            )
            
            logger.info(f"Checkout transaction finalized: Invoice {invoice_id}, Customer: {name}")
            self.controller.show_toast("Checkout Finalized", f"PDF Generated. Invoice ID: {invoice_id}", "success")
            
            # Clear active cart structure
            self.carts[self.active_cart_index] = self.get_empty_cart_structure()
            self.switch_cart(self.active_cart_index)
            
            open_pdf = Messagebox.yesno(f"Checkout successful!\nInvoice ID: {invoice_id}\n\nWould you like to open the generated PDF receipt?", "Open Receipt")
            if open_pdf == "Yes":
                try:
                    os.startfile(pdf_path)
                except Exception as e:
                    logger.error(f"Failed to open generated PDF file: {e}")
                    Messagebox.show_error(f"Failed to open PDF file: {e}", "File Error")
        else:
            Messagebox.show_error(res, "Checkout Transaction Failed")

    def clear_customer_fields(self):
        self._updating_customer_fields = True
        self.var_c_phone.set("")
        self.var_c_name.set("")
        self.var_c_address.set("")
        self.var_c_purchases.set("0")
        self._updating_customer_fields = False
        self.cust_suggestion_container.grid_forget()
        
        # Save change to active cart data structure
        idx = self.active_cart_index
        self.carts[idx]["customer"]["phone"] = ""
        self.carts[idx]["customer"]["name"] = ""
        self.carts[idx]["customer"]["address"] = ""
        self.save_carts()
        
        self.controller.show_toast("Customer Cleared", "Customer details have been cleared from this cart.", "info")

    def update_listbox_colors(self):
        style = self.controller.style
        bg_color = style.colors.get("inputbg") or style.colors.get("bg") or "#ffffff"
        fg_color = style.colors.get("inputfg") or style.colors.get("fg") or "#000000"
        select_bg = style.colors.get("selectbg") or style.colors.get("primary") or "#007fff"
        select_fg = style.colors.get("selectfg") or "#ffffff"
        
        self.list_suggestions.configure(
            bg=bg_color,
            fg=fg_color,
            selectbackground=select_bg,
            selectforeground=select_fg
        )
        
        self.list_cust_suggestions.configure(
            bg=bg_color,
            fg=fg_color,
            selectbackground=select_bg,
            selectforeground=select_fg
        )


# --- CUSTOMER DETAILS VIEW ---
class CustomersPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header = tb.Label(
            self, 
            text="Customer Directory & Loyalty Tracking", 
            font=("Helvetica", 20, "bold"), 
            bootstyle="primary",
            padding=(20, 20)
        )
        header.pack(anchor="w")
        
        # Filter / Search Panel
        search_frame = tb.Frame(self, padding=(20, 0, 20, 10))
        search_frame.pack(fill="x")
        
        tb.Label(search_frame, text="Search Customer Name or Phone: ").pack(side="left", padx=(0, 5))
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", lambda *args: self.reload_table())
        self.ent_search = tb.Entry(search_frame, textvariable=self.var_search, width=25)
        self.ent_search.pack(side="left", padx=5)
        
        # Sorting Options
        tb.Label(search_frame, text="Sort: ").pack(side="left", padx=(15, 5))
        self.var_sort = tk.StringVar(value="name")
        self.combo_sort = tb.Combobox(search_frame, textvariable=self.var_sort, values=["name", "phone", "purchases", "spent"], state="readonly", width=12)
        self.combo_sort.pack(side="left", padx=5)
        self.combo_sort.bind("<<ComboboxSelected>>", lambda e: self.reload_table())
        
        self.var_sort_desc = tk.BooleanVar(value=False)
        self.btn_sort_dir = tb.Button(
            search_frame, 
            text="Asc", 
            bootstyle="secondary-outline", 
            command=self.toggle_sort_dir,
            width=5
        )
        self.btn_sort_dir.pack(side="left", padx=5)
        
        # Table / Treeview (Size 12 styled globally via self.controller.style)
        columns = ("phone", "name", "address", "purchases", "spent")
        self.tree = tb.Treeview(self, columns=columns, show="headings", bootstyle="primary")
        self.tree.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        self.tree.heading("phone", text="Phone Number")
        self.tree.heading("name", text="Customer Name")
        self.tree.heading("address", text="Address")
        self.tree.heading("purchases", text="Loyalty Purchases")
        self.tree.heading("spent", text="Total Spent")
        
        self.tree.column("phone", width=150, anchor="center")
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("address", width=300, anchor="w")
        self.tree.column("purchases", width=130, anchor="center")
        self.tree.column("spent", width=150, anchor="e")
        
    def on_show(self):
        self.reload_table()
        
    def toggle_sort_dir(self):
        if self.var_sort_desc.get():
            self.var_sort_desc.set(False)
            self.btn_sort_dir.configure(text="Asc")
        else:
            self.var_sort_desc.set(True)
            self.btn_sort_dir.configure(text="Desc")
        self.reload_table()
        
    def reload_table(self):
        self.tree.delete(*self.tree.get_children())
        
        raw_customers = self.controller.customer_model.read_all()
        search_query = self.var_search.get().strip().lower()
        
        customers_data = []
        for c in raw_customers:
            if search_query and not (search_query in c["phone"].lower() or search_query in c["name"].lower()):
                continue
            phone = c["phone"]
            purchases = self.controller.transaction_model.get_customer_purchase_count(phone)
            spent = self.controller.transaction_model.get_customer_total_spent(phone)
            customers_data.append({
                "phone": phone,
                "name": c["name"],
                "address": c["address"] if c["address"] else "N/A",
                "purchases": purchases,
                "spent": spent
            })
            
        # Apply sorting
        sort_key = self.var_sort.get()
        is_desc = self.var_sort_desc.get()
        
        if sort_key == "purchases":
            customers_data.sort(key=lambda x: x["purchases"], reverse=is_desc)
        elif sort_key == "spent":
            customers_data.sort(key=lambda x: x["spent"], reverse=is_desc)
        elif sort_key == "phone":
            customers_data.sort(key=lambda x: x["phone"].lower(), reverse=is_desc)
        else: # default name
            customers_data.sort(key=lambda x: x["name"].lower(), reverse=is_desc)
            
        for c in customers_data:
            self.tree.insert("", "end", values=(
                c["phone"],
                c["name"],
                c["address"],
                str(c["purchases"]),
                f"₹{c['spent']:.2f}"
            ))


# --- TRANSACTION HISTORY VIEW ---
class HistoryPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Horizontal Split: Top (Search Panel & Header Table) and Bottom (Selected Invoice Detail)
        self.grid_rowconfigure(0, weight=6) # History list
        self.grid_rowconfigure(1, weight=4) # Details box
        self.grid_columnconfigure(0, weight=1)
        
        # Top Frame
        top_frame = tb.Frame(self, padding=20)
        top_frame.grid(row=0, column=0, sticky="nsew")
        
        lbl_title = tb.Label(top_frame, text="Transaction & Invoice History", font=("Helvetica", 16, "bold"), bootstyle="primary")
        lbl_title.pack(anchor="w", pady=(0, 15))
        
        # Filter controls
        filter_frame = tb.Frame(top_frame)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        tb.Label(filter_frame, text="Search Phone or Invoice ID: ").pack(side="left")
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", lambda *args: self.reload_history_table())
        tb.Entry(filter_frame, textvariable=self.var_search, width=25).pack(side="left", padx=5)
        
        # Sorting Options
        tb.Label(filter_frame, text="Sort: ").pack(side="left", padx=(15, 5))
        self.var_sort = tk.StringVar(value="timestamp")
        self.combo_sort = tb.Combobox(filter_frame, textvariable=self.var_sort, values=["timestamp", "invoice_id", "subtotal", "discount_percent", "grand_total"], state="readonly", width=15)
        self.combo_sort.pack(side="left", padx=5)
        self.combo_sort.bind("<<ComboboxSelected>>", lambda e: self.reload_history_table())
        
        self.var_sort_desc = tk.BooleanVar(value=True)
        self.btn_sort_dir = tb.Button(
            filter_frame, 
            text="Desc", 
            bootstyle="secondary-outline", 
            command=self.toggle_sort_dir,
            width=5
        )
        self.btn_sort_dir.pack(side="left", padx=5)
        
        # Table of Invoices
        columns = ("invoice_id", "timestamp", "customer_phone", "subtotal", "discount_percent", "grand_total")
        self.tree = tb.Treeview(top_frame, columns=columns, show="headings", bootstyle="primary")
        self.tree.pack(fill="both", expand=True)
        
        self.tree.heading("invoice_id", text="Invoice ID")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("customer_phone", text="Customer Phone")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.heading("discount_percent", text="Discount %")
        self.tree.heading("grand_total", text="Grand Total")
        
        self.tree.column("invoice_id", width=120, anchor="center")
        self.tree.column("timestamp", width=160, anchor="center")
        self.tree.column("customer_phone", width=110, anchor="center")
        self.tree.column("subtotal", width=90, anchor="e")
        self.tree.column("discount_percent", width=80, anchor="center")
        self.tree.column("grand_total", width=110, anchor="e")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_invoice_select)

        # Bottom Frame (Receipt Line Items viewer)
        bottom_frame = tb.Frame(self, padding=20)
        bottom_frame.grid(row=1, column=0, sticky="nsew")
        
        # Bottom Title & actions row
        det_title_row = tb.Frame(bottom_frame)
        det_title_row.pack(fill="x", pady=(0, 10))
        
        self.lbl_details_title = tb.Label(det_title_row, text="Invoice Itemized Details", font=("Helvetica", 12, "bold"))
        self.lbl_details_title.pack(side="left")
        
        self.btn_open_pdf = tb.Button(det_title_row, text="Open generated PDF bill", bootstyle="info", state="disabled", command=self.open_pdf_receipt)
        self.btn_open_pdf.pack(side="right")
        
        # Detail items Treeview
        det_columns = ("item_id", "name", "price", "quantity", "subtotal")
        self.detail_tree = tb.Treeview(bottom_frame, columns=det_columns, show="headings", bootstyle="secondary", height=6)
        self.detail_tree.pack(fill="both", expand=True)
        
        self.detail_tree.heading("item_id", text="Item ID")
        self.detail_tree.heading("name", text="Product Name")
        self.detail_tree.heading("price", text="Price")
        self.detail_tree.heading("quantity", text="Quantity Purchased")
        self.detail_tree.heading("subtotal", text="Subtotal")
        
        self.detail_tree.column("item_id", width=120, anchor="center")
        self.detail_tree.column("name", width=260, anchor="w")
        self.detail_tree.column("price", width=90, anchor="e")
        self.detail_tree.column("quantity", width=80, anchor="center")
        self.detail_tree.column("subtotal", width=110, anchor="e")

    def on_show(self):
        self.reload_history_table()
        self.detail_tree.delete(*self.detail_tree.get_children())
        self.lbl_details_title.configure(text="Invoice Itemized Details")
        self.btn_open_pdf.configure(state="disabled")

    def toggle_sort_dir(self):
        if self.var_sort_desc.get():
            self.var_sort_desc.set(False)
            self.btn_sort_dir.configure(text="Asc")
        else:
            self.var_sort_desc.set(True)
            self.btn_sort_dir.configure(text="Desc")
        self.reload_history_table()

    def reload_history_table(self):
        self.tree.delete(*self.tree.get_children())
        history = self.controller.transaction_model.get_history()
        
        q = self.var_search.get().strip().lower()
        if q:
            history = [
                tx for tx in history 
                if q in tx["invoice_id"].lower() or q in tx["customer_phone"].lower()
            ]
            
        # Apply sorting
        sort_key = self.var_sort.get()
        is_desc = self.var_sort_desc.get()
        
        if sort_key in ("subtotal", "discount_percent", "grand_total"):
            history.sort(key=lambda x: float(x[sort_key]), reverse=is_desc)
        else:
            history.sort(key=lambda x: x[sort_key].lower(), reverse=is_desc)
            
        for tx in history:
            self.tree.insert("", "end", values=(
                tx["invoice_id"],
                tx["timestamp"],
                tx["customer_phone"],
                f"₹{float(tx['subtotal']):.2f}",
                f"{float(tx['discount_percent'])}%",
                f"₹{float(tx['grand_total']):.2f}"
            ))

    def on_invoice_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        
        row = self.tree.item(selected[0])["values"]
        invoice_id = row[0]
        
        tx_details = self.controller.transaction_model.get_details(invoice_id)
        if tx_details:
            self.detail_tree.delete(*self.detail_tree.get_children())
            self.lbl_details_title.configure(text=f"Itemized Details for Invoice: {invoice_id}")
            
            for item in tx_details["items"]:
                self.detail_tree.insert("", "end", values=(
                    item["item_id"],
                    item["name"],
                    f"₹{float(item['price_at_sale']):.2f}",
                    item["quantity"],
                    f"₹{float(item['subtotal']):.2f}"
                ))
            self.btn_open_pdf.configure(state="normal")

    def open_pdf_receipt(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        row = self.tree.item(selected[0])["values"]
        invoice_id = row[0]
        timestamp_str = row[1]
        
        date_str = timestamp_str[:10]
        time_str = timestamp_str[11:19].replace(":", "-")
        pdf_filename = f"{invoice_id}_{date_str}_{time_str}.pdf"
        sanitized_name = sanitize_filename(pdf_filename)
        pdf_path = os.path.join("bills", sanitized_name)
        
        if os.path.exists(pdf_path):
            try:
                os.startfile(pdf_path)
            except Exception as e:
                Messagebox.show_error(f"Failed to open invoice PDF file: {e}", "File Error")
        else:
            tx_details = self.controller.transaction_model.get_details(invoice_id)
            if not tx_details:
                Messagebox.show_error("Transaction metadata not found.", "Database Error")
                return
                
            regenerate = Messagebox.yesno(
                f"Generated PDF file '{pdf_filename}' not found in the bills folder.\nWould you like to regenerate it now?", 
                "File Missing"
            )
            if regenerate == "Yes":
                cust_phone = tx_details["header"]["customer_phone"]
                cust_profile = self.controller.customer_model.get_by_phone(cust_phone)
                cust_details = {
                    "phone": cust_phone,
                    "name": cust_profile["name"] if cust_profile else "Walk-in Customer",
                    "address": cust_profile["address"] if cust_profile else ""
                }
                
                try:
                    new_path = PDFInvoiceGenerator.generate(
                        tx_details["header"],
                        tx_details["items"],
                        cust_details,
                        pdf_filename
                    )
                    os.startfile(new_path)
                except Exception as e:
                    Messagebox.show_error(f"Failed to regenerate and open PDF invoice: {e}", "Execution Error")


# --- SETTINGS & DIAGNOSTICS LOG VIEWER ---
class SettingsPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Horizontal Split: Left Panel (Analytics Graphs & Theme) and Right Panel (Logs Text Area)
        self.grid_columnconfigure(0, weight=5) # Graphs & Themes
        self.grid_columnconfigure(1, weight=5) # Diagnostic logs
        self.grid_rowconfigure(0, weight=1)
        
        # Left Panel Frame
        left_panel = tb.Frame(self, padding=20)
        left_panel.grid(row=0, column=0, sticky="nsew")
        
        tb.Label(left_panel, text="System Configurations", font=("Helvetica", 16, "bold"), bootstyle="primary").pack(anchor="w", pady=(0, 20))
        
        # Theme section
        theme_frame = tb.Labelframe(left_panel, text="App Theme Configuration", padding=15, bootstyle="primary")
        theme_frame.pack(fill="x", pady=(0, 10))
        
        tb.Label(theme_frame, text="Select Visual Style: ", font=("Helvetica", 11)).pack(anchor="w", pady=(0, 5))
        
        # Restrict themes to exactly cosmo and superhero
        themes = ["cosmo", "superhero"]
        
        current_theme = self.controller.config.get("theme", "cosmo")
        self.theme_combo = tb.Combobox(theme_frame, values=themes, state="readonly")
        self.theme_combo.set(current_theme)
        self.theme_combo.pack(fill="x", pady=5)
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_select)
        
        # Graphs section (Replacing Category Index)
        self.graphs_frame = tb.Labelframe(left_panel, text="Business Analytics & Metrics", padding=10, bootstyle="primary")
        self.graphs_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Configure layout inside graphs_frame
        self.graphs_frame.grid_columnconfigure((0, 1), weight=1)
        self.graphs_frame.grid_rowconfigure((0, 1), weight=1)
        
        # Canvas 1: Revenue / Date (Line Chart)
        self.canvas_rev = tk.Canvas(self.graphs_frame, height=160, highlightthickness=0)
        self.canvas_rev.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Canvas 2: Items Sold / Date (Bar Chart)
        self.canvas_sold = tk.Canvas(self.graphs_frame, height=160, highlightthickness=0)
        self.canvas_sold.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Canvas 3: Category Share (Pie Chart)
        self.canvas_pie = tk.Canvas(self.graphs_frame, height=220, highlightthickness=0)
        self.canvas_pie.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        # Bind resize configuration to redraw graphs dynamically
        self.graphs_frame.bind("<Configure>", lambda event: self.draw_graphs())

        # Right Panel Frame (Log Viewer)
        right_panel = tb.Frame(self, padding=20)
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        log_header = tb.Frame(right_panel)
        log_header.pack(fill="x", pady=(0, 10))
        
        tb.Label(log_header, text="Daily Log Operations Diagnostics", font=("Helvetica", 14, "bold"), bootstyle="primary").pack(side="left")
        tb.Button(log_header, text="Refresh Logs", bootstyle="info-outline", command=self.reload_logs).pack(side="right")
        
        # Read-only text box
        self.text_logs = tk.Text(
            right_panel, 
            bg="#11111b", 
            fg="#a6e3a1", # Console green
            insertbackground="white", 
            font=("Consolas", 10), 
            state="disabled", 
            wrap="word"
        )
        self.text_logs.pack(fill="both", expand=True)

    def on_show(self):
        self.reload_logs()
        self.draw_graphs()

    def on_theme_select(self, event):
        selected_theme = self.theme_combo.get()
        self.controller.change_theme(selected_theme)

    def reload_logs(self):
        self.text_logs.configure(state="normal")
        self.text_logs.delete("1.0", tk.END)
        
        log_file = os.path.join("logs", f"{datetime.now().strftime('%Y-%m-%d')}.log")
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    tail_lines = lines[-100:]
                    self.text_logs.insert(tk.END, "".join(tail_lines))
                    self.text_logs.see(tk.END)
            except Exception as e:
                self.text_logs.insert(tk.END, f"Error reading logs: {e}")
        else:
            self.text_logs.insert(tk.END, "No log entries found for today.")
            
        self.text_logs.configure(state="disabled")

    def draw_graphs(self):
        # Prevent drawing errors during initialization
        w_rev = self.canvas_rev.winfo_width()
        h_rev = self.canvas_rev.winfo_height()
        w_sold = self.canvas_sold.winfo_width()
        h_sold = self.canvas_sold.winfo_height()
        w_pie = self.canvas_pie.winfo_width()
        h_pie = self.canvas_pie.winfo_height()
        
        if w_rev < 10 or h_rev < 10 or w_sold < 10 or h_sold < 10 or w_pie < 10 or h_pie < 10:
            return
            
        # Get theme colors
        style = self.controller.style
        bg_color = style.colors.get("bg") or "#ffffff"
        fg_color = style.colors.get("fg") or "#000000"
        
        is_dark = (self.controller.config.get("theme", "cosmo") == "superhero")
        grid_color = "#343a40" if is_dark else "#e9ecef"
        text_color = fg_color
        line_color = "#37b24d" # Success Green
        bar_color = "#1c7ed6" # Primary Blue
        
        # Clear all canvases
        self.canvas_rev.delete("all")
        self.canvas_sold.delete("all")
        self.canvas_pie.delete("all")
        
        # Set background colors
        self.canvas_rev.configure(bg=bg_color)
        self.canvas_sold.configure(bg=bg_color)
        self.canvas_pie.configure(bg=bg_color)
        
        # Load transaction data
        history = self.controller.transaction_model.get_history()
        tx_items = self.controller.transaction_model.items_db.read_all()
        
        # Map invoice_id -> date
        tx_date_map = {}
        for tx in history:
            date_str = tx["timestamp"][:10]
            tx_date_map[tx["invoice_id"]] = date_str
            
        # Group revenue & quantities by date
        revenue_by_date = {}
        qty_by_date = {}
        
        for tx in history:
            date_str = tx["timestamp"][:10]
            revenue_by_date[date_str] = revenue_by_date.get(date_str, 0.0) + float(tx["grand_total"])
            
        for item in tx_items:
            inv_id = item["invoice_id"]
            date_str = tx_date_map.get(inv_id)
            if date_str:
                qty_by_date[date_str] = qty_by_date.get(date_str, 0) + int(item["quantity"])
                
        # Get last 7 days of sales activity
        all_dates = sorted(list(set(revenue_by_date.keys()) | set(qty_by_date.keys())))
        last_7_dates = all_dates[-7:] if len(all_dates) >= 7 else all_dates
        
        # 1. DRAW REVENUE TREND (LINE CHART)
        pad_left, pad_right, pad_top, pad_bottom = 45, 15, 20, 45
        self.canvas_rev.create_text(w_rev/2, h_rev - 5, text="Daily Revenue Trend", fill=text_color, font=("Helvetica", 10, "bold"), anchor="s")
        
        if not last_7_dates:
            self.canvas_rev.create_text(w_rev/2, h_rev/2, text="No Sales Data Available", fill=text_color, font=("Helvetica", 9, "italic"))
        else:
            max_rev = max(revenue_by_date.get(d, 0.0) for d in last_7_dates)
            if max_rev <= 0.0:
                max_rev = 1.0
            
            # Axes
            self.canvas_rev.create_line(pad_left, h_rev - pad_bottom, w_rev - pad_right, h_rev - pad_bottom, fill=text_color, width=1)
            self.canvas_rev.create_line(pad_left, pad_top, pad_left, h_rev - pad_bottom, fill=text_color, width=1)
            
            # Y ticks & Grid Lines
            for tick in [0.0, max_rev/2.0, max_rev]:
                y_pos = h_rev - pad_bottom - (tick / max_rev) * (h_rev - pad_top - pad_bottom)
                self.canvas_rev.create_line(pad_left, y_pos, w_rev - pad_right, y_pos, fill=grid_color, dash=(2, 2))
                self.canvas_rev.create_text(pad_left - 5, y_pos, text=f"₹{tick:.0f}", fill=text_color, font=("Helvetica", 8), anchor="e")
                
            # Plot Points & Lines
            points = []
            x_step = (w_rev - pad_left - pad_right) / max(1, len(last_7_dates) - 1) if len(last_7_dates) > 1 else (w_rev - pad_left - pad_right)
            
            for i, date_str in enumerate(last_7_dates):
                x = pad_left + i * x_step if len(last_7_dates) > 1 else pad_left + (w_rev - pad_left - pad_right)/2
                val = revenue_by_date.get(date_str, 0.0)
                y = h_rev - pad_bottom - (val / max_rev) * (h_rev - pad_top - pad_bottom)
                points.append((x, y))
                
                # X Labels (MM-DD)
                self.canvas_rev.create_text(x, h_rev - pad_bottom + 12, text=date_str[5:], fill=text_color, font=("Helvetica", 8), anchor="center")
                self.canvas_rev.create_line(x, pad_top, x, h_rev - pad_bottom, fill=grid_color, dash=(2, 2))
                
            # Draw line path
            if len(points) > 1:
                flat_points = [coord for pt in points for coord in pt]
                self.canvas_rev.create_line(flat_points, fill=line_color, width=2)
            for x, y in points:
                self.canvas_rev.create_oval(x-3, y-3, x+3, y+3, fill=line_color, outline=text_color)
                
        # 2. DRAW UNITS SOLD DAILY (BAR CHART)
        pad_left, pad_right, pad_top, pad_bottom = 40, 15, 20, 45
        self.canvas_sold.create_text(w_sold/2, h_sold - 5, text="Units Sold Daily", fill=text_color, font=("Helvetica", 10, "bold"), anchor="s")
        
        if not last_7_dates:
            self.canvas_sold.create_text(w_sold/2, h_sold/2, text="No Sales Data Available", fill=text_color, font=("Helvetica", 9, "italic"))
        else:
            max_qty = max(qty_by_date.get(d, 0) for d in last_7_dates)
            if max_qty <= 0:
                max_qty = 1
                
            # Axes
            self.canvas_sold.create_line(pad_left, h_sold - pad_bottom, w_sold - pad_right, h_sold - pad_bottom, fill=text_color, width=1)
            self.canvas_sold.create_line(pad_left, pad_top, pad_left, h_sold - pad_bottom, fill=text_color, width=1)
            
            # Y ticks & Grid Lines
            for tick in [0, max_qty // 2, max_qty]:
                y_pos = h_sold - pad_bottom - (tick / max_qty) * (h_sold - pad_top - pad_bottom)
                self.canvas_sold.create_line(pad_left, y_pos, w_sold - pad_right, y_pos, fill=grid_color, dash=(2, 2))
                self.canvas_sold.create_text(pad_left - 5, y_pos, text=str(tick), fill=text_color, font=("Helvetica", 8), anchor="e")
                
            # Draw Bars
            plot_w = w_sold - pad_left - pad_right
            n = len(last_7_dates)
            bar_w = plot_w / (n * 1.5)
            gap = plot_w / (n * 3)
            
            for i, date_str in enumerate(last_7_dates):
                x = pad_left + gap + i * (bar_w + gap)
                val = qty_by_date.get(date_str, 0)
                bar_h = (val / max_qty) * (h_sold - pad_top - pad_bottom)
                y = h_sold - pad_bottom - bar_h
                
                self.canvas_sold.create_rectangle(x, y, x + bar_w, h_sold - pad_bottom, fill=bar_color, outline=text_color, width=1)
                if val > 0:
                    self.canvas_sold.create_text(x + bar_w/2, y - 8, text=str(val), fill=text_color, font=("Helvetica", 8))
                    
                # X Label (MM-DD)
                self.canvas_sold.create_text(x + bar_w/2, h_sold - pad_bottom + 12, text=date_str[5:], fill=text_color, font=("Helvetica", 8), anchor="center")
                
        # 3. DRAW CATEGORY SHARE (PIE CHART)
        self.canvas_pie.create_text(w_pie/2, 10, text="Category Share (Stock Distribution)", fill=text_color, font=("Helvetica", 11, "bold"), anchor="n")
        
        active_items = self.controller.inventory_model.get_all()
        cat_counts = {}
        for item in active_items:
            cat = item["category"]
            cat_counts[cat] = cat_counts.get(cat, 0) + int(item["quantity"])
            
        total_items = sum(cat_counts.values())
        
        if total_items <= 0:
            self.canvas_pie.create_text(w_pie/2, h_pie/2, text="No Inventory Items Available", fill=text_color, font=("Helvetica", 10, "italic"))
        else:
            sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
            
            diameter = min(h_pie - 50, w_pie / 2.2)
            cx = diameter / 2 + 30
            cy = h_pie / 2 + 10
            x1, y1 = cx - diameter/2, cy - diameter/2
            x2, y2 = cx + diameter/2, cy + diameter/2
            
            pie_colors = ["#4dabf7", "#37b24d", "#f783ac", "#f59f00", "#748ffc", "#f06595", "#3bc9db", "#ae3ec9"]
            
            start_angle = 0
            lx = diameter + 70
            
            for i, (cat, qty) in enumerate(sorted_cats):
                percentage = (qty / total_items) * 100
                angle = (qty / total_items) * 360
                color = pie_colors[i % len(pie_colors)]
                
                self.canvas_pie.create_arc(x1, y1, x2, y2, start=start_angle, extent=angle, fill=color, outline=text_color)
                start_angle += angle
                
                if i < 7:
                    ly = 35 + i * 22
                    self.canvas_pie.create_rectangle(lx, ly, lx + 12, ly + 12, fill=color, outline=text_color)
                    legend_text = f"{cat}: {qty} units ({percentage:.1f}%)"
                    self.canvas_pie.create_text(lx + 20, ly + 6, text=legend_text, fill=text_color, font=("Helvetica", 9), anchor="w")
                    
            if len(sorted_cats) > 7:
                self.canvas_pie.create_text(lx, 35 + 7 * 22, text="... and more categories", fill=text_color, font=("Helvetica", 8, "italic"), anchor="w")


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
