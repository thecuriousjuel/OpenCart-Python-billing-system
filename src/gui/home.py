# src/gui/home.py
"""
Dashboard Home Page for the OpenCart Billing System.

Displays real-time KPI summary cards (total items, low stock warnings,
daily sales count, and daily revenue) along with quick-action buttons
to navigate to the billing terminal or inventory manager.
"""
import tkinter as tk
import ttkbootstrap as tb
from datetime import datetime

class HomePage(tb.Frame):
    """Dashboard overview page displaying live business KPI metrics and navigation shortcuts."""

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
            command=lambda: self.controller.show_logs_dialog()
        )
        btn_view_logs.pack(side="left", padx=10)

    def create_kpi_card(self, title, initial_val, column):
        """Creates a labelled KPI card widget in the cards grid at the specified column index."""
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
