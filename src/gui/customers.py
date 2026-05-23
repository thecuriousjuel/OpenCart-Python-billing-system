# src/gui/customers.py
"""
Customer Directory Page for the OpenCart Billing System.

Displays all registered customer profiles in a searchable, sortable table.
Shows loyalty purchase counts and total spending per customer, computed
live from the transaction history records.
"""
import tkinter as tk
import ttkbootstrap as tb

class CustomersPage(tb.Frame):
    """Customer directory view showing registered profiles with loyalty stats and sorting."""

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
        
        # Table / Treeview
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
        """Reloads the customer table when navigating to this page."""
        self.reload_table()
        
    def toggle_sort_dir(self):
        """Toggles the sort direction between ascending and descending and refreshes the table."""
        if self.var_sort_desc.get():
            self.var_sort_desc.set(False)
            self.btn_sort_dir.configure(text="Asc")
        else:
            self.var_sort_desc.set(True)
            self.btn_sort_dir.configure(text="Desc")
        self.reload_table()
        
    def reload_table(self):
        """Reloads the customer list from database, applying the current search query and sort order."""
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
            
        for idx, c in enumerate(customers_data):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(
                c["phone"],
                c["name"],
                c["address"],
                str(c["purchases"]),
                f"₹{c['spent']:.2f}"
            ), tags=(tag,))
        self.controller.apply_striped_tags(self.tree)
