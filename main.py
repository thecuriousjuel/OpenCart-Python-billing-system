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
from ttkbootstrap.toast import ToastNotification

# Import core modules
from src.database import InventoryModel, CategoryModel, CustomerModel, TransactionModel
from src.utils import logger, PDFInvoiceGenerator, sanitize_filename

class MainApplication(tb.Window):
    """Main window controller managing configurations, layouts, and frame switching."""
    def __init__(self):
        # Load persisted settings
        self.config_file = "data/settings.json"
        self.config = self.load_settings()
        initial_theme = self.config.get("theme", "darkly")
        
        super().__init__(
            title="OpenCart - Python Billing System",
            themename=initial_theme,
            size=(1300, 850),
            position=(50, 50),
            state="zoomed" # Maximize by default
        )
        
        # Instantiate CSV models
        self.inventory_model = InventoryModel()
        self.category_model = CategoryModel()
        self.customer_model = CustomerModel()
        self.transaction_model = TransactionModel()
        
        # Build core layout container
        self.sidebar = tb.Frame(self, bootstyle="dark", width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        self.content_area = tb.Frame(self, bootstyle="secondary")
        self.content_area.pack(side="right", expand=True, fill="both")
        
        # Initialize page dictionaries
        self.pages = {}
        self.current_page = None
        
        # Initialize frames
        for PageClass in (HomePage, InventoryPage, BillingPage, HistoryPage, SettingsPage):
            page_name = PageClass.__name__
            frame = PageClass(parent=self.content_area, controller=self)
            self.pages[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        self.build_sidebar()
        self.show_frame("HomePage")
        logger.info("Main Application layout loaded successfully.")

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read settings: {e}")
        # Default fallback
        default_config = {"theme": "darkly"}
        self.save_settings(default_config)
        return default_config

    def save_settings(self, config):
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def build_sidebar(self):
        # Application Branding
        brand = tb.Label(
            self.sidebar, 
            text="OpenCart Billing", 
            bootstyle="inverse-dark", 
            font=("Helvetica", 16, "bold"), 
            justify="center",
            padding=(0, 25)
        )
        brand.pack(fill="x")
        
        # Divider Line
        div = tb.Separator(self.sidebar, bootstyle="secondary")
        div.pack(fill="x", padx=10, pady=5)
        
        # Navigation Buttons configuration
        nav_items = [
            ("Home Dashboard", "HomePage", "home"),
            ("Inventory Manager", "InventoryPage", "inventory"),
            ("Billing / Cart", "BillingPage", "cart"),
            ("Invoice History", "HistoryPage", "history"),
            ("Settings & Logs", "SettingsPage", "settings")
        ]
        
        self.nav_buttons = {}
        for text, frame_name, key in nav_items:
            btn = tb.Button(
                self.sidebar, 
                text=text, 
                bootstyle="light-outline", 
                command=lambda f=frame_name: self.show_frame(f)
            )
            btn.pack(fill="x", padx=15, pady=8)
            self.nav_buttons[frame_name] = btn
            
    def show_frame(self, page_name):
        frame = self.pages[page_name]
        frame.tkraise()
        self.current_page = page_name
        
        # Visual indication of active nav button
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(bootstyle="light")
            else:
                btn.configure(bootstyle="light-outline")
                
        # Trigger reload hooks if present
        if hasattr(frame, "on_show"):
            frame.on_show()

    def change_theme(self, new_theme):
        self.style.theme_use(new_theme)
        self.config["theme"] = new_theme
        self.save_settings(self.config)
        logger.info(f"Theme successfully updated to {new_theme}")

    def show_toast(self, title, message, level="info"):
        """Displays a non-blocking toast notification at the bottom-right."""
        # Translate level to theme color
        bootstyle = SUCCESS if level == "success" else (DANGER if level == "error" else INFO)
        toast = ToastNotification(
            title=title,
            message=message,
            duration=3000,
            bootstyle=bootstyle,
            position=(950, 750, 'se')
        )
        toast.show_toast()


# --- HOME PAGE VIEW (DASHBOARD) ---
class HomePage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bootstyle="secondary")
        self.controller = controller
        
        # Header banner
        header = tb.Label(
            self, 
            text="Dashboard Overview", 
            font=("Helvetica", 24, "bold"), 
            bootstyle="inverse-secondary",
            padding=(20, 20)
        )
        header.pack(anchor="w")
        
        # Card Grid container
        self.cards_frame = tb.Frame(self, bootstyle="secondary")
        self.cards_frame.pack(fill="x", padx=20, pady=10)
        self.cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Instantiate Dashboard KPI metrics cards
        self.total_items_card = self.create_kpi_card("Total Items in Stock", "0", INFO, 0)
        self.low_stock_card = self.create_kpi_card("Low Stock Warnings", "0", DANGER, 1)
        self.tx_today_card = self.create_kpi_card("Sales Invoices Today", "0", WARNING, 2)
        self.rev_today_card = self.create_kpi_card("Revenue Today", "$0.00", SUCCESS, 3)
        
        # Shortcuts panel
        shortcuts_lbl = tb.Label(
            self, 
            text="Quick Action Panels", 
            font=("Helvetica", 14, "bold"), 
            bootstyle="inverse-secondary",
            padding=(20, 30, 20, 10)
        )
        shortcuts_lbl.pack(anchor="w")
        
        sh_frame = tb.Frame(self, bootstyle="secondary")
        sh_frame.pack(fill="x", padx=20, pady=10)
        
        btn_new_bill = tb.Button(
            sh_frame, 
            text="Launch New Cart Checkout", 
            bootstyle="success", 
            font=("Helvetica", 12, "bold"),
            padding=15, 
            command=lambda: self.controller.show_frame("BillingPage")
        )
        btn_new_bill.pack(side="left", padx=10)
        
        btn_add_item = tb.Button(
            sh_frame, 
            text="Manage Inventory catalog", 
            bootstyle="info", 
            font=("Helvetica", 12, "bold"),
            padding=15, 
            command=lambda: self.controller.show_frame("InventoryPage")
        )
        btn_add_item.pack(side="left", padx=10)
        
        btn_view_logs = tb.Button(
            sh_frame, 
            text="View System Diagnostics", 
            bootstyle="warning", 
            font=("Helvetica", 12, "bold"),
            padding=15, 
            command=lambda: self.controller.show_frame("SettingsPage")
        )
        btn_view_logs.pack(side="left", padx=10)

    def create_kpi_card(self, title, initial_val, style_boot, column):
        card = tb.Frame(self.cards_frame, bootstyle=style_boot, padding=20)
        card.grid(row=0, column=column, padx=10, sticky="nsew")
        
        lbl_title = tb.Label(card, text=title, font=("Helvetica", 11), bootstyle=f"inverse-{style_boot}")
        lbl_title.pack(anchor="w", pady=(0, 5))
        
        lbl_val = tb.Label(card, text=initial_val, font=("Helvetica", 22, "bold"), bootstyle=f"inverse-{style_boot}")
        lbl_val.pack(anchor="w")
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
        self.rev_today_card.configure(text=f"${revenue_today:.2f}")


# --- INVENTORY PAGE VIEW ---
class InventoryPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bootstyle="secondary")
        self.controller = controller
        
        # Layout splits into Form Panel (Left) and Grid Table (Right)
        self.grid_columnconfigure(0, weight=4) # Form
        self.grid_columnconfigure(1, weight=6) # Table
        self.grid_rowconfigure(0, weight=1)
        
        # Left Panel (Inputs)
        left_panel = tb.Frame(self, bootstyle="secondary", padding=20)
        left_panel.grid(row=0, column=0, sticky="nsew")
        
        lbl_title = tb.Label(left_panel, text="Manage Inventory Catalog", font=("Helvetica", 16, "bold"), bootstyle="inverse-secondary")
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
        tb.Label(left_panel, text="Product ID (Auto Generated)", bootstyle="inverse-secondary").pack(anchor="w", pady=(5, 2))
        self.ent_id = tb.Entry(left_panel, textvariable=self.var_id, state="readonly", bootstyle="dark")
        self.ent_id.pack(fill="x", pady=(0, 10))
        
        # Name field
        tb.Label(left_panel, text="Product Name *", bootstyle="inverse-secondary").pack(anchor="w", pady=(5, 2))
        self.ent_name = tb.Entry(left_panel, textvariable=self.var_name, bootstyle="dark")
        self.ent_name.pack(fill="x", pady=(0, 10))
        
        # Category field (Combobox with popup dialog trigger)
        cat_lbl_frame = tb.Frame(left_panel, bootstyle="secondary")
        cat_lbl_frame.pack(fill="x", pady=(5, 2))
        tb.Label(cat_lbl_frame, text="Category Selection *", bootstyle="inverse-secondary").pack(side="left")
        
        tb.Button(
            cat_lbl_frame, 
            text="+ Add New", 
            bootstyle="success-link", 
            padding=0, 
            command=self.open_new_category_dialog
        ).pack(side="right")
        
        self.combo_category = tb.Combobox(left_panel, textvariable=self.var_category, state="readonly", bootstyle="dark")
        self.combo_category.pack(fill="x", pady=(0, 10))
        
        # Price and Quantity Row
        pq_frame = tb.Frame(left_panel, bootstyle="secondary")
        pq_frame.pack(fill="x", pady=(0, 10))
        pq_frame.grid_columnconfigure((0, 1), weight=1)
        
        p_frame = tb.Frame(pq_frame, bootstyle="secondary")
        p_frame.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        tb.Label(p_frame, text="Unit Price ($) *", bootstyle="inverse-secondary").pack(anchor="w", pady=(0, 2))
        tb.Entry(p_frame, textvariable=self.var_price, bootstyle="dark").pack(fill="x")
        
        q_frame = tb.Frame(pq_frame, bootstyle="secondary")
        q_frame.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        tb.Label(q_frame, text="Stock Quantity *", bootstyle="inverse-secondary").pack(anchor="w", pady=(0, 2))
        tb.Entry(q_frame, textvariable=self.var_qty, bootstyle="dark").pack(fill="x")
        
        # Manufacture and Expiry Dates Row
        dates_frame = tb.Frame(left_panel, bootstyle="secondary")
        dates_frame.pack(fill="x", pady=(0, 10))
        dates_frame.grid_columnconfigure((0, 1), weight=1)
        
        m_frame = tb.Frame(dates_frame, bootstyle="secondary")
        m_frame.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        tb.Label(m_frame, text="Mfg Date (YYYY-MM-DD) *", bootstyle="inverse-secondary").pack(anchor="w", pady=(0, 2))
        tb.Entry(m_frame, textvariable=self.var_mfg, bootstyle="dark").pack(fill="x")
        
        e_frame = tb.Frame(dates_frame, bootstyle="secondary")
        e_frame.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        tb.Label(e_frame, text="Expiry Date (YYYY-MM-DD) *", bootstyle="inverse-secondary").pack(anchor="w", pady=(0, 2))
        tb.Entry(e_frame, textvariable=self.var_exp, bootstyle="dark").pack(fill="x")
        
        # Action Buttons Form
        actions_frame = tb.Frame(left_panel, bootstyle="secondary")
        actions_frame.pack(fill="x", pady=(15, 0))
        
        self.btn_save = tb.Button(actions_frame, text="Add Product", bootstyle="success", command=self.save_item)
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_update = tb.Button(actions_frame, text="Update", bootstyle="warning", state="disabled", command=self.update_item)
        self.btn_update.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_delete = tb.Button(actions_frame, text="Delete", bootstyle="danger", state="disabled", command=self.delete_item)
        self.btn_delete.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        tb.Button(left_panel, text="Clear Form", bootstyle="secondary-outline", command=self.clear_form).pack(fill="x", pady=10)

        # Right Panel (List Grid View)
        right_panel = tb.Frame(self, bootstyle="secondary", padding=20)
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Search & Sort Controls
        search_frame = tb.Frame(right_panel, bootstyle="secondary")
        search_frame.pack(fill="x", pady=(0, 15))
        
        tb.Label(search_frame, text="Search Catalog: ", bootstyle="inverse-secondary").pack(side="left", padx=(0, 5))
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", lambda *args: self.reload_tree())
        self.ent_search = tb.Entry(search_frame, textvariable=self.var_search, width=25, bootstyle="dark")
        self.ent_search.pack(side="left", padx=5)
        
        tb.Label(search_frame, text="Sort By: ", bootstyle="inverse-secondary").pack(side="left", padx=(15, 5))
        self.var_sort = tk.StringVar(value="name")
        self.combo_sort = tb.Combobox(search_frame, textvariable=self.var_sort, values=["name", "price", "quantity", "expiry_date", "mfg_date"], state="readonly", width=12, bootstyle="dark")
        self.combo_sort.pack(side="left", padx=5)
        self.combo_sort.bind("<<ComboboxSelected>>", lambda e: self.reload_tree())
        
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

    def reload_categories(self):
        categories = [r["category_name"] for r in self.controller.category_model.get_all()]
        self.combo_category.configure(values=categories)

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
            
        # Apply Sorting
        sort_key = self.var_sort.get()
        if sort_key in ("price", "quantity"):
            items.sort(key=lambda x: float(x[sort_key]) if sort_key == "price" else int(x[sort_key]))
        else:
            items.sort(key=lambda x: x[sort_key].lower())
            
        for item in items:
            self.tree.insert("", "end", values=(
                item["item_id"],
                item["name"],
                item["category"],
                f"${float(item['price']):.2f}",
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

    def open_new_category_dialog(self):
        # Mini modal Toplevel popup window for adding categories
        dialog = tb.Toplevel(self, title="Add New Category")
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


# --- BILLING & MULTI-CART terminal VIEW ---
class BillingPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bootstyle="secondary")
        self.controller = controller
        
        # Cart structure: Up to 5 carts concurrent support
        # self.carts: dict representing each cart database.
        # Key: int (1 to 5), Val: dict containing {invoice_id, customer: {phone, name, address}, items: list, discount: float}
        self.active_cart_index = 1
        self.carts = {}
        for idx in range(1, 6):
            self.carts[idx] = self.get_empty_cart_structure()
            
        # Top Panel: Cart tabs and Invoice ID display
        top_frame = tb.Frame(self, bootstyle="secondary", padding=15)
        top_frame.pack(fill="x")
        
        tb.Label(top_frame, text="Active Billing Terminals: ", font=("Helvetica", 12, "bold"), bootstyle="inverse-secondary").pack(side="left")
        
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
        main_billing_split = tb.Frame(self, bootstyle="secondary")
        main_billing_split.pack(fill="both", expand=True, padx=15, pady=5)
        
        main_billing_split.grid_columnconfigure(0, weight=7) # Left Panel
        main_billing_split.grid_columnconfigure(1, weight=3) # Right Panel
        main_billing_split.grid_rowconfigure(0, weight=1)
        
        left_layout = tb.Frame(main_billing_split, bootstyle="secondary")
        left_layout.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Section A: Customer Details
        cust_frame = tb.Labelframe(left_layout, text="Buyer Information Details", padding=10, bootstyle="primary")
        cust_frame.pack(fill="x", pady=(0, 10))
        cust_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.var_c_phone = tk.StringVar()
        self.var_c_name = tk.StringVar()
        self.var_c_address = tk.StringVar()
        
        # Handle Phone Autocomplete trigger
        self.var_c_phone.trace_add("write", lambda *args: self.handle_customer_autocomplete())
        
        # Phone
        p_frame = tb.Frame(cust_frame)
        p_frame.grid(row=0, column=0, padx=5, sticky="nsew")
        tb.Label(p_frame, text="Phone Number * (Type to query)", font=("Helvetica", 9)).pack(anchor="w")
        tb.Entry(p_frame, textvariable=self.var_c_phone, bootstyle="dark").pack(fill="x")
        
        # Name
        n_frame = tb.Frame(cust_frame)
        n_frame.grid(row=0, column=1, padx=5, sticky="nsew")
        tb.Label(n_frame, text="Customer Name *", font=("Helvetica", 9)).pack(anchor="w")
        tb.Entry(n_frame, textvariable=self.var_c_name, bootstyle="dark").pack(fill="x")
        
        # Address
        a_frame = tb.Frame(cust_frame)
        a_frame.grid(row=0, column=2, padx=5, sticky="nsew")
        tb.Label(a_frame, text="Address (Optional)", font=("Helvetica", 9)).pack(anchor="w")
        tb.Entry(a_frame, textvariable=self.var_c_address, bootstyle="dark").pack(fill="x")

        # Section B: Item Search & Selection Bar
        item_picker_frame = tb.Labelframe(left_layout, text="Search & Insert Product to Cart", padding=10, bootstyle="primary")
        item_picker_frame.pack(fill="x", pady=10)
        
        tb.Label(item_picker_frame, text="Type Item Name or ID:", font=("Helvetica", 10)).pack(anchor="w", pady=(0, 2))
        
        self.var_item_search = tk.StringVar()
        self.var_item_search.trace_add("write", lambda *args: self.handle_item_suggestion())
        self.ent_item_search = tb.Entry(item_picker_frame, textvariable=self.var_item_search, bootstyle="dark")
        self.ent_item_search.pack(fill="x")
        
        # Dynamic Suggestion Listbox (packed below input when searching)
        self.suggestion_container = tb.Frame(item_picker_frame, bootstyle="dark")
        self.list_suggestions = tk.Listbox(
            self.suggestion_container, 
            height=4, 
            bg="#313244", 
            fg="#cdd6f4", 
            selectbackground="#89b4fa",
            selectforeground="#11111b",
            font=("Segoe UI", 10)
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
        tb.Label(row_actions, text="* Double-click a row to update quantity", font=("Helvetica", 9, "italic"), bootstyle="inverse-secondary").pack(side="right")

        # Right Panel (Receipt Totals Drawer)
        right_panel = tb.Frame(main_billing_split, bootstyle="dark", padding=20)
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        tb.Label(right_panel, text="Receipt Summary", font=("Helvetica", 14, "bold"), bootstyle="inverse-dark").pack(anchor="w", pady=(0, 20))
        
        # Summary totals labels
        self.lbl_subtotal = tb.Label(right_panel, text="Subtotal: $0.00", font=("Helvetica", 12), bootstyle="inverse-dark")
        self.lbl_subtotal.pack(anchor="w", pady=10)
        
        # Discount field
        disc_frame = tb.Frame(right_panel, bootstyle="dark")
        disc_frame.pack(fill="x", pady=10)
        tb.Label(disc_frame, text="Discount (%): ", font=("Helvetica", 11), bootstyle="inverse-dark").pack(side="left")
        
        self.var_discount = tk.StringVar(value="0")
        self.var_discount.trace_add("write", lambda *args: self.recalculate_totals())
        self.ent_discount = tb.Entry(disc_frame, textvariable=self.var_discount, width=8, bootstyle="secondary")
        self.ent_discount.pack(side="right")
        
        # Grand total
        self.lbl_grand = tb.Label(right_panel, text="Grand Total: $0.00", font=("Helvetica", 16, "bold"), bootstyle="inverse-dark")
        self.lbl_grand.pack(anchor="w", pady=(30, 20))
        
        # Checkout buttons
        tb.Button(
            right_panel, 
            text="Confirm checkout & Print PDF", 
            bootstyle="success", 
            font=("Helvetica", 12, "bold"), 
            padding=12,
            command=self.process_checkout
        ).pack(fill="x", pady=10)
        
        tb.Button(
            right_panel, 
            text="Cancel Checkout Order", 
            bootstyle="danger-outline", 
            command=self.reset_active_cart
        ).pack(fill="x")

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

    def on_show(self):
        # Sync view and inputs with current active cart state
        self.switch_cart(self.active_cart_index)
        self.suggestion_container.pack_forget()

    def switch_cart(self, index):
        # Save variables of the previous cart to dictionary before switching
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
        self.var_c_phone.set("")
        self.var_c_name.set(cart["customer"]["name"])
        self.var_c_address.set(cart["customer"]["address"])
        self.var_c_phone.set(cart["customer"]["phone"])
        
        self.var_discount.set(str(int(cart["discount"]) if cart["discount"].is_integer() else cart["discount"]))
        self.var_item_search.set("")
        self.suggestion_container.pack_forget()
        
        self.reload_cart_table()

    def reload_cart_table(self):
        self.cart_tree.delete(*self.cart_tree.get_children())
        cart = self.carts[self.active_cart_index]
        for item in cart["items"]:
            sub = round(int(item["quantity"]) * float(item["price"]), 2)
            self.cart_tree.insert("", "end", values=(
                item["item_id"],
                item["name"],
                f"${float(item['price']):.2f}",
                item["quantity"],
                f"${sub:.2f}"
            ))
        self.recalculate_totals()

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
        
        self.lbl_subtotal.configure(text=f"Subtotal: ${subtotal:.2f}")
        self.lbl_grand.configure(text=f"Grand Total: ${grand:.2f}")

    def handle_customer_autocomplete(self):
        phone = self.var_c_phone.get().strip()
        # Trigger query check when exactly 10 digits are inputted
        digits_only = "".join(filter(str.isdigit, phone))
        if len(digits_only) == 10:
            cust = self.controller.customer_model.get_by_phone(digits_only)
            if cust:
                self.var_c_name.set(cust["name"])
                self.var_c_address.set(cust["address"])
                self.controller.show_toast("Buyer Found", f"Autocompleted details for customer: {cust['name']}", "info")

    def handle_item_suggestion(self):
        q = self.var_item_search.get().strip().lower()
        if not q:
            self.suggestion_container.pack_forget()
            return
            
        # Search inventory
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
            # Check inventory limit
            avail_stock = int(item["quantity"])
            if avail_stock <= 0:
                Messagebox.show_warning(f"Item '{item['name']}' is out of stock.", "Stock Warning")
                return
                
            cart = self.carts[self.active_cart_index]
            
            # Check if item already exists in cart
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
        
        # Re-fetch inventory stock limit
        item_info = self.controller.inventory_model.get_by_id(item_id)
        if not item_info:
            return
        max_stock = int(item_info["quantity"])
        
        # Modal Dialog popup for quantity
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
        
        # Validations
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
            
        # Get and validate discount percent bounds
        try:
            discount_percent = float(self.var_discount.get())
            if not (0 <= discount_percent <= 100):
                Messagebox.show_error("Discount percentage must be between 0 and 100.", "Validation Error")
                return
        except ValueError:
            Messagebox.show_error("Discount percentage must be a numeric value.", "Validation Error")
            return
            
        # Check stock quantities and execute transaction database writes
        success, res = self.controller.transaction_model.checkout(
            digits_phone,
            cart["items"],
            discount_percent
        )
        
        if success:
            invoice_data = res # returned header details
            invoice_id = invoice_data["invoice_id"]
            
            # Save customer profile to CSV database
            self.controller.customer_model.add_or_update(digits_phone, name, address)
            
            # Map item names for PDF generation
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
            
            # Ask user if they wish to open the PDF immediately
            open_pdf = Messagebox.yesno(f"Checkout successful!\nInvoice ID: {invoice_id}\n\nWould you like to open the generated PDF receipt?", "Open Receipt")
            if open_pdf == "Yes":
                try:
                    os.startfile(pdf_path)
                except Exception as e:
                    logger.error(f"Failed to open generated PDF file: {e}")
                    Messagebox.show_error(f"Failed to open PDF file: {e}", "File Error")
        else:
            Messagebox.show_error(res, "Checkout Transaction Failed")


# --- TRANSACTION HISTORY VIEW ---
class HistoryPage(tb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bootstyle="secondary")
        self.controller = controller
        
        # Horizontal Split: Top (Search Panel & Header Table) and Bottom (Selected Invoice Detail)
        self.grid_rowconfigure(0, weight=6) # History list
        self.grid_rowconfigure(1, weight=4) # Details box
        self.grid_columnconfigure(0, weight=1)
        
        # Top Frame
        top_frame = tb.Frame(self, bootstyle="secondary", padding=20)
        top_frame.grid(row=0, column=0, sticky="nsew")
        
        lbl_title = tb.Label(top_frame, text="Transaction & Invoice History", font=("Helvetica", 16, "bold"), bootstyle="inverse-secondary")
        lbl_title.pack(anchor="w", pady=(0, 15))
        
        # Filter controls
        filter_frame = tb.Frame(top_frame, bootstyle="secondary")
        filter_frame.pack(fill="x", pady=(0, 10))
        
        tb.Label(filter_frame, text="Search Phone or Invoice ID: ", bootstyle="inverse-secondary").pack(side="left")
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", lambda *args: self.reload_history_table())
        tb.Entry(filter_frame, textvariable=self.var_search, width=30, bootstyle="dark").pack(side="left", padx=5)
        
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
        bottom_frame = tb.Frame(self, bootstyle="dark", padding=20)
        bottom_frame.grid(row=1, column=0, sticky="nsew")
        
        # Bottom Title & actions row
        det_title_row = tb.Frame(bottom_frame, bootstyle="dark")
        det_title_row.pack(fill="x", pady=(0, 10))
        
        self.lbl_details_title = tb.Label(det_title_row, text="Invoice Itemized Details", font=("Helvetica", 12, "bold"), bootstyle="inverse-dark")
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

    def reload_history_table(self):
        self.tree.delete(*self.tree.get_children())
        history = self.controller.transaction_model.get_history()
        
        q = self.var_search.get().strip().lower()
        if q:
            history = [
                tx for tx in history 
                if q in tx["invoice_id"].lower() or q in tx["customer_phone"].lower()
            ]
            
        for tx in history:
            self.tree.insert("", "end", values=(
                tx["invoice_id"],
                tx["timestamp"],
                tx["customer_phone"],
                f"${float(tx['subtotal']):.2f}",
                f"{float(tx['discount_percent'])}%",
                f"${float(tx['grand_total']):.2f}"
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
                    f"${float(item['price_at_sale']):.2f}",
                    item["quantity"],
                    f"${float(item['subtotal']):.2f}"
                ))
            self.btn_open_pdf.configure(state="normal")

    def open_pdf_receipt(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        row = self.tree.item(selected[0])["values"]
        invoice_id = row[0]
        timestamp_str = row[1] # YYYY-MM-DD HH:MM:SS
        
        # Re-derive filename
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
            # PDF file missing. Offer to regenerate on the fly
            tx_details = self.controller.transaction_model.get_details(invoice_id)
            if not tx_details:
                Messagebox.show_error("Transaction metadata not found.", "Database Error")
                return
                
            regenerate = Messagebox.yesno(
                f"Generated PDF file '{pdf_filename}' not found in the bills folder.\nWould you like to regenerate it now?", 
                "File Missing"
            )
            if regenerate == "Yes":
                # Find customer name
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
        super().__init__(parent, bootstyle="secondary")
        self.controller = controller
        
        # Horizontal Split: Left Panel (Categories Table + Theme) and Right Panel (Logs Text Area)
        self.grid_columnconfigure(0, weight=5) # Categories & Themes
        self.grid_columnconfigure(1, weight=5) # Diagnostic logs
        self.grid_rowconfigure(0, weight=1)
        
        # Left Panel Frame
        left_panel = tb.Frame(self, bootstyle="secondary", padding=20)
        left_panel.grid(row=0, column=0, sticky="nsew")
        
        tb.Label(left_panel, text="System Configurations", font=("Helvetica", 16, "bold"), bootstyle="inverse-secondary").pack(anchor="w", pady=(0, 20))
        
        # Theme section
        theme_frame = tb.Labelframe(left_panel, text="App Theme Configuration", padding=15, bootstyle="primary")
        theme_frame.pack(fill="x", pady=(0, 20))
        
        tb.Label(theme_frame, text="Select Visual Style: ", font=("Helvetica", 11)).pack(anchor="w", pady=(0, 5))
        
        themes = [
            "cosmo", "flatly", "journal", "litera", "lumen", "minty", 
            "pulse", "sandstone", "united", "yeti", "simplex", "morph",
            "solar", "cyborg", "darkly", "superhero", "vapor", "charcoal"
        ]
        
        current_theme = self.controller.config.get("theme", "darkly")
        self.theme_combo = tb.Combobox(theme_frame, values=themes, state="readonly", bootstyle="dark")
        self.theme_combo.set(current_theme)
        self.theme_combo.pack(fill="x", pady=5)
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_select)
        
        # Category Management section
        cat_frame = tb.Labelframe(left_panel, text="Inventory Category Index", padding=15, bootstyle="primary")
        cat_frame.pack(fill="both", expand=True)
        
        # Category Table
        self.cat_tree = tb.Treeview(cat_frame, columns=("name", "count"), show="headings", bootstyle="primary", height=8)
        self.cat_tree.pack(fill="both", expand=True, pady=(0, 10))
        
        self.cat_tree.heading("name", text="Category Name")
        self.cat_tree.heading("count", text="Active Products Count")
        self.cat_tree.column("name", width=180, anchor="w")
        self.cat_tree.column("count", width=100, anchor="center")
        
        # Actions row
        cat_actions = tb.Frame(cat_frame)
        cat_actions.pack(fill="x")
        
        tb.Button(cat_actions, text="Add Category", bootstyle="success", command=self.add_category).pack(side="left", padx=5)
        tb.Button(cat_actions, text="Delete Selected", bootstyle="danger-outline", command=self.delete_category).pack(side="left", padx=5)

        # Right Panel Frame (Log Viewer)
        right_panel = tb.Frame(self, bootstyle="dark", padding=20)
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        log_header = tb.Frame(right_panel, bootstyle="dark")
        log_header.pack(fill="x", pady=(0, 10))
        
        tb.Label(log_header, text="Daily Log Operations Diagnostics", font=("Helvetica", 14, "bold"), bootstyle="inverse-dark").pack(side="left")
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
        self.reload_categories()
        self.reload_logs()

    def on_theme_select(self, event):
        selected_theme = self.theme_combo.get()
        self.controller.change_theme(selected_theme)
        self.controller.show_toast("Theme Changed", f"Successfully loaded '{selected_theme}' theme.", "success")

    def reload_categories(self):
        self.cat_tree.delete(*self.cat_tree.get_children())
        categories = self.controller.category_model.get_all()
        for cat in categories:
            self.cat_tree.insert("", "end", values=(cat["category_name"], cat["total_items"]))

    def add_category(self):
        dialog = tb.Toplevel(self, title="Add Category")
        dialog.geometry("380x160")
        dialog.resizable(False, False)
        dialog.grab_set()
        
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

    def reload_logs(self):
        self.text_logs.configure(state="normal")
        self.text_logs.delete("1.0", tk.END)
        
        log_file = os.path.join("logs", f"{datetime.now().strftime('%Y-%m-%d')}.log")
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # Show last 100 lines
                    tail_lines = lines[-100:]
                    self.text_logs.insert(tk.END, "".join(tail_lines))
                    self.text_logs.see(tk.END) # Auto scroll to bottom
            except Exception as e:
                self.text_logs.insert(tk.END, f"Error reading logs: {e}")
        else:
            self.text_logs.insert(tk.END, "No log entries found for today.")
            
        self.text_logs.configure(state="disabled")


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
