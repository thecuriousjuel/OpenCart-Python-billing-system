# src/gui/inventory.py
"""
Inventory Management Page for the OpenCart Billing System.

Provides a split-panel interface for adding, updating, and soft-deleting
product catalog entries. Includes category management, real-time search,
category filtering, and ascending/descending column sorting.
"""
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.dialogs import Messagebox
from src.utils import logger

class InventoryPage(tb.Frame):
    """Product catalog management view with CRUD form, category manager, and sortable data grid."""

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
        
        # Category field (Combobox)
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

        # Category Manager section
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
        
        # Search & Sort & Filter Controls
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
        """Refreshes categories and the product table whenever this page is navigated to."""
        self.reload_categories()
        self.clear_form()
        self.reload_tree()

    def toggle_sort_dir(self):
        """Toggles the sort direction between ascending and descending and reloads the table."""
        if self.var_sort_desc.get():
            self.var_sort_desc.set(False)
            self.btn_sort_dir.configure(text="Asc")
        else:
            self.var_sort_desc.set(True)
            self.btn_sort_dir.configure(text="Desc")
        self.reload_tree()

    def reload_categories(self):
        """Refreshes the category combobox values and the category table tree from the database."""
        categories = [r["category_name"] for r in self.controller.category_model.get_all()]
        self.combo_category.configure(values=categories)
        self.combo_filter.configure(values=["All"] + categories)
        
        # Also reload category table
        self.cat_tree.delete(*self.cat_tree.get_children())
        all_categories = self.controller.category_model.get_all()
        for idx, cat in enumerate(all_categories):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.cat_tree.insert("", "end", values=(cat["category_name"], cat["total_items"]), tags=(tag,))
        self.controller.apply_striped_tags(self.cat_tree)

    def reload_tree(self):
        """Reloads the inventory table applying the current search query, category filter, and sort order."""
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
            
        for idx, item in enumerate(items):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                item["item_id"],
                item["name"],
                item["category"],
                f"₹{float(item['price']):.2f}",
                item["quantity"],
                item["mfg_date"],
                item["expiry_date"]
            ), tags=(tag,))
        self.controller.apply_striped_tags(self.tree)

    def on_row_select(self, event):
        """Populates the input form with data from the selected inventory row for editing."""
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
        """Resets all form inputs to empty and restores the Add / Update / Delete button states."""
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
        """Reads form fields and calls the inventory model to add a new product to the catalog."""
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
        """Reads form fields and calls the inventory model to update the selected product record."""
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
        """Shows a confirmation dialog and soft-deletes the selected product to the deleted archive."""
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
        """Opens a modal dialog to add a new category name to the database."""
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
        """Confirms and deletes the selected category if no active products belong to it."""
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
